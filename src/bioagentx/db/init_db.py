import json
import logging
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from bioagentx.core.config import Settings
from bioagentx.rag.embeddings import HashEmbeddingProvider
from bioagentx.rag.seed_data import SEED_PAPERS

logger = logging.getLogger(__name__)


def vector_literal(vector: list[float]) -> str:
    return "[" + ",".join(f"{value:.6f}" for value in vector) + "]"


async def initialise_database(engine: AsyncEngine, settings: Settings) -> None:
    if not settings.auto_create_schema:
        return
    embedder = HashEmbeddingProvider(settings.embedding_dimensions)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgcrypto"))
        await conn.execute(
            text(
                f"""
                CREATE TABLE IF NOT EXISTS bio_papers (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    source_url TEXT NOT NULL,
                    year INTEGER NOT NULL,
                    gene TEXT,
                    disease TEXT,
                    document_type TEXT NOT NULL DEFAULT 'paper',
                    metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                    embedding vector({settings.embedding_dimensions}) NOT NULL
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS bio_papers_embedding_hnsw_idx
                ON bio_papers USING hnsw (embedding vector_cosine_ops)
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS bio_papers_text_gin_idx
                ON bio_papers USING gin (to_tsvector('english', title || ' ' || abstract))
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    workflow_id UUID PRIMARY KEY,
                    query TEXT NOT NULL,
                    state JSONB NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        await conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS feedback_events (
                    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    workflow_id UUID,
                    label TEXT NOT NULL,
                    comment TEXT,
                    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        for paper in SEED_PAPERS:
            embedding = await embedder.embed(f"{paper.title}\n{paper.abstract}")
            params: dict[str, Any] = {
                "paper_id": paper.paper_id,
                "title": paper.title,
                "abstract": paper.abstract,
                "source_url": paper.source_url,
                "year": paper.year,
                "gene": paper.gene,
                "disease": paper.disease,
                "document_type": paper.document_type,
                "metadata": json.dumps(paper.metadata),
                "embedding": vector_literal(embedding),
            }
            await conn.execute(
                text(
                    """
                    INSERT INTO bio_papers
                      (paper_id, title, abstract, source_url, year, gene, disease, document_type, metadata, embedding)
                    VALUES
                      (:paper_id, :title, :abstract, :source_url, :year, :gene, :disease, :document_type,
                       CAST(:metadata AS jsonb), CAST(:embedding AS vector))
                    ON CONFLICT (paper_id) DO UPDATE SET
                      title = EXCLUDED.title,
                      abstract = EXCLUDED.abstract,
                      source_url = EXCLUDED.source_url,
                      year = EXCLUDED.year,
                      gene = EXCLUDED.gene,
                      disease = EXCLUDED.disease,
                      document_type = EXCLUDED.document_type,
                      metadata = EXCLUDED.metadata,
                      embedding = EXCLUDED.embedding
                    """
                ),
                params,
            )
    logger.info("database_initialised")
