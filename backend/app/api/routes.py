import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.adk.runtime import ADKRuntime, WORKFLOW_REGISTRY
from app.chat.service import ChatService
from app.database.session import WorkflowStatus, async_session_factory, get_db
from app.schemas import (
    ApprovalDecision,
    ApprovalResponse,
    ChatRequest,
    ChatResponse,
    DynamicWorkflowDefinition,
    DynamicWorkflowRunResponse,
    ExecutionDetailResponse,
    ExecutionResponse,
    ExecutionStartResponse,
    ManualTriggerRequest,
    WebhookTriggerRequest,
    WorkflowCreate,
    WorkflowResponse,
)
from app.services import ApprovalService, ExecutionService, WorkflowService

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_workflow_name(session: AsyncSession, workflow: str) -> str:
    if workflow in WORKFLOW_REGISTRY:
        return workflow
    service = WorkflowService(session)
    db_workflow = await service.get_by_name(workflow)
    if db_workflow:
        return db_workflow.name
    raise HTTPException(status_code=404, detail=f"Workflow '{workflow}' not found")


async def _run_workflow_background(
    execution_id: uuid.UUID,
    workflow_name: str,
    input_data: dict | None = None,
) -> None:
    async with async_session_factory() as session:
        runtime = ADKRuntime(session)
        await runtime.run_workflow(execution_id, workflow_name, input_data)


async def _run_dynamic_workflow_background(
    execution_id: uuid.UUID,
    definition: dict,
    resume_payload: dict | None = None,
) -> None:
    from app.adk.dynamic_runner import DynamicWorkflowRunner

    async with async_session_factory() as session:
        runner = DynamicWorkflowRunner(session)
        await runner.run(execution_id, definition, resume_payload)


async def _resume_workflow_background(
    execution_id: uuid.UUID,
    workflow_name: str,
    decision: str,
    comments: str | None,
) -> None:
    async with async_session_factory() as session:
        runtime = ADKRuntime(session)
        await runtime.resume_after_approval(execution_id, workflow_name, decision, comments)


async def _resume_dynamic_workflow_background(
    execution_id: uuid.UUID,
    definition: dict,
    decision: str,
) -> None:
    from app.adk.dynamic_runner import DynamicWorkflowRunner

    async with async_session_factory() as session:
        runner = DynamicWorkflowRunner(session)
        await runner.resume_after_approval(execution_id, definition, decision)


# --- Workflow APIs ---

@router.post("/workflows", response_model=WorkflowResponse)
async def register_workflow(
    body: WorkflowCreate,
    session: AsyncSession = Depends(get_db),
):
    service = WorkflowService(session)
    if body.name not in WORKFLOW_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Workflow '{body.name}' is not implemented. Available: {list(WORKFLOW_REGISTRY)}",
        )
    return await service.register(body.name, body.description, body.version)


@router.get("/workflows", response_model=list[WorkflowResponse])
async def list_workflows(session: AsyncSession = Depends(get_db)):
    service = WorkflowService(session)
    return await service.list_workflows()


@router.post("/workflows/{workflow}/enable", response_model=WorkflowResponse)
async def enable_workflow(workflow: str, session: AsyncSession = Depends(get_db)):
    service = WorkflowService(session)
    try:
        return await service.enable(workflow)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/{workflow}/disable", response_model=WorkflowResponse)
async def disable_workflow(workflow: str, session: AsyncSession = Depends(get_db)):
    service = WorkflowService(session)
    try:
        return await service.disable(workflow)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/workflows/dynamic/run", response_model=DynamicWorkflowRunResponse)
