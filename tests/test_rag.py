import pytest

from bioagentx.rag.embeddings import HashEmbeddingProvider, cosine_similarity
from bioagentx.rag.reranker import SimpleReranker
from bioagentx.rag.types import BioPaper, RagHit, RetrievalFilter


@pytest.mark.asyncio
async def test_hash_embedding_deterministic() -> None:
    provider = HashEmbeddingProvider(dimensions=32)
    v1 = await provider.embed("BRCA1 breast cancer")
    v2 = await provider.embed("BRCA1 breast cancer")

    assert v1 == v2


@pytest.mark.asyncio
async def test_hash_embedding_normalized() -> None:
    provider = HashEmbeddingProvider(dimensions=32)
    vec = await provider.embed("test query")
    norm = sum(v * v for v in vec) ** 0.5

    assert abs(norm - 1.0) < 1e-6


def test_cosine_similarity_identical() -> None:
    vec = [0.5, 0.5, 0.5, 0.5]
    assert abs(cosine_similarity(vec, vec) - 1.0) < 1e-6


def test_cosine_similarity_empty() -> None:
    assert cosine_similarity([], [1.0, 2.0]) == 0.0


def _make_hit(paper_id: str, gene: str | None, disease: str | None, vs: float) -> RagHit:
    return RagHit(
        paper=BioPaper(
            paper_id=paper_id,
            title=f"Paper about {gene or 'topic'}",
            abstract=f"Abstract about {gene or 'topic'} and {disease or 'condition'}",
            source_url="https://example.test",
            year=2023,
            gene=gene,
            disease=disease,
        ),
        score=vs,
        vector_score=vs,
        keyword_score=0.0,
        rationale="test",
    )


def test_reranker_respects_limit() -> None:
    hits = [_make_hit(f"p{i}", "BRCA1", "breast cancer", 0.5 + i * 0.01) for i in range(10)]
    result = SimpleReranker().rerank("BRCA1", hits, RetrievalFilter(), limit=3)

    assert len(result) == 3


def test_reranker_boosts_metadata_match() -> None:
    unmatched = _make_hit("p1", "TP53", "solid tumor", 0.8)
    matched = _make_hit("p2", "BRCA1", "breast cancer", 0.7)
    filters = RetrievalFilter(gene="BRCA1", disease="breast cancer")

    result = SimpleReranker().rerank("BRCA1 breast cancer", [unmatched, matched], filters, limit=2)

    assert result[0].paper.paper_id == "p2"
