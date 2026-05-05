import logging
import time

from bioagentx.agents.base import Agent
from bioagentx.core.metrics import WORKFLOW_LATENCY, WORKFLOW_RUNS
from bioagentx.orchestration.state import StepStatus, WorkflowState
from bioagentx.orchestration.store import WorkflowStore

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Stateful pipeline engine that runs agents in sequence.

    Persists intermediate state after every agent step for auditability.
    """

    def __init__(
        self,
        planner: Agent,
        research: Agent,
        analysis: Agent,
        synthesis: Agent,
        verifier: Agent,
        store: WorkflowStore,
    ) -> None:
        self._agents: list[Agent] = [planner, research, analysis, synthesis, verifier]
        self.store = store

    async def run(self, query: str, trace_id: str | None = None) -> WorkflowState:
        """Execute the full agent pipeline and return final state."""
        start = time.perf_counter()
        state = WorkflowState(query=query, trace_id=trace_id, status=StepStatus.RUNNING)
        try:
            for agent in self._agents:
                state = await agent.run(state)
                await self.store.save_workflow(state)
            state.status = StepStatus.COMPLETED
            state.touch()
            await self.store.save_workflow(state)
            WORKFLOW_RUNS.labels(status="completed").inc()
            return state
        except Exception:
            logger.exception("workflow_failed", extra={"workflow_id": state.workflow_id})
            state.status = StepStatus.FAILED
            state.touch()
            await self.store.save_workflow(state)
            WORKFLOW_RUNS.labels(status="failed").inc()
            raise
        finally:
            WORKFLOW_LATENCY.observe(time.perf_counter() - start)
