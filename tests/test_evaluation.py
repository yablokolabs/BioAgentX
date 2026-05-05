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


def test_evaluator_fails_when_tool_missing() -> None:
    state = WorkflowState(query="BRCA1 breast cancer")
    state.plan = [
        WorkflowPlanStep(agent="analysis", objective="tools", required_tools=["gene_lookup", "pathway_analysis"])
    ]
    state.sources = [
        Source(source_id="S1", title="T", url=None, snippet="s", score=0.5, year=2020)
    ]
    state.tool_calls = [
        ToolCallRecord(tool_name="gene_lookup", input={"gene": "BRCA1"}, output={"found": True})
    ]
    state.answer = "Answer [S1]."

    report = Evaluator().evaluate(state)

    assert report.tool_coverage < 1.0
    assert not report.passed
    assert any("required_tool" in f for f in report.hallucination_flags)


def test_evaluator_flags_overclaim_terms() -> None:
    state = WorkflowState(query="gene therapy")
    state.plan = [WorkflowPlanStep(agent="analysis", objective="tools", required_tools=["gene_lookup"])]
    state.tool_calls = [
        ToolCallRecord(tool_name="gene_lookup", input={"gene": "X"}, output={"found": True})
    ]
    state.sources = []
    state.answer = "This therapy cures all diseases."

    report = Evaluator().evaluate(state)

    assert any("cures" in f for f in report.hallucination_flags)


def test_evaluator_no_sources() -> None:
    state = WorkflowState(query="test")
    state.plan = [WorkflowPlanStep(agent="analysis", objective="tools", required_tools=["stats_analysis"])]
    state.tool_calls = [
        ToolCallRecord(tool_name="stats_analysis", input={"query": "test"}, output={"n": 0})
    ]
    state.sources = []
    state.answer = "No data."

    report = Evaluator().evaluate(state)

    assert any("no_retrieved_sources" in f for f in report.hallucination_flags)
