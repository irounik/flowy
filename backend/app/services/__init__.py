import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import ApprovalStatus, Execution, ExecutionStatus
from app.repositories import (
    ApprovalRepository,
    EventRepository,
    ExecutionRepository,
    WorkflowRepository,
)

logger = logging.getLogger(__name__)

EVENT_TYPES = {
    "WORKFLOW_STARTED": "WorkflowStarted",
    "WORKFLOW_COMPLETED": "WorkflowCompleted",
    "WORKFLOW_FAILED": "WorkflowFailed",
    "NODE_STARTED": "NodeStarted",
    "NODE_COMPLETED": "NodeCompleted",
    "NODE_FAILED": "NodeFailed",
    "APPROVAL_REQUESTED": "ApprovalRequested",
    "APPROVAL_GRANTED": "ApprovalGranted",
    "APPROVAL_REJECTED": "ApprovalRejected",
    "CHAT_MESSAGE": "ChatMessage",
    "NOTIFICATION_SENT": "NotificationSent",
}


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = EventRepository(session)

    async def emit(
        self,
        execution_id: uuid.UUID,
        event_type: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        payload = payload or {}
        await self.repo.create(execution_id, event_type, payload)
        logger.info(
            "event emitted",
            extra={
                "execution_id": str(execution_id),
                "event_type": event_type,
                "payload": payload,
            },
        )

    async def list_events(self, execution_id: uuid.UUID):
        return await self.repo.list_for_execution(execution_id)


class WorkflowService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = WorkflowRepository(session)

    async def register(self, name: str, description: str | None, version: str):
        existing = await self.repo.get_by_name(name)
        if existing:
            return existing
        return await self.repo.create(name, description, version)

    async def get_by_name(self, name: str):
        return await self.repo.get_by_name(name)

    async def get_by_id(self, workflow_id: uuid.UUID):
        return await self.repo.get_by_id(workflow_id)

    async def list_workflows(self):
        return await self.repo.list_all()

    async def enable(self, name: str):
        workflow = await self.repo.get_by_name(name)
        if not workflow:
            raise ValueError(f"Workflow '{name}' not found")
        from app.database.session import WorkflowStatus

        return await self.repo.set_status(workflow, WorkflowStatus.ENABLED)

    async def disable(self, name: str):
        workflow = await self.repo.get_by_name(name)
        if not workflow:
            raise ValueError(f"Workflow '{name}' not found")
        from app.database.session import WorkflowStatus

        return await self.repo.set_status(workflow, WorkflowStatus.DISABLED)


class ExecutionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ExecutionRepository(session)
        self.event_service = EventService(session)
        self.approval_repo = ApprovalRepository(session)

    async def create_execution(
        self,
        workflow_id: uuid.UUID,
        trigger_type: str,
        context: dict | None = None,
    ) -> Execution:
        execution = await self.repo.create(workflow_id, trigger_type, context)
        await self.event_service.emit(
            execution.id,
            EVENT_TYPES["WORKFLOW_STARTED"],
            {"workflow_id": str(workflow_id), "trigger_type": trigger_type},
        )
        return execution

    async def get_execution(self, execution_id: uuid.UUID) -> Execution | None:
        return await self.repo.get_by_id(execution_id)

    async def list_executions(self, status: str | None = None, workflow_id: uuid.UUID | None = None):
        return await self.repo.list_executions(status=status, workflow_id=workflow_id)

    async def get_execution_detail(self, execution_id: uuid.UUID) -> dict[str, Any] | None:
        execution = await self.repo.get_by_id(execution_id)
        if not execution:
            return None
        events = await self.event_service.list_events(execution_id)
        pending = await self.approval_repo.list_pending_for_execution(execution_id)
        return {
            "execution": execution,
            "history": [
                {
                    "type": event.type,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                }
                for event in events
            ],
            "pending_approvals": pending,
        }

    async def mark_running(self, execution: Execution, current_node: str | None = None) -> Execution:
        execution.status = ExecutionStatus.RUNNING
        if current_node:
            execution.current_node = current_node
        if not execution.started_at:
            execution.started_at = datetime.now(UTC)
        return await self.repo.update(execution)

    async def mark_waiting(self, execution: Execution, current_node: str) -> Execution:
        execution.status = ExecutionStatus.WAITING
        execution.current_node = current_node
        return await self.repo.update(execution)

    async def mark_completed(self, execution: Execution, context: dict | None = None) -> Execution:
        execution.status = ExecutionStatus.COMPLETED
        execution.finished_at = datetime.now(UTC)
        if context:
            execution.context = {**execution.context, **context}
        await self.repo.update(execution)
        await self.event_service.emit(
            execution.id,
            EVENT_TYPES["WORKFLOW_COMPLETED"],
            {"context": execution.context},
        )
        return execution

    async def mark_failed(self, execution: Execution, error: str) -> Execution:
        execution.status = ExecutionStatus.FAILED
        execution.finished_at = datetime.now(UTC)
        execution.context = {**execution.context, "error": error}
        await self.repo.update(execution)
        await self.event_service.emit(
            execution.id,
            EVENT_TYPES["WORKFLOW_FAILED"],
            {"error": error},
        )
        return execution

    async def mark_cancelled(self, execution: Execution) -> Execution:
        execution.status = ExecutionStatus.CANCELLED
        execution.finished_at = datetime.now(UTC)
        return await self.repo.update(execution)

    async def update_context(self, execution: Execution, updates: dict) -> Execution:
        execution.context = {**execution.context, **updates}
        return await self.repo.update(execution)

    async def update_metrics(self, execution: Execution, updates: dict) -> Execution:
        metrics = {**execution.metrics, **updates}
        execution.metrics = metrics
        return await self.repo.update(execution)


class ApprovalService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ApprovalRepository(session)
        self.event_service = EventService(session)
        self.execution_repo = ExecutionRepository(session)

    async def create_request(self, execution_id: uuid.UUID, node_name: str, message: str):
        approval = await self.repo.create(execution_id, node_name)
        execution = await self.execution_repo.get_by_id(execution_id)
        if execution:
            execution.status = ExecutionStatus.WAITING
            execution.current_node = node_name
            await self.execution_repo.update(execution)
        await self.event_service.emit(
            execution_id,
            EVENT_TYPES["APPROVAL_REQUESTED"],
            {
                "approval_id": str(approval.id),
                "node_name": node_name,
                "message": message,
            },
        )
        return approval

    async def respond(self, approval_id: uuid.UUID, decision: str, comments: str | None = None):
        approval = await self.repo.get_by_id(approval_id)
        if not approval:
            raise ValueError("Approval not found")
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError("Approval already responded")

        approved = decision.lower() in {"approve", "approved", "yes"}
        approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval.decision = decision
        approval.comments = comments
        approval.responded_at = datetime.now(UTC)
        await self.repo.update(approval)

        event_type = (
            EVENT_TYPES["APPROVAL_GRANTED"] if approved else EVENT_TYPES["APPROVAL_REJECTED"]
        )
        await self.event_service.emit(
            approval.execution_id,
            event_type,
            {
                "approval_id": str(approval.id),
                "decision": decision,
                "comments": comments,
            },
        )
        return approval, approved
