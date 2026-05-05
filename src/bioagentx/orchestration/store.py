from abc import ABC, abstractmethod
from typing import Any

from bioagentx.orchestration.state import WorkflowState


class WorkflowStore(ABC):
    """Persistence interface for workflow state and feedback events."""

    @abstractmethod
    async def save_workflow(self, state: WorkflowState) -> None: ...

    @abstractmethod
    async def get_workflow(self, workflow_id: str) -> WorkflowState | None: ...

    @abstractmethod
    async def save_feedback(
        self,
        *,
        workflow_id: str,
        label: str,
        comment: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]: ...


class InMemoryWorkflowStore(WorkflowStore):
    """Non-persistent workflow store for development and testing."""

    def __init__(self, *, max_workflows: int = 1024) -> None:
        self.workflows: dict[str, WorkflowState] = {}
        self.feedback: list[dict[str, Any]] = []
        self._max_workflows = max_workflows

    async def save_workflow(self, state: WorkflowState) -> None:
        self.workflows[state.workflow_id] = state.model_copy(deep=True)
        # Evict oldest workflows when the store exceeds the cap.
        while len(self.workflows) > self._max_workflows:
            oldest = next(iter(self.workflows))
            del self.workflows[oldest]

    async def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        state = self.workflows.get(workflow_id)
        return state.model_copy(deep=True) if state else None

    async def save_feedback(
        self,
        *,
        workflow_id: str,
        label: str,
        comment: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "feedback_id": f"fb-{len(self.feedback) + 1}",
            "workflow_id": workflow_id,
            "label": label,
            "comment": comment,
            "metadata": metadata or {},
            "status": "recorded",
        }
        self.feedback.append(record)
        return record