async def run_dynamic_workflow(
    body: DynamicWorkflowDefinition,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """Execute a user-designed workflow graph from the designer UI."""
    if not body.nodes:
        raise HTTPException(status_code=400, detail="Workflow must contain at least one node")

    slug = body.name.lower().replace(" ", "-")
    wf_service = WorkflowService(session)
    db_workflow = await wf_service.get_by_name(slug)
    if not db_workflow:
        db_workflow = await wf_service.register(slug, body.description, body.version)

    definition = body.model_dump()
    exec_service = ExecutionService(session)
    execution = await exec_service.create_execution(
        db_workflow.id,
        trigger_type="dynamic",
        context={"input": body.input, "workflow_definition": definition},
    )
    background_tasks.add_task(_run_dynamic_workflow_background, execution.id, definition)
    return DynamicWorkflowRunResponse(
        execution_id=execution.id,
        workflow_name=slug,
        status="RUNNING",
    )


@router.post("/workflows/{workflow}/run", response_model=ExecutionStartResponse)
async def start_workflow(
    workflow: str,
    background_tasks: BackgroundTasks,
    input: dict | None = None,
    session: AsyncSession = Depends(get_db),
):
    workflow_name = await _get_workflow_name(session, workflow)
    wf_service = WorkflowService(session)
    db_workflow = await wf_service.get_by_name(workflow_name)
    if not db_workflow:
        db_workflow = await wf_service.register(workflow_name, None, "0.1.0")
    if db_workflow.status == WorkflowStatus.DISABLED:
        raise HTTPException(status_code=403, detail="Workflow is disabled")

    exec_service = ExecutionService(session)
    execution = await exec_service.create_execution(
        db_workflow.id,
        trigger_type="manual",
        context={"input": input or {}},
    )
    background_tasks.add_task(_run_workflow_background, execution.id, workflow_name, input)
    return ExecutionStartResponse(execution_id=execution.id)


# --- Trigger APIs ---

@router.post("/triggers/manual", response_model=ExecutionStartResponse)
async def manual_trigger(
    body: ManualTriggerRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    workflow_name = await _get_workflow_name(session, body.workflow)
    wf_service = WorkflowService(session)
    db_workflow = await wf_service.get_by_name(workflow_name)
    if not db_workflow:
        db_workflow = await wf_service.register(workflow_name, None, "0.1.0")

    exec_service = ExecutionService(session)
    execution = await exec_service.create_execution(
        db_workflow.id,
        trigger_type="manual",
        context={"input": body.input},
    )
    background_tasks.add_task(_run_workflow_background, execution.id, workflow_name, body.input)
    return ExecutionStartResponse(execution_id=execution.id)


@router.post("/webhooks/{workflow}", response_model=ExecutionStartResponse)
async def webhook_trigger(
    workflow: str,
    body: WebhookTriggerRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    workflow_name = await _get_workflow_name(session, workflow)
    wf_service = WorkflowService(session)
    db_workflow = await wf_service.get_by_name(workflow_name)
    if not db_workflow:
        db_workflow = await wf_service.register(workflow_name, None, "0.1.0")

    exec_service = ExecutionService(session)
    execution = await exec_service.create_execution(
        db_workflow.id,
        trigger_type="webhook",
        context={"input": body.payload},
    )
    background_tasks.add_task(_run_workflow_background, execution.id, workflow_name, body.payload)
    return ExecutionStartResponse(execution_id=execution.id)


# --- Execution APIs ---

@router.get("/executions", response_model=list[ExecutionResponse])
async def list_executions(
    status: str | None = Query(None),
    workflow: str | None = Query(None),
    session: AsyncSession = Depends(get_db),
):
    workflow_id = None
    if workflow:
        wf_service = WorkflowService(session)
        db_workflow = await wf_service.get_by_name(workflow)
        if db_workflow:
            workflow_id = db_workflow.id

    exec_service = ExecutionService(session)
    return await exec_service.list_executions(status=status, workflow_id=workflow_id)


@router.get("/executions/{execution_id}", response_model=ExecutionDetailResponse)
async def get_execution(execution_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    exec_service = ExecutionService(session)
    detail = await exec_service.get_execution_detail(execution_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Execution not found")

    execution = detail["execution"]
    return ExecutionDetailResponse(
        id=execution.id,
        workflow_id=execution.workflow_id,
        status=execution.status,
        trigger_type=execution.trigger_type,
        started_at=execution.started_at,
        finished_at=execution.finished_at,
        current_node=execution.current_node,
        context=execution.context,
        metrics=execution.metrics,
        created_at=execution.created_at,
        history=detail["history"],
        pending_approvals=detail["pending_approvals"],
    )


@router.post("/executions/{execution_id}/cancel", response_model=ExecutionResponse)
async def cancel_execution(execution_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    exec_service = ExecutionService(session)
    execution = await exec_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return await exec_service.mark_cancelled(execution)


# --- Approval APIs ---

@router.post("/approvals/{approval_id}", response_model=ApprovalResponse)
async def approve_request(
    approval_id: uuid.UUID,
    body: ApprovalDecision,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    approval_service = ApprovalService(session)
    try:
        approval, approved = await approval_service.respond(approval_id, body.decision, body.comments)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if approved:
        execution = await ExecutionService(session).get_execution(approval.execution_id)
        if execution:
            definition = execution.context.get("workflow_definition")
            if definition:
                background_tasks.add_task(
                    _resume_dynamic_workflow_background,
                    approval.execution_id,
                    definition,
                    body.decision,
                )
            else:
                wf_service = WorkflowService(session)
                workflow = await wf_service.get_by_id(execution.workflow_id)
                if workflow:
                    background_tasks.add_task(
                        _resume_workflow_background,
                        approval.execution_id,
                        workflow.name,
                        body.decision,
                        body.comments,
                    )

    return approval


@router.post("/approvals/{approval_id}/reject", response_model=ApprovalResponse)
async def reject_request(
    approval_id: uuid.UUID,
    body: ApprovalDecision,
    session: AsyncSession = Depends(get_db),
):
    approval_service = ApprovalService(session)
    try:
        approval, _ = await approval_service.respond(approval_id, "reject", body.comments)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    execution = await ExecutionService(session).get_execution(approval.execution_id)
    if execution:
        await ExecutionService(session).mark_failed(execution, "Approval rejected")

    return approval


# --- Chat API ---

@router.post("/chat/{execution_id}", response_model=ChatResponse)
async def chat_with_execution(
    execution_id: uuid.UUID,
    body: ChatRequest,
    session: AsyncSession = Depends(get_db),
):
    chat_service = ChatService(session)
    try:
        result = await chat_service.chat(execution_id, body.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ChatResponse(**result)


# --- Event streaming ---

@router.get("/executions/{execution_id}/events")
async def stream_events(execution_id: uuid.UUID, session: AsyncSession = Depends(get_db)):
    exec_service = ExecutionService(session)
    execution = await exec_service.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    from app.events.stream import stream_execution_events

    return EventSourceResponse(stream_execution_events(session, execution_id))
