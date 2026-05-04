from bioagentx.agents.base import Agent
from bioagentx.evaluation.evaluator import Evaluator
from bioagentx.orchestration.state import WorkflowState


class VerifierAgent(Agent):
    name = "verifier"

    def __init__(self, evaluator: Evaluator) -> None:
        self.evaluator = evaluator

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        report = self.evaluator.evaluate(state)
        state.verification = report
        state.confidence_score = min(state.confidence_score, report.correctness_score)
        if not report.passed:
            state.answer = (
                f"{state.answer or ''} Verification warning: "
                f"{'; '.join(report.hallucination_flags or report.notes)}"
            ).strip()
        return report.model_dump()
