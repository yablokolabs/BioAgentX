from abc import ABC, abstractmethod
from typing import Any

from bioagentx.orchestration.state import WorkflowState


class WorkflowStore(ABC):
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
    def __init__(self) -> None:
        self.workflows: dict[str, WorkflowState] = {}
        self.feedback: list[dict[str, Any]] = []

    async def save_workflow(self, state: WorkflowState) -> None:
        self.workflows[state.workflow_id] = state.model_copy(deep=True)

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
        }
        self.feedback.append(record)
        return record
