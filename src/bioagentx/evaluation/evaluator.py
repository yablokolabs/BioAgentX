import re

from bioagentx.orchestration.state import VerificationReport, WorkflowState

CLAIM_RISK_TERMS = ["cures", "guarantees", "proves", "always", "never", "definitively"]


class Evaluator:
    """Heuristic evaluator for grounding, tool usage, and hallucination risk."""

    def evaluate(self, state: WorkflowState) -> VerificationReport:
        answer = state.answer or ""
        source_ids = {source.source_id for source in state.sources}
        cited_ids = set(re.findall(r"\[(S\d+)\]", answer))
        used_sources = source_ids & cited_ids
        grounding_score = len(used_sources) / max(len(source_ids), 1) if source_ids else 0.0
        required_tools = {
            tool for step in state.plan if step.agent == "analysis" for tool in step.required_tools
        }
        executed_tools = {record.tool_name for record in state.tool_calls}
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
            max(0.0, min(0.98, 0.45 * grounding_score + 0.35 * tool_coverage + 0.20 * (0 if flags else 1))),
            3,
        )
        passed = correctness_score >= 0.62 and not any(flag.startswith("required_tool") for flag in flags)
        notes = []
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
