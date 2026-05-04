import re

from bioagentx.rag.types import RagHit, RetrievalFilter

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class SimpleReranker:
    """Combines vector score, keyword overlap, and metadata alignment."""

    def rerank(self, query: str, hits: list[RagHit], filters: RetrievalFilter, limit: int) -> list[RagHit]:
        query_terms = set(TOKEN_RE.findall(query.lower()))
        reranked: list[RagHit] = []
        for hit in hits:
            doc_terms = set(TOKEN_RE.findall(f"{hit.paper.title} {hit.paper.abstract}".lower()))
            overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
            metadata_boost = 0.0
            if filters.gene and hit.paper.gene and filters.gene.upper() == hit.paper.gene.upper():
                metadata_boost += 0.15
            if filters.disease and hit.paper.disease and filters.disease.lower() in hit.paper.disease.lower():
                metadata_boost += 0.15
            score = 0.65 * hit.vector_score + 0.25 * overlap + metadata_boost
            reranked.append(
                hit.model_copy(
                    update={
                        "score": round(score, 4),
                        "keyword_score": round(overlap, 4),
                        "rationale": "vector similarity + lexical overlap + metadata alignment",
                    }
                )
            )
        return sorted(reranked, key=lambda item: item.score, reverse=True)[:limit]
