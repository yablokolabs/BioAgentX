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

## Quick start

### Local development (no database)

```bash
uv venv .venv
uv pip install -e '.[dev]'
USE_DATABASE=false .venv/bin/uvicorn bioagentx.main:app --reload
```

### Docker Compose (with PostgreSQL + pgvector)

```bash
cp .env.example .env
# edit .env — set POSTGRES_PASSWORD and DATABASE_URL
docker-compose up --build
```

Services:

- `app` on http://localhost:8080
- `postgres` with `pgvector` enabled

## Usage examples

### Submit a biomedical query

```bash
curl -s -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain EGFR lung cancer therapy evidence and clinical trials"}' \
  | python -m json.tool
```

**Response:**

```json
{
  "workflow_id": "a1b2c3d4-...",
  "answer": "BioAgentX analyzed the query using an agentic workflow with mandatory tool execution (clinical_trial_search, gene_lookup, pathway_analysis). Key gene context: EGFR. Disease context: lung cancer. ...",
  "reasoning_steps": [
    "Planner decomposed the biomedical question into retrieval, tool analysis, synthesis, and verification.",
    "Research retrieved 5 literature sources and expanded graph context around EGFR, EGFR signaling, ...",
    "Analysis executed required tools: clinical_trial_search, gene_lookup, pathway_analysis.",
    "Synthesis only uses retrieved sources, graph relationships, and structured tool outputs."
  ],
  "sources": [
    {
      "source_id": "S1",
      "title": "EGFR mutations and targeted therapy in non-small cell lung cancer",
      "url": "https://pubmed.ncbi.nlm.nih.gov/1003/",
      "gene": "EGFR",
      "disease": "lung cancer",
      "year": 2021,
      "snippet": "Activating EGFR mutations can drive non-small cell lung cancer...",
      "score": 0.82
    }
  ],
  "confidence_score": 0.72,
  "verification": {
    "passed": true,
    "hallucination_flags": [],
    "grounding_score": 0.6,
    "tool_coverage": 1.0,
    "correctness_score": 0.82,
    "notes": ["All planner-required tools executed."]
  }
}
```

### Retrieve a workflow audit trail

```bash
curl -s http://localhost:8080/workflow/a1b2c3d4-... | python -m json.tool
```

### Submit feedback

```bash
curl -s -X POST http://localhost:8080/feedback \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "a1b2c3d4-...", "label": "helpful", "comment": "useful synthesis"}'
```

### Check health

```bash
curl -s http://localhost:8080/health | python -m json.tool
```

```json
{
  "status": "ok",
  "app": "BioAgentX",
  "version": "0.1.0",
  "database": "disabled"
}
```

### Prometheus metrics

```bash
curl -s http://localhost:8080/metrics
```

### Python client example

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient(base_url="http://localhost:8080", timeout=30) as client:
        # Submit a query
        resp = await client.post("/query", json={
            "query": "What is the role of TP53 in solid tumor pathology?"
        })
        resp.raise_for_status()
        result = resp.json()

        print(f"Workflow ID: {result['workflow_id']}")
        print(f"Confidence:  {result['confidence_score']}")
        print(f"Verified:    {result['verification']['passed']}")
        print(f"Answer:      {result['answer'][:200]}...")

        # Leave feedback
        await client.post("/feedback", json={
            "workflow_id": result["workflow_id"],
            "label": "correct",
            "comment": "Accurate gene function summary."
        })

asyncio.run(main())
```

## API reference

| Endpoint                    | Method | Description                                |
| --------------------------- | ------ | ------------------------------------------ |
| `/health`                   | GET    | Liveness/readiness probe                   |
| `/query`                    | POST   | Submit a biomedical question               |
| `/workflow/{workflow_id}`   | GET    | Full audit trail of a completed workflow   |
| `/feedback`                 | POST   | Record user feedback on a workflow         |
| `/metrics`                  | GET    | Prometheus counters and histograms         |

## Quality gates

```bash
.venv/bin/ruff check .
.venv/bin/pytest
.venv/bin/python -m compileall -q src tests
```

## Production notes

- Replace deterministic hash embeddings with validated biomedical embeddings (e.g., PubMedBERT).
- Replace mock tools with versioned connectors to HGNC, Ensembl, PubMed, ClinicalTrials.gov, OMIM/ClinVar, and statistics engines.
- Put auth, tenant isolation, TLS, audit logging, PHI controls, and model/data retention policies in front before handling clinical data.
- Use Redis or an API gateway for distributed rate limiting and cache invalidation.
- Add Neo4j or managed graph storage if the graph grows beyond in-memory footprint.
- Treat generated outputs as research support, not medical advice.
