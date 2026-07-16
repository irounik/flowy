import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WorkflowCreate(BaseModel):
    name: str
    description: str | None = None
    version: str = "0.1.0"


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    version: str
    status: str
    created_at: datetime
    updated_at: datetime


class ExecutionStartResponse(BaseModel):
    execution_id: uuid.UUID


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    trigger_type: str
    started_at: datetime | None
    finished_at: datetime | None
    current_node: str | None
    context: dict[str, Any]
    metrics: dict[str, Any]
    created_at: datetime


class ExecutionDetailResponse(ExecutionResponse):
    history: list[dict[str, Any]] = Field(default_factory=list)
    pending_approvals: list["ApprovalResponse"] = Field(default_factory=list)


class ApprovalDecision(BaseModel):
    decision: str
    comments: str | None = None


class ApprovalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    node_name: str
    status: str
    decision: str | None
    requested_at: datetime
    responded_at: datetime | None
    comments: str | None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    session_id: uuid.UUID
    role: str
    message: str
    created_at: datetime


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    execution_id: uuid.UUID
    type: str
    payload: dict[str, Any]
    created_at: datetime


class ManualTriggerRequest(BaseModel):
    workflow: str
    input: dict[str, Any] = Field(default_factory=dict)


class WebhookTriggerRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
