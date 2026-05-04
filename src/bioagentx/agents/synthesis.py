from bioagentx.agents.base import Agent
from bioagentx.orchestration.state import WorkflowState


class SynthesisAgent(Agent):
    name = "synthesis"

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        source_tags = ", ".join(f"[{source.source_id}]" for source in state.sources[:3]) or "no retrieved sources"
        genes = state.extracted_entities.get("genes", [])
        diseases = state.extracted_entities.get("diseases", [])
        tool_names = sorted({record.tool_name for record in state.tool_calls})
        graph_terms = sorted({term for ctx in state.graph_context.values() for term in ctx.get("expanded_terms", [])})

        reasoning = [
            "Planner decomposed the biomedical question into retrieval, tool analysis, synthesis, and verification steps.",
            f"Research retrieved {len(state.sources)} literature sources and expanded graph context around {', '.join(graph_terms[:8]) or 'the query terms'}.",
            f"Analysis executed required tools: {', '.join(tool_names)}.",
            "Synthesis only uses retrieved sources, graph relationships, and structured tool outputs.",
        ]
        state.reasoning_steps = reasoning

        answer_parts = [
            f"BioAgentX analyzed the query using an agentic workflow with mandatory tool execution ({', '.join(tool_names)}).",
        ]
        if genes:
            answer_parts.append(f"Key gene context: {', '.join(genes)}.")
        if diseases:
            answer_parts.append(f"Disease context: {', '.join(diseases)}.")
        if state.sources:
            top = state.sources[0]
            answer_parts.append(
                f"The strongest retrieved evidence is '{top.title}' ({top.year}), which supports the core biomedical relationship under review [{top.source_id}]."
            )
        if "gene_lookup" in state.analysis_results:
            summaries = []
            for result in state.analysis_results["gene_lookup"]:
                if result.get("found"):
                    summaries.append(f"{result['name']}: {result['function']}")
            if summaries:
                answer_parts.append("Gene lookup results: " + " ".join(summaries))
        if "pathway_analysis" in state.analysis_results:
            top_pathways = state.analysis_results["pathway_analysis"][0].get("top_pathways", [])
            if top_pathways:
                pathway_text = "; ".join(
                    f"{item['gene']}->{item['pathway']} score={item['enrichment_score']}" for item in top_pathways[:3]
                )
                answer_parts.append(f"Pathway analysis prioritized: {pathway_text}.")
        if "clinical_trial_search" in state.analysis_results:
            trial_count = sum(result.get("count", 0) for result in state.analysis_results["clinical_trial_search"])
            answer_parts.append(f"Clinical trial search found {trial_count} matching mock trial records.")
        if "stats_analysis" in state.analysis_results:
            stats = state.analysis_results["stats_analysis"][0]
            if stats.get("n", 0):
                answer_parts.append(f"Stats tool summarized n={stats['n']} observations with mean={stats['mean']}.")
            else:
                answer_parts.append("Stats tool found no numeric observations and recommended formal endpoint/cohort design before inference.")

        if source_tags != "no retrieved sources":
            answer_parts.append(f"Citations used: {source_tags}.")
        answer_parts.append("This is research support, not clinical advice; biomedical conclusions require domain expert review.")
        state.answer = " ".join(answer_parts)
        preliminary_confidence = 0.35 + min(len(state.sources), 4) * 0.08 + min(len(state.tool_calls), 4) * 0.07
        state.confidence_score = round(min(preliminary_confidence, 0.86), 3)
        return {"answer": state.answer, "reasoning_steps": reasoning, "confidence_score": state.confidence_score}
