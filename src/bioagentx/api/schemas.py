from typing import Any, Literal

from pydantic import BaseModel, Field

from bioagentx.orchestration.state import AgentStep, Source, VerificationReport, WorkflowPlanStep


class QueryRequest(BaseModel):
    query: str = Field(min_length=8, max_length=4000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class QueryResponse(BaseModel):
    workflow_id: str
    answer: str
    reasoning_steps: list[str]
    sources: list[Source]
    confidence_score: float
    verification: VerificationReport


class WorkflowResponse(BaseModel):
    workflow_id: str
    query: str
    status: str
    plan: list[WorkflowPlanStep]
    steps: list[AgentStep]
    extracted_entities: dict[str, list[str]]
    graph_context: dict[str, Any]
    tool_calls: list[dict[str, Any]]
    answer: str | None
    confidence_score: float
    verification: VerificationReport | None


class FeedbackRequest(BaseModel):
    workflow_id: str
    label: Literal["correct", "incorrect", "helpful", "not_helpful", "unsafe", "other"]
    comment: str | None = Field(default=None, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackResponse(BaseModel):
    feedback_id: str
    workflow_id: str
    label: str
    status: str = "recorded"


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    database: str
