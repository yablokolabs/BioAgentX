import re

from bioagentx.rag.types import RagHit, RetrievalFilter

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")

# Reranking weights (configurable via subclass or future settings).
_VECTOR_WEIGHT = 0.65
_OVERLAP_WEIGHT = 0.25
_GENE_BOOST = 0.15
_DISEASE_BOOST = 0.15


class SimpleReranker:
    """Combines vector score, keyword overlap, and metadata alignment.

    Produces a composite score that balances semantic similarity with
    lexical and metadata signals.
    """

    def rerank(self, query: str, hits: list[RagHit], filters: RetrievalFilter, limit: int) -> list[RagHit]:
        """Rerank hits and return the top *limit* results."""
        query_terms = set(TOKEN_RE.findall(query.lower()))
        reranked: list[RagHit] = []
        for hit in hits:
            doc_terms = set(TOKEN_RE.findall(f"{hit.paper.title} {hit.paper.abstract}".lower()))
            overlap = len(query_terms & doc_terms) / max(len(query_terms), 1)
            metadata_boost = 0.0
            if filters.gene and hit.paper.gene and filters.gene.upper() == hit.paper.gene.upper():
                metadata_boost += _GENE_BOOST
            if filters.disease and hit.paper.disease and filters.disease.lower() in hit.paper.disease.lower():
                metadata_boost += _DISEASE_BOOST
            score = _VECTOR_WEIGHT * hit.vector_score + _OVERLAP_WEIGHT * overlap + metadata_boost
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
