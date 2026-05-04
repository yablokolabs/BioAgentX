from typing import Any

from bioagentx.agents.base import Agent
from bioagentx.orchestration.state import ToolCallRecord, WorkflowState
from bioagentx.tools.registry import ToolRegistry


class AnalysisAgent(Agent):
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
            inputs = self._inputs_for_tool(tool_name, state.query, genes, diseases)
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

    @staticmethod
    def _inputs_for_tool(
        tool_name: str,
        query: str,
        genes: list[str],
        diseases: list[str],
    ) -> list[dict[str, Any]]:
        if tool_name == "gene_lookup":
            return [{"gene": gene} for gene in genes] or [{"gene": "UNKNOWN"}]
        if tool_name == "pathway_analysis":
            return [{"genes": genes or ["BRCA1"], "query": query}]
        if tool_name == "clinical_trial_search":
            if genes:
                return [{"gene": gene, "disease": diseases[0] if diseases else None} for gene in genes]
            return [{"gene": None, "disease": diseases[0] if diseases else None}]
        if tool_name == "stats_analysis":
            return [{"query": query}]
        return [{"query": query}]
