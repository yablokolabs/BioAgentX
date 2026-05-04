from bioagentx.agents.base import Agent
from bioagentx.knowledge_graph.graph import KnowledgeGraph
from bioagentx.orchestration.state import WorkflowPlanStep, WorkflowState


class PlannerAgent(Agent):
    name = "planner"

    def __init__(self, graph: KnowledgeGraph) -> None:
        self.graph = graph

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        entities = self.graph.extract_known_terms(state.query)
        lowered = state.query.lower()
        required_tools: list[str] = []
        genes = entities.get("genes", [])
        diseases = entities.get("diseases", [])

        if genes:
            required_tools.append("gene_lookup")
        if genes or "pathway" in lowered or entities.get("pathways"):
            required_tools.append("pathway_analysis")
        if diseases or "trial" in lowered or "therapy" in lowered or "clinical" in lowered:
            required_tools.append("clinical_trial_search")
        if any(token in lowered for token in ["stats", "p-value", "significant", "cohort", "mean", "median"]):
            required_tools.append("stats_analysis")

        # Enforce real tool use even for broad scientific questions.
        if not required_tools:
            required_tools.append("stats_analysis")

        # Preserve order while removing duplicates.
        ordered_tools = list(dict.fromkeys(required_tools))
        state.extracted_entities = entities
        state.plan = [
            WorkflowPlanStep(
                agent="research",
                objective="Retrieve biomedical literature and expand query using graph neighbors.",
            ),
            WorkflowPlanStep(
                agent="analysis",
                objective="Call mandatory computational tools and store structured outputs.",
                required_tools=ordered_tools,
            ),
            WorkflowPlanStep(
                agent="synthesis",
                objective="Synthesize grounded answer with citations and reasoning.",
            ),
            WorkflowPlanStep(
                agent="verifier",
                objective="Check grounding, hallucination risk, tool coverage, and confidence.",
            ),
        ]
        return {"entities": entities, "required_tools": ordered_tools, "plan": [step.model_dump() for step in state.plan]}
