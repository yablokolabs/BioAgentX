from bioagentx.agents.base import Agent
from bioagentx.knowledge_graph.graph import KnowledgeGraph
from bioagentx.orchestration.state import Source, WorkflowState
from bioagentx.rag.retrieval import RetrievalService
from bioagentx.rag.types import RetrievalFilter


class ResearchAgent(Agent):
    name = "research"

    def __init__(self, retrieval: RetrievalService, graph: KnowledgeGraph, graph_depth: int = 2) -> None:
        self.retrieval = retrieval
        self.graph = graph
        self.graph_depth = graph_depth

    async def execute(self, state: WorkflowState) -> dict[str, object]:
        genes = state.extracted_entities.get("genes", [])
        diseases = state.extracted_entities.get("diseases", [])
        seed_terms = [*genes, *diseases, *state.extracted_entities.get("pathways", [])]
        neighborhoods = self.graph.expand_terms(seed_terms, depth=self.graph_depth)
        expanded_terms = sorted({term for nb in neighborhoods.values() for term in nb.expanded_terms})
        query = f"{state.query} {' '.join(expanded_terms)}".strip()
        filters = RetrievalFilter(gene=genes[0] if genes else None, disease=diseases[0] if diseases else None)
        hits = await self.retrieval.retrieve(query, filters)
        state.sources = [
            Source(
                source_id=f"S{idx}",
                title=hit.paper.title,
                url=hit.paper.source_url,
                gene=hit.paper.gene,
                disease=hit.paper.disease,
                year=hit.paper.year,
                snippet=hit.paper.abstract[:500],
                score=hit.score,
            )
            for idx, hit in enumerate(hits, start=1)
        ]
        state.graph_context = {
            seed: neighborhood.model_dump() for seed, neighborhood in neighborhoods.items()
        }
        return {
            "source_count": len(state.sources),
            "sources": [source.model_dump() for source in state.sources],
            "expanded_terms": expanded_terms,
        }
