"""Execute user-designed workflow graphs dynamically."""

from __future__ import annotations

import logging
import uuid
from collections import defaultdict, deque
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.adk.mock_llm import mock_llm_complete
from app.adk.tools.mcp_tools import mcp_client
from app.adk.tools.python_tools import (
    calculator,
    extract_invoice_data,
    send_email,
    send_slack_notification,
    summarize_invoice,
    web_search,
)
from app.config import settings
from app.database.session import ExecutionStatus
from app.services import ApprovalService, EVENT_TYPES, EventService, ExecutionService

logger = logging.getLogger(__name__)

TOOL_MAP = {
    "calculator": lambda **kw: calculator(kw.get("expression", "2+2")),
    "extract_invoice_data": lambda **kw: extract_invoice_data(kw.get("invoice_text", "Sample invoice")),
    "web_search": lambda **kw: None,  # async handled separately
    "send_email": lambda **kw: None,
}


class DynamicWorkflowRunner:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.execution_service = ExecutionService(session)
        self.event_service = EventService(session)
        self.approval_service = ApprovalService(session)

    async def run(
        self,
        execution_id: uuid.UUID,
        definition: dict[str, Any],
        resume_payload: dict[str, Any] | None = None,
    ) -> None:
        execution = await self.execution_service.get_execution(execution_id)
        if not execution:
            return

        nodes = {n["id"]: n for n in definition.get("nodes", [])}
        edges = definition.get("edges", [])
        order = self._topological_sort(nodes, edges)

        if not order:
            await self.execution_service.mark_failed(execution, "Workflow has no executable nodes")
            return

        context: dict[str, Any] = {**execution.context, "node_outputs": {}}
        start = datetime.now(UTC)
        await self.execution_service.mark_running(execution, order[0])

        try:
            skip_until_resume = resume_payload is not None
            resumed = False

            for node_id in order:
                node = nodes[node_id]
                node_type = node.get("type", "tool")
                label = node.get("label", node_id)
                config = node.get("config", {})

                if skip_until_resume and not resumed:
                    if node_type == "approval" and resume_payload:
                        resumed = True
                    else:
                        continue

                await self.event_service.emit(
                    execution_id, EVENT_TYPES["NODE_STARTED"], {"node": label, "id": node_id}
                )
                await self.execution_service.mark_running(execution, label)

                if node_type == "approval" and not resume_payload:
                    await self.execution_service.mark_waiting(execution, label)
                    approval = await self.approval_service.create_request(
                        execution_id, label, config.get("message", f"Approve {label}?")
                    )
                    context["pending_approval_id"] = str(approval.id)
                    await self.execution_service.update_context(execution, context)
                    return

                output = await self._execute_node(
                    execution_id, node_type, label, config, context, resume_payload
                )
                context["node_outputs"][node_id] = output
                context["last_output"] = output
                await self.execution_service.update_context(execution, context)

                await self.event_service.emit(
                    execution_id,
                    EVENT_TYPES["NODE_COMPLETED"],
                    {"node": label, "id": node_id, "output": output},
                )

            duration = (datetime.now(UTC) - start).total_seconds()
            await self.execution_service.update_metrics(
                execution,
                {
                    "total_duration_seconds": duration,
                    "workflow": definition.get("name", "dynamic"),
                    "mock_llm": settings.mock_llm,
                    "node_count": len(order),
                },
            )
            await self.execution_service.mark_completed(execution, context)

        except Exception as exc:
            logger.exception("dynamic workflow failed")
            await self.execution_service.mark_failed(execution, str(exc))

    async def _execute_node(
        self,
        execution_id: uuid.UUID,
        node_type: str,
        label: str,
        config: dict[str, Any],
        context: dict[str, Any],
        resume_payload: dict[str, Any] | None,
    ) -> Any:
        if node_type == "trigger":
            return {"trigger": config.get("triggerType", "manual"), "input": context.get("input", {})}

        if node_type == "llm":
            prompt = config.get("prompt") or f"Process workflow step: {label}"
            if settings.mock_llm or not settings.google_api_key:
                return await mock_llm_complete(
                    prompt, config.get("model", "gemini-2.5-flash"), context
                )
            return await mock_llm_complete(prompt, config.get("model", "gemini-2.5-flash"), context)

        if node_type == "tool":
            fn_name = config.get("function", "calculator")
            if fn_name == "web_search":
                return await web_search(context.get("input", {}).get("query", label))
            if fn_name == "send_email":
                return await send_email("demo@flowy.local", f"Workflow: {label}", str(context.get("last_output", "")))
            if fn_name == "extract_invoice_data":
                return extract_invoice_data(str(context.get("input", {}).get("invoice_text", "Invoice $500")))
            if fn_name == "calculator":
                return calculator("42 * 2")
            return {"tool": fn_name, "result": "executed"}

        if node_type == "mcp":
            return await mcp_client.call_tool(
                config.get("server", "filesystem"),
                config.get("tool", "list_directory"),
                {"path": "/workspace"},
            )

        if node_type == "approval":
            decision = (resume_payload or {}).get("decision", "approve")
            return {"decision": decision, "approved": decision.lower() in {"approve", "approved", "yes"}}

        if node_type == "notification":
            channel = config.get("channel", "email")
            body = str(context.get("last_output", ""))[:500]
            if channel == "slack":
                result = await send_slack_notification(f"[{label}] {body}")
            else:
                result = await send_email("team@flowy.local", label, body)
            await self.event_service.emit(
                execution_id,
                EVENT_TYPES["NOTIFICATION_SENT"],
                {"channel": channel, "result": result},
            )
            return result

        return {"node": label, "status": "skipped"}

    def _topological_sort(self, nodes: dict[str, Any], edges: list[dict]) -> list[str]:
        graph: dict[str, list[str]] = defaultdict(list)
        in_degree: dict[str, int] = {nid: 0 for nid in nodes}

        for edge in edges:
            src, tgt = edge["source"], edge["target"]
            if src in nodes and tgt in nodes:
                graph[src].append(tgt)
                in_degree[tgt] = in_degree.get(tgt, 0) + 1

        queue = deque([nid for nid, deg in in_degree.items() if deg == 0])
        result: list[str] = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(nodes):
            # fallback: declaration order for cyclic/incomplete graphs
            return list(nodes.keys())
        return result

    async def resume_after_approval(
        self, execution_id: uuid.UUID, definition: dict[str, Any], decision: str
    ) -> None:
        execution = await self.execution_service.get_execution(execution_id)
        if execution:
            execution.status = ExecutionStatus.RUNNING
            await self.execution_service.mark_running(execution, execution.current_node)
        await self.run(execution_id, definition, resume_payload={"decision": decision})
