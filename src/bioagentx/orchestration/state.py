from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class StepStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Source(BaseModel):
    source_id: str
    title: str
    url: str | None = None
    gene: str | None = None
    disease: str | None = None
    year: int | None = None
    snippet: str
    score: float


class ToolCallRecord(BaseModel):
    tool_name: str
    input: dict[str, Any]
    output: dict[str, Any]
    cached: bool = False
    latency_ms: float = 0.0


class AgentStep(BaseModel):
    step_id: str = Field(default_factory=lambda: str(uuid4()))
    agent: str
    action: str
    status: StepStatus = StepStatus.PENDING
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        self.status = StepStatus.RUNNING
        self.started_at = datetime.now(UTC)

    def complete(self, output: dict[str, Any]) -> None:
        self.output = output
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now(UTC)


class WorkflowPlanStep(BaseModel):
    agent: Literal["research", "analysis", "synthesis", "verifier"]
    objective: str
    required_tools: list[str] = Field(default_factory=list)


class VerificationReport(BaseModel):
    passed: bool
    hallucination_flags: list[str] = Field(default_factory=list)
    grounding_score: float
    tool_coverage: float
    correctness_score: float
    notes: list[str] = Field(default_factory=list)


class WorkflowState(BaseModel):
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    query: str
    trace_id: str | None = None
    status: StepStatus = StepStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    extracted_entities: dict[str, list[str]] = Field(default_factory=dict)
    plan: list[WorkflowPlanStep] = Field(default_factory=list)
    steps: list[AgentStep] = Field(default_factory=list)
    graph_context: dict[str, Any] = Field(default_factory=dict)
    sources: list[Source] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    analysis_results: dict[str, Any] = Field(default_factory=dict)
    answer: str | None = None
    reasoning_steps: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    verification: VerificationReport | None = None

    def touch(self) -> None:
        self.updated_at = datetime.now(UTC)

    def add_step(self, step: AgentStep) -> AgentStep:
        self.steps.append(step)
        self.touch()
        return step
