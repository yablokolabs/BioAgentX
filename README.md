# BioAgentX

BioAgentX is a production-style FastAPI platform for agentic biological and clinical data analysis. It is intentionally **not** a chatbot: every workflow is stateful, tool-backed, retrieval-grounded, and verified before returning a scientific answer.

## What it does

- Decomposes biomedical questions into a multi-agent workflow.
- Uses mandatory structured tools for gene lookup, pathway analysis, clinical trial search, and statistics.
- Retrieves literature through RAG with metadata filtering and reranking.
- Expands queries through an in-memory biomedical knowledge graph.
- Produces grounded JSON outputs with answer, reasoning steps, sources, confidence, and verification.
- Stores workflow state and feedback for audit/evaluation.

## Architecture

```text
POST /query
  -> Planner Agent      extracts entities and required tools
  -> Research Agent     graph expansion + vector/keyword RAG
  -> Analysis Agent     executes mandatory tools
  -> Synthesis Agent    creates cited scientific response
  -> Verifier Agent     checks grounding, hallucination risk, tool coverage, score
  -> Workflow Store     saves state and feedback
```

Project layout:

```text
src/bioagentx/
  agents/            planner, research, analysis, synthesis, verifier
  orchestration/     shared state, workflow engine, stores
  tools/             gene/pathway/trial/stat tools + cached registry
  rag/               embeddings, pgvector repository, reranking, seed papers
  knowledge_graph/   in-memory genes/diseases/pathways graph
  evaluation/        hallucination and grounding heuristics
  api/               FastAPI schemas/routes/dependencies
  db/                PostgreSQL + pgvector initialization and store
```

## API

### `POST /query`

```json
{
  "query": "Explain EGFR lung cancer therapy evidence and clinical trials"
}
```

Returns:

```json
{
  "workflow_id": "...",
  "answer": "... [S1] ...",
  "reasoning_steps": ["..."],
  "sources": [{"source_id": "S1", "title": "...", "score": 0.82}],
  "confidence_score": 0.72,
  "verification": {
    "passed": true,
    "hallucination_flags": [],
    "grounding_score": 0.6,
    "tool_coverage": 1.0,
    "correctness_score": 0.82
  }
}
```

### `GET /workflow/{id}`

Returns the full persisted state: plan, steps, graph context, tool calls, answer, and verification.

### `POST /feedback`

```json
{
  "workflow_id": "...",
  "label": "helpful",
  "comment": "useful synthesis"
}
```

### `GET /metrics`

Prometheus counters/histograms for workflows, tools, retrieval, and latency.

## Local development

```bash
uv venv .venv
uv pip install -e '.[dev]'
USE_DATABASE=false .venv/bin/uvicorn bioagentx.main:app --reload
```

Run gates:

```bash
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/python -m compileall -q src tests
```

## Docker

```bash
cp .env.example .env
# edit .env and set POSTGRES_PASSWORD plus DATABASE_URL
docker-compose up --build
```

Services:

- `app` on http://localhost:8080
- `postgres` with `pgvector` enabled

The app seeds a small mock biomedical corpus into PostgreSQL on startup. Keep credentials only in local `.env` (gitignored); the committed example intentionally leaves secrets blank. If PostgreSQL is unavailable, BioAgentX degrades to in-memory RAG and workflow storage so development remains runnable.

## Production notes

- Replace deterministic hash embeddings with validated biomedical embeddings.
- Replace mock tools with versioned connectors to HGNC, Ensembl, PubMed, ClinicalTrials.gov, OMIM/ClinVar, and statistics engines.
- Put auth, tenant isolation, TLS, audit logging, PHI controls, and model/data retention policies in front before handling clinical data.
- Use Redis or an API gateway for distributed rate limiting and cache invalidation.
- Add Neo4j or managed graph storage if the graph grows beyond in-memory footprint.
- Treat generated outputs as research support, not medical advice.
