from bioagentx.rag.embeddings import HashEmbeddingProvider
from bioagentx.rag.repository import BioPaperRepository
from bioagentx.rag.reranker import SimpleReranker
from bioagentx.rag.types import RagHit, RetrievalFilter


class RetrievalService:
    def __init__(
        self,
        repository: BioPaperRepository,
        embeddings: HashEmbeddingProvider,
        reranker: SimpleReranker,
        retrieval_limit: int = 8,
        rerank_limit: int = 5,
    ) -> None:
        self.repository = repository
        self.embeddings = embeddings
        self.reranker = reranker
        self.retrieval_limit = retrieval_limit
        self.rerank_limit = rerank_limit

    async def retrieve(self, query: str, filters: RetrievalFilter) -> list[RagHit]:
        query_embedding = await self.embeddings.embed(query)
        hits = await self.repository.search(query, query_embedding, filters, self.retrieval_limit)
        return self.reranker.rerank(query, hits, filters, self.rerank_limit)
