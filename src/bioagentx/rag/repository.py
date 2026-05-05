import logging
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bioagentx.core.metrics import RETRIEVALS
from bioagentx.rag.embeddings import HashEmbeddingProvider, cosine_similarity
from bioagentx.rag.seed_data import SEED_PAPERS
from bioagentx.rag.types import BioPaper, RagHit, RetrievalFilter

logger = logging.getLogger(__name__)


class BioPaperRepository(ABC):
    """Interface for searching biomedical papers."""

    @abstractmethod
    async def search(
        self,
        query: str,
        query_embedding: list[float],
        filters: RetrievalFilter,
        limit: int,
    ) -> list[RagHit]: ...


class InMemoryBioPaperRepository(BioPaperRepository):
    """In-memory paper store using hash-based embeddings for vector search."""

    def __init__(self, embedding_provider: HashEmbeddingProvider, papers: list[BioPaper] | None = None) -> None:
        self.embedding_provider = embedding_provider
        self.papers = papers or SEED_PAPERS
        self._embeddings: dict[str, list[float]] = {}

    async def _embedding_for(self, paper: BioPaper) -> list[float]:
        cached = self._embeddings.get(paper.paper_id)
        if cached is not None:
            return cached
        embedding = await self.embedding_provider.embed(f"{paper.title}\n{paper.abstract}")
        self._embeddings[paper.paper_id] = embedding
        return embedding

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        filters: RetrievalFilter,
        limit: int,
    ) -> list[RagHit]:
        RETRIEVALS.labels(backend="memory").inc()
        hits: list[RagHit] = []
        for paper in self.papers:
            if filters.gene and paper.gene and paper.gene.upper() != filters.gene.upper():
                continue
            if filters.disease and paper.disease and filters.disease.lower() not in paper.disease.lower():
                continue
            if filters.document_type and paper.document_type != filters.document_type:
                continue
            vector_score = cosine_similarity(query_embedding, await self._embedding_for(paper))
            hits.append(
                RagHit(
                    paper=paper,
                    score=round(vector_score, 4),
                    vector_score=round(vector_score, 4),
                    keyword_score=0.0,
                    rationale="in-memory vector search",
                )
            )
        return sorted(hits, key=lambda item: item.vector_score, reverse=True)[:limit]


class PostgresBioPaperRepository(BioPaperRepository):
    """Postgres + pgvector paper repository with hybrid keyword/vector search."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def search(
        self,
        query: str,
        query_embedding: list[float],
        filters: RetrievalFilter,
        limit: int,
    ) -> list[RagHit]:
        RETRIEVALS.labels(backend="postgres").inc()
        params: dict[str, Any] = {
            "query": query,
            "embedding": self._vector_literal(query_embedding),
            "gene": filters.gene.upper() if filters.gene else None,
            "disease": filters.disease.lower() if filters.disease else None,
            "document_type": filters.document_type,
            "limit": limit,
        }
        sql = text(
            """
            WITH vector_candidates AS (
              SELECT *, 1 - (embedding <=> CAST(:embedding AS vector)) AS vector_score
              FROM bio_papers
              WHERE (:gene IS NULL OR upper(gene) = :gene)
                AND (:disease IS NULL OR lower(disease) LIKE '%' || :disease || '%')
                AND (:document_type IS NULL OR document_type = :document_type)
              ORDER BY embedding <=> CAST(:embedding AS vector)
              LIMIT (:limit * 6)
            ), keyword_candidates AS (
              SELECT *,
                ts_rank_cd(to_tsvector('english', title || ' ' || abstract), plainto_tsquery('english', :query)) AS keyword_score
              FROM bio_papers
              WHERE to_tsvector('english', title || ' ' || abstract) @@ plainto_tsquery('english', :query)
              LIMIT (:limit * 6)
            ), candidates AS (
              SELECT paper_id FROM vector_candidates
              UNION
              SELECT paper_id FROM keyword_candidates
            )
            SELECT p.*,
              1 - (p.embedding <=> CAST(:embedding AS vector)) AS vector_score,
              ts_rank_cd(to_tsvector('english', p.title || ' ' || p.abstract), plainto_tsquery('english', :query)) AS keyword_score
            FROM bio_papers p
            JOIN candidates c ON c.paper_id = p.paper_id
            ORDER BY (0.75 * (1 - (p.embedding <=> CAST(:embedding AS vector))) +
                      0.25 * ts_rank_cd(to_tsvector('english', p.title || ' ' || p.abstract), plainto_tsquery('english', :query))) DESC
            LIMIT :limit
            """
        )
        try:
            async with self.session_factory() as session:
                rows = (await session.execute(sql, params)).mappings().all()
        except Exception:
            logger.exception("postgres_rag_search_failed")
            return []
        return [self._row_to_hit(row) for row in rows]

    @staticmethod
    def _vector_literal(vector: list[float]) -> str:
        from bioagentx.db.session import vector_literal
        return vector_literal(vector)

    @staticmethod
    def _row_to_hit(row: Any) -> RagHit:
        paper = BioPaper(
            paper_id=row["paper_id"],
            title=row["title"],
            abstract=row["abstract"],
            source_url=row["source_url"],
            year=row["year"],
            gene=row["gene"],
            disease=row["disease"],
            document_type=row["document_type"],
            metadata=dict(row["metadata"] or {}),
        )
        vector_score = float(row["vector_score"] or 0.0)
        keyword_score = float(row["keyword_score"] or 0.0)
        return RagHit(
            paper=paper,
            score=round((0.75 * vector_score) + (0.25 * keyword_score), 4),
            vector_score=round(vector_score, 4),
            keyword_score=round(keyword_score, 4),
            rationale="postgres pgvector + full text search",
        )
