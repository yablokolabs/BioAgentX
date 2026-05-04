from bioagentx.evaluation.evaluator import Evaluator
from bioagentx.orchestration.state import Source, ToolCallRecord, WorkflowPlanStep, WorkflowState


def test_evaluator_requires_grounding_and_tool_coverage() -> None:
    state = WorkflowState(query="BRCA1 breast cancer")
    state.plan = [WorkflowPlanStep(agent="analysis", objective="tools", required_tools=["gene_lookup"])]
    state.sources = [
        Source(
            source_id="S1",
            title="BRCA1 paper",
            url="https://example.test",
            gene="BRCA1",
            disease="breast cancer",
            year=2020,
            snippet="BRCA1 evidence",
            score=0.9,
        )
    ]
    state.tool_calls = [
        ToolCallRecord(tool_name="gene_lookup", input={"gene": "BRCA1"}, output={"found": True})
    ]
    state.answer = "BRCA1 is related to DNA repair [S1]."

    report = Evaluator().evaluate(state)

    assert report.passed is True
    assert report.grounding_score == 1.0
    assert report.tool_coverage == 1.0
