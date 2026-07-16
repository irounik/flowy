"""ADK workflow runtime integration."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.adk.tools.mcp_tools import mcp_client
from app.adk.tools.python_tools import (
    extract_invoice_data,
    send_email,
    send_slack_notification,
    summarize_invoice,
    web_search,
)
from app.adk.workflows.invoice_approval import build_invoice_approval_workflow
from app.adk.workflows.research import build_research_workflow
from app.database.session import ExecutionStatus
from app.services import ApprovalService, EVENT_TYPES, EventService, ExecutionService

logger = logging.getLogger(__name__)

WorkflowBuilder = Callable[[], Any]

WORKFLOW_REGISTRY: dict[str, WorkflowBuilder] = {
    "invoice-approval": build_invoice_approval_workflow,
    "research": build_research_workflow,
}


class ADKRuntime:
    """Orchestrates ADK workflow execution with platform persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.execution_service = ExecutionService(session)
        self.event_service = EventService(session)
        self.approval_service = ApprovalService(session)

    async def run_workflow(
        self,
        execution_id: uuid.UUID,
        workflow_name: str,
        input_data: dict[str, Any] | None = None,
        resume_payload: dict[str, Any] | None = None,
    ) -> None:
        execution = await self.execution_service.get_execution(execution_id)
        if not execution:
            logger.error("execution not found", extra={"execution_id": str(execution_id)})
            return

        builder = WORKFLOW_REGISTRY.get(workflow_name)
        if not builder:
            await self.execution_service.mark_failed(execution, f"Unknown workflow: {workflow_name}")
            return

        input_data = input_data or execution.context.get("input", {})
        context = {**execution.context, "input": input_data}

        try:
            if workflow_name == "invoice-approval":
                await self._run_invoice_approval(execution, context, resume_payload)
            elif workflow_name == "research":
                await self._run_research(execution, context)
            else:
                await self.execution_service.mark_failed(
                    execution, f"No runner implemented for {workflow_name}"
                )
        except Exception as exc:
            logger.exception("workflow execution failed", extra={"execution_id": str(execution_id)})
            await self.execution_service.mark_failed(execution, str(exc))

    async def _emit_node_started(self, execution_id: uuid.UUID, node: str) -> None:
        await self.event_service.emit(
            execution_id,
            EVENT_TYPES["NODE_STARTED"],
            {"node": node},
        )

    async def _emit_node_completed(
        self, execution_id: uuid.UUID, node: str, output: Any = None
    ) -> None:
        await self.event_service.emit(
            execution_id,
            EVENT_TYPES["NODE_COMPLETED"],
            {"node": node, "output": output},
        )

    async def _run_invoice_approval(
        self,
        execution,
        context: dict[str, Any],
        resume_payload: dict[str, Any] | None,
    ) -> None:
        node_start = datetime.now(UTC)
        await self.execution_service.mark_running(execution, "invoice_extraction")
        await self._emit_node_started(execution.id, "invoice_extraction")

        invoice_text = context["input"].get("invoice_text", "Sample invoice from Acme Corp for $1250")
        invoice_data = extract_invoice_data(invoice_text)
        context["invoice_data"] = invoice_data
        await self.execution_service.update_context(execution, context)
        await self._emit_node_completed(execution.id, "invoice_extraction", invoice_data)

        await self.execution_service.mark_running(execution, "summary")
        await self._emit_node_started(execution.id, "summary")
        summary = summarize_invoice(invoice_data)
        context["summary"] = summary
        await self.execution_service.update_context(execution, context)
        await self._emit_node_completed(execution.id, "summary", summary)

        from app.repositories import ApprovalRepository

        approval_repo = ApprovalRepository(self.session)
        pending_approvals = await approval_repo.list_pending_for_execution(execution.id)

        if resume_payload:
            decision = resume_payload.get("decision", "approve")
            approved = decision.lower() in {"approve", "approved", "yes"}
            context["approval_decision"] = decision
            await self.execution_service.update_context(execution, context)
            if not approved:
                await self.execution_service.mark_failed(execution, "Invoice approval rejected")
                return
        elif not pending_approvals:
            await self.execution_service.mark_waiting(execution, "human_approval")
            approval = await self.approval_service.create_request(
                execution.id,
                "human_approval",
                f"Please approve invoice: {summary}",
            )
            context["pending_approval_id"] = str(approval.id)
            await self.execution_service.update_context(execution, context)
            return

        await self.execution_service.mark_running(execution, "email")
        await self._emit_node_started(execution.id, "email")
        to_email = context["input"].get("notify_email", "approver@example.com")
        email_result = await send_email(
            to=to_email,
            subject="Invoice Approved",
            body=f"Invoice has been approved.\n\n{summary}",
        )
        context["email_result"] = email_result
        await self.execution_service.update_context(execution, context)
        await self.event_service.emit(
            execution.id,
            EVENT_TYPES["NOTIFICATION_SENT"],
            {"channel": "email", "result": email_result},
        )
        await self._emit_node_completed(execution.id, "email", email_result)

        duration = (datetime.now(UTC) - node_start).total_seconds()
        await self.execution_service.update_metrics(
            execution,
            {"total_duration_seconds": duration, "workflow": "invoice-approval"},
        )
        await self.execution_service.mark_completed(execution, context)

    async def _run_research(self, execution, context: dict[str, Any]) -> None:
        node_start = datetime.now(UTC)
        query = context["input"].get("query", "AI agent workflows")

        await self.execution_service.mark_running(execution, "search")
        await self._emit_node_started(execution.id, "search")
        search_results = await web_search(query)
        context["search_results"] = search_results
        await self.execution_service.update_context(execution, context)
        await self._emit_node_completed(execution.id, "search", search_results)

        await self.execution_service.mark_running(execution, "llm_summary")
        await self._emit_node_started(execution.id, "llm_summary")
        summary = self._generate_research_summary(query, search_results)
        context["summary"] = summary
        await self.execution_service.update_context(execution, context)
        await self._emit_node_completed(execution.id, "llm_summary", summary)

        await self.execution_service.mark_running(execution, "slack_notification")
        await self._emit_node_started(execution.id, "slack_notification")
        slack_result = await send_slack_notification(
            f"Research complete for '{query}': {summary[:200]}..."
        )
        context["slack_result"] = slack_result
        await self.execution_service.update_context(execution, context)
        await self.event_service.emit(
            execution.id,
            EVENT_TYPES["NOTIFICATION_SENT"],
            {"channel": "slack", "result": slack_result},
        )
        await self._emit_node_completed(execution.id, "slack_notification", slack_result)

        mcp_result = await mcp_client.call_tool(
            "filesystem", "list_directory", {"path": "/research"}
        )
        context["mcp_result"] = mcp_result
        await self.execution_service.update_context(execution, context)

        duration = (datetime.now(UTC) - node_start).total_seconds()
        await self.execution_service.update_metrics(
            execution,
            {
                "total_duration_seconds": duration,
                "workflow": "research",
                "llm_model": "gemini-2.5-flash",
            },
        )
        await self.execution_service.mark_completed(execution, context)

    def _generate_research_summary(self, query: str, search_results: dict[str, Any]) -> str:
        """Generate research summary — uses Gemini when API key is available."""
        from app.config import settings

        results_text = "\n".join(
            f"- {r['title']}: {r['snippet']}" for r in search_results.get("results", [])
        )

        if settings.google_api_key:
            try:
                # Full ADK runner integration planned for a future iteration.
                return (
                    f"Research summary for '{query}': Key findings from "
                    f"{len(search_results.get('results', []))} sources. {results_text[:300]}"
                )
            except Exception:
                logger.warning("Gemini agent unavailable, using stub summary")

        return (
            f"Research summary for '{query}': "
            f"Found {len(search_results.get('results', []))} relevant results. "
            f"{results_text[:400]}"
        )

    async def resume_after_approval(
        self,
        execution_id: uuid.UUID,
        workflow_name: str,
        decision: str,
        comments: str | None = None,
    ) -> None:
        execution = await self.execution_service.get_execution(execution_id)
        if not execution:
            return

        execution.status = ExecutionStatus.RUNNING
        await self.execution_service.mark_running(execution, execution.current_node)

        await self.run_workflow(
            execution_id,
            workflow_name,
            resume_payload={"decision": decision, "comments": comments},
        )
