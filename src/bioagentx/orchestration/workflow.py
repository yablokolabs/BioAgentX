import logging
import time

from bioagentx.agents.analysis import AnalysisAgent
from bioagentx.agents.planner import PlannerAgent
from bioagentx.agents.research import ResearchAgent
from bioagentx.agents.synthesis import SynthesisAgent
from bioagentx.agents.verifier import VerifierAgent
from bioagentx.core.metrics import WORKFLOW_LATENCY, WORKFLOW_RUNS
from bioagentx.orchestration.state import StepStatus, WorkflowState
from bioagentx.orchestration.store import WorkflowStore

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """Minimal LangGraph-style state machine for biomedical agent workflows."""

    def __init__(
        self,
        planner: PlannerAgent,
        research: ResearchAgent,
        analysis: AnalysisAgent,
        synthesis: SynthesisAgent,
        verifier: VerifierAgent,
        store: WorkflowStore,
    ) -> None:
        self.planner = planner
        self.research = research
        self.analysis = analysis
        self.synthesis = synthesis
        self.verifier = verifier
        self.store = store

    async def run(self, query: str, trace_id: str | None = None) -> WorkflowState:
        start = time.perf_counter()
        state = WorkflowState(query=query, trace_id=trace_id, status=StepStatus.RUNNING)
        try:
            for agent in [self.planner, self.research, self.analysis, self.synthesis, self.verifier]:
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
