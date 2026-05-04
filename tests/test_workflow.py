import pytest

from bioagentx.agents.analysis import AnalysisAgent
from bioagentx.agents.planner import PlannerAgent
from bioagentx.agents.research import ResearchAgent
from bioagentx.agents.synthesis import SynthesisAgent
from bioagentx.agents.verifier import VerifierAgent
from bioagentx.evaluation.evaluator import Evaluator
from bioagentx.knowledge_graph.seed import build_seed_graph
from bioagentx.orchestration.store import InMemoryWorkflowStore
from bioagentx.orchestration.workflow import WorkflowEngine
from bioagentx.rag.embeddings import HashEmbeddingProvider
from bioagentx.rag.repository import InMemoryBioPaperRepository
from bioagentx.rag.reranker import SimpleReranker
from bioagentx.rag.retrieval import RetrievalService
from bioagentx.tools.registry import build_default_registry


def build_engine() -> WorkflowEngine:
    graph = build_seed_graph()
    embeddings = HashEmbeddingProvider(64)
    retrieval = RetrievalService(
        repository=InMemoryBioPaperRepository(embeddings),
        embeddings=embeddings,
        reranker=SimpleReranker(),
    )
    return WorkflowEngine(
        planner=PlannerAgent(graph),
        research=ResearchAgent(retrieval, graph),
        analysis=AnalysisAgent(build_default_registry()),
        synthesis=SynthesisAgent(),
        verifier=VerifierAgent(Evaluator()),
        store=InMemoryWorkflowStore(),
    )


@pytest.mark.asyncio
async def test_workflow_runs_tool_backed_biomedical_analysis() -> None:
    engine = build_engine()

    state = await engine.run("How does EGFR affect lung cancer therapy and clinical trials?")

    assert state.answer
    assert state.verification is not None
    assert state.verification.tool_coverage == 1.0
    assert {call.tool_name for call in state.tool_calls} >= {
        "gene_lookup",
        "pathway_analysis",
        "clinical_trial_search",
    }
    assert state.sources
    assert state.confidence_score > 0.5
