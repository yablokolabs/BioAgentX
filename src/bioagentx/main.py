import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from bioagentx import __version__
from bioagentx.agents.analysis import AnalysisAgent
from bioagentx.agents.planner import PlannerAgent
from bioagentx.agents.research import ResearchAgent
from bioagentx.agents.synthesis import SynthesisAgent
from bioagentx.agents.verifier import VerifierAgent
from bioagentx.api.routes import router
from bioagentx.core.config import get_settings
from bioagentx.core.logging import configure_logging
from bioagentx.core.middleware import RequestContextMiddleware
from bioagentx.core.rate_limit import InMemoryRateLimitMiddleware
from bioagentx.db.init_db import initialise_database
from bioagentx.db.session import create_engine, create_session_factory
from bioagentx.db.store import PostgresWorkflowStore
from bioagentx.evaluation.evaluator import Evaluator
from bioagentx.knowledge_graph.seed import build_seed_graph
from bioagentx.orchestration.store import InMemoryWorkflowStore, WorkflowStore
from bioagentx.orchestration.workflow import WorkflowEngine
from bioagentx.rag.embeddings import HashEmbeddingProvider
from bioagentx.rag.repository import InMemoryBioPaperRepository, PostgresBioPaperRepository
from bioagentx.rag.reranker import SimpleReranker
from bioagentx.rag.retrieval import RetrievalService
from bioagentx.tools.registry import build_default_registry

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    graph = build_seed_graph()
    embeddings = HashEmbeddingProvider(settings.embedding_dimensions)
    engine = None
    store: WorkflowStore = InMemoryWorkflowStore()
    repository = InMemoryBioPaperRepository(embeddings)
    app.state.database_status = "disabled"

    if settings.use_database:
        try:
            engine = create_engine(settings)
            session_factory = create_session_factory(engine)
            await initialise_database(engine, settings)
            repository = PostgresBioPaperRepository(session_factory)
            store = PostgresWorkflowStore(session_factory)
            app.state.database_status = "postgres"
            app.state.engine = engine
        except Exception:
            logger.exception("database_initialisation_failed_using_in_memory_backends")
            app.state.database_status = "degraded_in_memory"

    retrieval = RetrievalService(
        repository=repository,
        embeddings=embeddings,
        reranker=SimpleReranker(),
        retrieval_limit=settings.retrieval_limit,
        rerank_limit=settings.rerank_limit,
    )
    tools = build_default_registry(
        settings.cache_ttl_seconds, max_cache_size=settings.cache_max_size
    )
    workflow_engine = WorkflowEngine(
        planner=PlannerAgent(graph),
        research=ResearchAgent(retrieval, graph, settings.graph_depth),
        analysis=AnalysisAgent(tools),
        synthesis=SynthesisAgent(),
        verifier=VerifierAgent(Evaluator()),
        store=store,
    )
    app.state.workflow_engine = workflow_engine
    app.state.workflow_store = store
    yield
    if engine is not None:
        await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="BioAgentX",
        version=__version__,
        description="Agentic biomedical and clinical data analysis platform with tool-backed workflows.",
        lifespan=lifespan,
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        InMemoryRateLimitMiddleware,
        limit_per_minute=settings.rate_limit_per_minute,
        burst=settings.rate_limit_burst,
    )
    app.include_router(router)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "trace_id": getattr(request.state, "trace_id", None),
                "details": exc.errors(),
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled_request_error", extra={"trace_id": getattr(request.state, "trace_id", None)}
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "trace_id": getattr(request.state, "trace_id", None),
                "message": "BioAgentX could not complete the workflow safely.",
            },
        )

    return app


app = create_app()
