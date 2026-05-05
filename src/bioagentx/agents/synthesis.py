from bioagentx.agents.base import Agent
from bioagentx.orchestration.state import WorkflowState

# Confidence scoring weights (sum to ~1.0).
_SOURCE_WEIGHT = 0.08
_TOOL_WEIGHT = 0.07
_BASE_CONFIDENCE = 0.35
_MAX_CONTRIBUTING_SOURCES = 4
_MAX_CONTRIBUTING_TOOLS = 4
_CONFIDENCE_CEILING = 0.86


class SynthesisAgent(Agent):
    """Constructs a grounded, cited answer from retrieval and tool outputs."""

    name = "synthesis"

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        source_tags = (
            ", ".join(f"[{src.source_id}]" for src in state.sources[:3]) or "no retrieved sources"
        )
        genes = state.extracted_entities.get("genes", [])
        diseases = state.extracted_entities.get("diseases", [])
        tool_names = sorted({rec.tool_name for rec in state.tool_calls})
        graph_terms = sorted(
            {term for ctx in state.graph_context.values() for term in ctx.get("expanded_terms", [])}
        )

        state.reasoning_steps = self._build_reasoning(state, tool_names, graph_terms)
        state.answer = self._build_answer(state, genes, diseases, tool_names, source_tags)
        state.confidence_score = self._compute_confidence(len(state.sources), len(state.tool_calls))
        return {
            "answer": state.answer,
            "reasoning_steps": state.reasoning_steps,
            "confidence_score": state.confidence_score,
        }

    @staticmethod
    def _build_reasoning(
        state: WorkflowState, tool_names: list[str], graph_terms: list[str]
    ) -> list[str]:
        return [
            "Planner decomposed the biomedical question into retrieval, tool analysis, synthesis, and verification.",
            (
                f"Research retrieved {len(state.sources)} literature sources and expanded graph context "
                f"around {', '.join(graph_terms[:8]) or 'the query terms'}."
            ),
            f"Analysis executed required tools: {', '.join(tool_names)}.",
            "Synthesis only uses retrieved sources, graph relationships, and structured tool outputs.",
        ]

    @staticmethod
    def _build_answer(
        state: WorkflowState,
        genes: list[str],
        diseases: list[str],
        tool_names: list[str],
        source_tags: str,
    ) -> str:
        parts: list[str] = [
            f"BioAgentX analyzed the query using an agentic workflow with mandatory tool execution ({', '.join(tool_names)}).",
        ]
        if genes:
            parts.append(f"Key gene context: {', '.join(genes)}.")
        if diseases:
            parts.append(f"Disease context: {', '.join(diseases)}.")
        if state.sources:
            top = state.sources[0]
            parts.append(
                f"The strongest retrieved evidence is '{top.title}' ({top.year}), "
                f"which supports the core biomedical relationship under review [{top.source_id}]."
            )
        if "gene_lookup" in state.analysis_results:
            summaries = [
                f"{r['name']}: {r['function']}"
                for r in state.analysis_results["gene_lookup"]
                if r.get("found")
            ]
            if summaries:
                parts.append("Gene lookup results: " + " ".join(summaries))
        if "pathway_analysis" in state.analysis_results:
            top_pathways = state.analysis_results["pathway_analysis"][0].get("top_pathways", [])
            if top_pathways:
                pathway_text = "; ".join(
                    f"{item['gene']}->{item['pathway']} score={item['enrichment_score']}"
                    for item in top_pathways[:3]
                )
                parts.append(f"Pathway analysis prioritized: {pathway_text}.")
        if "clinical_trial_search" in state.analysis_results:
            trial_count = sum(
                r.get("count", 0) for r in state.analysis_results["clinical_trial_search"]
            )
            parts.append(f"Clinical trial search found {trial_count} matching mock trial records.")
        if "stats_analysis" in state.analysis_results:
            stats = state.analysis_results["stats_analysis"][0]
            if stats.get("n", 0):
                parts.append(
                    f"Stats tool summarized n={stats['n']} observations with mean={stats['mean']}."
                )
            else:
                parts.append(
                    "Stats tool found no numeric observations and recommended "
                    "formal endpoint/cohort design before inference."
                )
        if source_tags != "no retrieved sources":
            parts.append(f"Citations used: {source_tags}.")
        parts.append(
            "This is research support, not clinical advice; "
            "biomedical conclusions require domain expert review."
        )
        return " ".join(parts)

    @staticmethod
    def _compute_confidence(source_count: int, tool_count: int) -> float:
        raw = (
            _BASE_CONFIDENCE
            + min(source_count, _MAX_CONTRIBUTING_SOURCES) * _SOURCE_WEIGHT
            + min(tool_count, _MAX_CONTRIBUTING_TOOLS) * _TOOL_WEIGHT
        )
        return round(min(raw, _CONFIDENCE_CEILING), 3)
