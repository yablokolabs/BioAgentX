import hashlib
import math
import re

TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


class HashEmbeddingProvider:
    """Deterministic hash-based embedding for local development and tests.

    **Not** a semantic embedding — only useful for demonstrating the
    retrieval pipeline.  Replace with a validated biomedical embedding
    model (e.g. PubMedBERT) for production use.
    """

    def __init__(self, dimensions: int = 64) -> None:
        self.dimensions = dimensions

    async def embed(self, text: str) -> list[float]:
        """Return an L2-normalized vector derived from token hashes."""
        vector = [0.0] * self.dimensions
        for token in TOKEN_RE.findall(text.lower()):
            digest = hashlib.sha256(token.encode()).digest()
            index = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    """Compute cosine similarity between two equal-length vectors."""
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=False))
