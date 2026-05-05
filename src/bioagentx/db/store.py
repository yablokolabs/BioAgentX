import json
import logging
import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bioagentx.orchestration.state import WorkflowState
from bioagentx.orchestration.store import WorkflowStore

logger = logging.getLogger(__name__)


class PostgresWorkflowStore(WorkflowStore):
    """Postgres-backed workflow and feedback persistence layer."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def save_workflow(self, state: WorkflowState) -> None:
        """Upsert the workflow state into ``workflow_runs``."""
        async with self.session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO workflow_runs (workflow_id, query, state, status, created_at, updated_at)
                    VALUES (:workflow_id, :query, CAST(:state AS jsonb), :status, :created_at, :updated_at)
                    ON CONFLICT (workflow_id) DO UPDATE SET
                      query = EXCLUDED.query,
                      state = EXCLUDED.state,
                      status = EXCLUDED.status,
                      updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "workflow_id": state.workflow_id,
                    "query": state.query,
                    "state": state.model_dump_json(),
                    "status": state.status.value,
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                },
            )
            await session.commit()

    async def get_workflow(self, workflow_id: str) -> WorkflowState | None:
        """Load a previously persisted workflow by ID."""
        async with self.session_factory() as session:
            row = (
                (
                    await session.execute(
                        text("SELECT state FROM workflow_runs WHERE workflow_id = :workflow_id"),
                        {"workflow_id": workflow_id},
                    )
                )
                .mappings()
                .first()
            )
        if not row:
            return None
        return WorkflowState.model_validate(row["state"])

    async def save_feedback(
        self,
        *,
        workflow_id: str,
        label: str,
        comment: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Insert a feedback event linked to a workflow run."""
        feedback_id = str(uuid.uuid4())
        async with self.session_factory() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO feedback_events (feedback_id, workflow_id, label, comment, metadata)
                    VALUES (:feedback_id, :workflow_id, :label, :comment, CAST(:metadata AS jsonb))
                    """
                ),
                {
                    "feedback_id": feedback_id,
                    "workflow_id": workflow_id,
                    "label": label,
                    "comment": comment,
                    "metadata": json.dumps(metadata or {}),
                },
            )
            await session.commit()
        return {
            "feedback_id": feedback_id,
            "workflow_id": workflow_id,
            "label": label,
            "status": "recorded",
        }
