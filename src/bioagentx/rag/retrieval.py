from __future__ import annotations

from typing import Protocol

from bioagentx.rag.repository import BioPaperRepository
from bioagentx.rag.types import RagHit, RetrievalFilter


class EmbeddingProvider(Protocol):
    """Protocol for embedding providers — allows swapping implementations."""

    async def embed(self, text: str) -> list[float]: ...


class Reranker(Protocol):
    """Protocol for reranker implementations."""

    def rerank(
        self, query: str, hits: list[RagHit], filters: RetrievalFilter, limit: int
    ) -> list[RagHit]: ...


class RetrievalService:
    """Orchestrates retrieval: embed query → repository search → rerank."""

    def __init__(
        self,
        repository: BioPaperRepository,
        embeddings: EmbeddingProvider,
        reranker: Reranker,
        retrieval_limit: int = 8,
        rerank_limit: int = 5,
    ) -> None:
        self.repository = repository
        self.embeddings = embeddings
        self.reranker = reranker
        self.retrieval_limit = retrieval_limit
        self.rerank_limit = rerank_limit

    async def retrieve(self, query: str, filters: RetrievalFilter) -> list[RagHit]:
        """Retrieve, rerank, and return the top matching papers."""
        query_embedding = await self.embeddings.embed(query)
        hits = await self.repository.search(query, query_embedding, filters, self.retrieval_limit)
        return self.reranker.rerank(query, hits, filters, self.rerank_limit)
