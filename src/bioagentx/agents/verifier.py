from bioagentx.agents.base import Agent
from bioagentx.evaluation.evaluator import Evaluator
from bioagentx.orchestration.state import WorkflowState


class VerifierAgent(Agent):
    """Evaluates grounding quality and hallucination risk.

    Adjusts the workflow confidence score downward when the verification
    score is lower, and records warnings as structured notes rather than
    mutating the answer text.
    """

    name = "verifier"

    def __init__(self, evaluator: Evaluator) -> None:
        self.evaluator = evaluator

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        report = self.evaluator.evaluate(state)
        state.verification = report
        state.confidence_score = min(state.confidence_score, report.correctness_score)
        if not report.passed:
            warnings = report.hallucination_flags or report.notes
            report.notes = [*report.notes, *(f"warning: {w}" for w in warnings if w not in report.notes)]
        return report.model_dump()
