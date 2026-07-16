"""Execution-aware chat service."""

import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.adk.prompts.system import CHAT_SYSTEM_PROMPT
from app.config import settings
from app.repositories import ChatRepository, EventRepository, ExecutionRepository
from app.services import EVENT_TYPES, EventService


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self.chat_repo = ChatRepository(session)
        self.execution_repo = ExecutionRepository(session)
        self.event_repo = EventRepository(session)
        self.event_service = EventService(session)

    async def chat(self, execution_id: uuid.UUID, user_message: str) -> dict[str, Any]:
        execution = await self.execution_repo.get_by_id(execution_id)
        if not execution:
            raise ValueError("Execution not found")

        session = await self.chat_repo.get_or_create_session(execution_id)
        await self.chat_repo.add_message(session.id, "user", user_message)

        context = await self._build_context(execution)
        response = await self._generate_response(user_message, context)

        assistant_message = await self.chat_repo.add_message(session.id, "assistant", response)
        await self.event_service.emit(
            execution_id,
            EVENT_TYPES["CHAT_MESSAGE"],
            {"role": "assistant", "message": response},
        )

        return {
            "session_id": session.id,
            "role": assistant_message.role,
            "message": assistant_message.message,
            "created_at": assistant_message.created_at,
        }

    async def _build_context(self, execution) -> dict[str, Any]:
        events = await self.event_repo.list_for_execution(execution.id)
        pending_approvals = [
            {
                "id": str(a.id),
                "node_name": a.node_name,
                "status": a.status,
            }
            for a in execution.approvals
            if a.status == "PENDING"
        ]

        return {
            "workflow_id": str(execution.workflow_id),
            "status": execution.status,
            "current_node": execution.current_node,
            "context": execution.context,
            "metrics": execution.metrics,
            "pending_approvals": pending_approvals,
            "recent_events": [
                {"type": e.type, "payload": e.payload, "created_at": e.created_at.isoformat()}
                for e in events[-10:]
            ],
        }

    async def _generate_response(self, user_message: str, context: dict[str, Any]) -> str:
        if settings.google_api_key:
            try:
                return await self._gemini_response(user_message, context)
            except Exception:
                pass
        return self._stub_response(user_message, context)

    async def _gemini_response(self, user_message: str, context: dict[str, Any]) -> str:
        import httpx

        prompt = (
            f"{CHAT_SYSTEM_PROMPT}\n\n"
            f"Execution context:\n{context}\n\n"
            f"User question: {user_message}"
        )

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
                params={"key": settings.google_api_key},
                json={"contents": [{"parts": [{"text": prompt}]}]},
                timeout=30.0,
            )
            response.raise_for_status()
            data = response.json()
            return data["candidates"][0]["content"]["parts"][0]["text"]

    def _stub_response(self, user_message: str, context: dict[str, Any]) -> str:
        status = context.get("status", "unknown")
        current_node = context.get("current_node") or "none"
        pending = context.get("pending_approvals", [])

        lines = [
            f"The workflow is currently **{status}**.",
            f"Active node: **{current_node}**.",
        ]

        if pending:
            approval_list = ", ".join(f"{a['node_name']} ({a['id'][:8]}...)" for a in pending)
            lines.append(f"Pending approvals: {approval_list}")
        elif status == "WAITING":
            lines.append("The workflow is waiting, but no pending approvals were found.")

        if context.get("context", {}).get("summary"):
            lines.append(f"Summary: {context['context']['summary']}")

        lines.append(f"\nRe: your question — {user_message}")
        return "\n".join(lines)
