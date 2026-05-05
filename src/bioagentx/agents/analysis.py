from typing import Any

from bioagentx.agents.base import Agent
from bioagentx.orchestration.state import ToolCallRecord, WorkflowState
from bioagentx.tools.registry import ToolRegistry

_TOOL_INPUT_BUILDERS: dict[str, Any] = {}  # populated at module level below


class AnalysisAgent(Agent):
    """Executes all planner-required tools and records structured outputs."""

    name = "analysis"

    def __init__(self, tools: ToolRegistry) -> None:
        self.tools = tools

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        required_tools = []
        for step in state.plan:
            if step.agent == "analysis":
                required_tools.extend(step.required_tools)
        required_tools = list(dict.fromkeys(required_tools))
        if not required_tools:
            raise RuntimeError("Planner failed to require tool usage; refusing chatbot-only execution.")

        genes = state.extracted_entities.get("genes", [])
        diseases = state.extracted_entities.get("diseases", [])
        results: dict[str, list[dict[str, Any]]] = {}

        for tool_name in required_tools:
            inputs = _build_tool_inputs(tool_name, state.query, genes, diseases)
            for tool_input in inputs:
                result, cached = await self.tools.call(tool_name, tool_input)
                record = ToolCallRecord(
                    tool_name=tool_name,
                    input=tool_input,
                    output=result.output,
                    cached=cached,
                    latency_ms=result.latency_ms,
                )
                state.tool_calls.append(record)
                results.setdefault(tool_name, []).append(result.output)

        state.analysis_results = results
        return {"tool_results": results, "tool_call_count": len(state.tool_calls)}


def _build_tool_inputs(
    tool_name: str,
    query: str,
    genes: list[str],
    diseases: list[str],
) -> list[dict[str, Any]]:
    """Build tool input payloads from extracted entities.

    Uses a dispatch dict for cleaner extension.  Falls back to the raw
    query string for unrecognised tools.
    """
    builders = {
        "gene_lookup": lambda: [{"gene": g} for g in genes] if genes else [],
        "pathway_analysis": lambda: [{"genes": genes, "query": query}] if genes else [],
        "clinical_trial_search": lambda: (
            [{"gene": g, "disease": diseases[0] if diseases else None} for g in genes]
            if genes
            else [{"gene": None, "disease": diseases[0] if diseases else None}]
        ),
        "stats_analysis": lambda: [{"query": query}],
    }
    builder = builders.get(tool_name)
    if builder is None:
        return [{"query": query}]
    result = builder()
    return result if result else [{"query": query}]
