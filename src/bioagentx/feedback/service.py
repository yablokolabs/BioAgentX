from typing import Any

from bioagentx.orchestration.store import WorkflowStore


class FeedbackService:
    """Thin service boundary for feedback persistence and later evaluator training hooks."""

    def __init__(self, store: WorkflowStore) -> None:
        self.store = store

    async def record(
        self,
        *,
        workflow_id: str,
        label: str,
        comment: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return await self.store.save_feedback(
            workflow_id=workflow_id,
            label=label,
            comment=comment,
            metadata=metadata,
        )
