import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import (
    Approval,
    ApprovalStatus,
    ChatMessage,
    ChatSession,
    Event,
    Execution,
    ExecutionStatus,
    Workflow,
    WorkflowStatus,
)


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, name: str, description: str | None, version: str) -> Workflow:
        workflow = Workflow(name=name, description=description, version=version)
        self.session.add(workflow)
        await self.session.commit()
        await self.session.refresh(workflow)
        return workflow

    async def get_by_name(self, name: str) -> Workflow | None:
        result = await self.session.execute(select(Workflow).where(Workflow.name == name))
        return result.scalar_one_or_none()

    async def get_by_id(self, workflow_id: uuid.UUID) -> Workflow | None:
        result = await self.session.execute(select(Workflow).where(Workflow.id == workflow_id))
        return result.scalar_one_or_none()

    async def list_all(self) -> Sequence[Workflow]:
        result = await self.session.execute(select(Workflow).order_by(Workflow.name))
        return result.scalars().all()

    async def set_status(self, workflow: Workflow, status: WorkflowStatus) -> Workflow:
        workflow.status = status
        await self.session.commit()
        await self.session.refresh(workflow)
        return workflow


class ExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        workflow_id: uuid.UUID,
        trigger_type: str,
        context: dict | None = None,
    ) -> Execution:
        execution = Execution(
            workflow_id=workflow_id,
            trigger_type=trigger_type,
            context=context or {},
            status=ExecutionStatus.RUNNING,
        )
        self.session.add(execution)
        await self.session.commit()
        await self.session.refresh(execution)
        return execution

    async def get_by_id(self, execution_id: uuid.UUID) -> Execution | None:
        result = await self.session.execute(select(Execution).where(Execution.id == execution_id))
        return result.scalar_one_or_none()

    async def list_executions(
        self,
        status: str | None = None,
        workflow_id: uuid.UUID | None = None,
    ) -> Sequence[Execution]:
        query = select(Execution).order_by(Execution.created_at.desc())
        if status:
            query = query.where(Execution.status == status)
        if workflow_id:
            query = query.where(Execution.workflow_id == workflow_id)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def update(self, execution: Execution) -> Execution:
        await self.session.commit()
        await self.session.refresh(execution)
        return execution


class ApprovalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, execution_id: uuid.UUID, node_name: str) -> Approval:
        approval = Approval(execution_id=execution_id, node_name=node_name)
        self.session.add(approval)
        await self.session.commit()
        await self.session.refresh(approval)
        return approval

    async def get_by_id(self, approval_id: uuid.UUID) -> Approval | None:
        result = await self.session.execute(select(Approval).where(Approval.id == approval_id))
        return result.scalar_one_or_none()

    async def list_pending_for_execution(self, execution_id: uuid.UUID) -> Sequence[Approval]:
        result = await self.session.execute(
            select(Approval).where(
                Approval.execution_id == execution_id,
                Approval.status == ApprovalStatus.PENDING,
            )
        )
        return result.scalars().all()

    async def update(self, approval: Approval) -> Approval:
        await self.session.commit()
        await self.session.refresh(approval)
        return approval


class EventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, execution_id: uuid.UUID, event_type: str, payload: dict) -> Event:
        event = Event(execution_id=execution_id, type=event_type, payload=payload)
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list_for_execution(self, execution_id: uuid.UUID) -> Sequence[Event]:
        result = await self.session.execute(
            select(Event)
            .where(Event.execution_id == execution_id)
            .order_by(Event.created_at.asc())
        )
        return result.scalars().all()


class ChatRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create_session(self, execution_id: uuid.UUID) -> ChatSession:
        result = await self.session.execute(
            select(ChatSession).where(ChatSession.execution_id == execution_id)
        )
        session = result.scalar_one_or_none()
        if session:
            return session
        session = ChatSession(execution_id=execution_id)
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        return session

    async def add_message(self, session_id: uuid.UUID, role: str, message: str) -> ChatMessage:
        chat_message = ChatMessage(session_id=session_id, role=role, message=message)
        self.session.add(chat_message)
        await self.session.commit()
        await self.session.refresh(chat_message)
        return chat_message

    async def list_messages(self, session_id: uuid.UUID) -> Sequence[ChatMessage]:
        result = await self.session.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return result.scalars().all()
