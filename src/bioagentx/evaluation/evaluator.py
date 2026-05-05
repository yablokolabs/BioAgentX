import re

from bioagentx.orchestration.state import VerificationReport, WorkflowState

CLAIM_RISK_TERMS = ("cures", "guarantees", "proves", "always", "never", "definitively")

# Verification scoring weights.
_GROUNDING_WEIGHT = 0.45
_TOOL_WEIGHT = 0.35
_FLAG_WEIGHT = 0.20
_PASS_THRESHOLD = 0.62


class Evaluator:
    """Heuristic evaluator for grounding, tool usage, and hallucination risk.

    Scores are composites of three signals: citation grounding, required
    tool coverage, and absence of overclaim language.
    """

    def evaluate(self, state: WorkflowState) -> VerificationReport:
        """Produce a :class:`VerificationReport` from the current state."""
        answer = state.answer or ""
        source_ids = {src.source_id for src in state.sources}
        cited_ids = set(re.findall(r"\[(S\d+)\]", answer))
        used_sources = source_ids & cited_ids
        grounding_score = len(used_sources) / max(len(source_ids), 1) if source_ids else 0.0

        required_tools = {
            tool for step in state.plan if step.agent == "analysis" for tool in step.required_tools
        }
        executed_tools = {rec.tool_name for rec in state.tool_calls}
        tool_coverage = len(required_tools & executed_tools) / max(len(required_tools), 1)

        flags: list[str] = []
        lower_answer = answer.lower()
        for term in CLAIM_RISK_TERMS:
            if term in lower_answer:
                flags.append(f"absolute_or_overclaim_term:{term}")
        if source_ids and not cited_ids:
            flags.append("retrieved_sources_not_cited")
        if required_tools and tool_coverage < 1.0:
            flags.append("required_tool_not_executed")
        if not state.sources:
            flags.append("no_retrieved_sources")

        correctness_score = round(
            max(
                0.0,
                min(
                    0.98,
                    _GROUNDING_WEIGHT * grounding_score
                    + _TOOL_WEIGHT * tool_coverage
                    + _FLAG_WEIGHT * (0 if flags else 1),
                ),
            ),
            3,
        )
        passed = correctness_score >= _PASS_THRESHOLD and not any(
            flag.startswith("required_tool") for flag in flags
        )
        notes: list[str] = []
        if grounding_score < 0.5:
            notes.append("Increase citation density or retrieval quality.")
        if tool_coverage == 1.0:
            notes.append("All planner-required tools executed.")
        return VerificationReport(
            passed=passed,
            hallucination_flags=flags,
            grounding_score=round(grounding_score, 3),
            tool_coverage=round(tool_coverage, 3),
            correctness_score=correctness_score,
            notes=notes,
        )
