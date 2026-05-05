from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from bioagentx import __version__
from bioagentx.api.dependencies import get_workflow_engine, get_workflow_store
from bioagentx.api.schemas import (
    FeedbackRequest,
    FeedbackResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    WorkflowResponse,
)
from bioagentx.core.metrics import metrics_bytes
from bioagentx.orchestration.store import WorkflowStore
from bioagentx.orchestration.workflow import WorkflowEngine

router = APIRouter()
WorkflowEngineDep = Annotated[WorkflowEngine, Depends(get_workflow_engine)]
WorkflowStoreDep = Annotated[WorkflowStore, Depends(get_workflow_store)]


@router.get("/health", response_model=HealthResponse)
async def health(request: Request) -> HealthResponse:
    """Liveness / readiness probe."""
    return HealthResponse(
        status="ok",
        app="BioAgentX",
        version=__version__,
        database=getattr(request.app.state, "database_status", "unknown"),
    )


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest, request: Request, engine: WorkflowEngineDep) -> QueryResponse:
    """Submit a biomedical question and receive a tool-backed answer."""
    trace_id = getattr(request.state, "trace_id", None)
    state = await engine.run(payload.query, trace_id=trace_id)
    if state.answer is None or state.verification is None:
        raise HTTPException(status_code=500, detail="Workflow completed without answer or verification.")
    return QueryResponse(
        workflow_id=state.workflow_id,
        answer=state.answer,
        reasoning_steps=state.reasoning_steps,
        sources=state.sources,
        confidence_score=state.confidence_score,
        verification=state.verification,
    )


@router.get("/workflow/{workflow_id}", response_model=WorkflowResponse)
async def workflow(workflow_id: str, store: WorkflowStoreDep) -> WorkflowResponse:
    """Retrieve the full persisted state of a previous workflow run."""
    state = await store.get_workflow(workflow_id)
    if state is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    return WorkflowResponse(
        workflow_id=state.workflow_id,
        query=state.query,
        status=state.status.value,
        plan=state.plan,
        steps=state.steps,
        extracted_entities=state.extracted_entities,
        graph_context=state.graph_context,
        tool_calls=state.tool_calls,
        answer=state.answer,
        confidence_score=state.confidence_score,
        verification=state.verification,
    )


@router.post("/feedback", response_model=FeedbackResponse)
async def feedback(payload: FeedbackRequest, store: WorkflowStoreDep) -> FeedbackResponse:
    """Record user feedback for a completed workflow."""
    if await store.get_workflow(payload.workflow_id) is None:
        raise HTTPException(status_code=404, detail="workflow_not_found")
    record = await store.save_feedback(
        workflow_id=payload.workflow_id,
        label=payload.label,
        comment=payload.comment,
        metadata=payload.metadata,
    )
    return FeedbackResponse(**record)


@router.get("/metrics")
async def metrics() -> Response:
    """Prometheus-compatible metrics endpoint."""
    return Response(content=metrics_bytes(), media_type="text/plain; version=0.0.4")
