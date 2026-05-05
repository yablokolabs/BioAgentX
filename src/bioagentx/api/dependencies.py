from fastapi import Request

from bioagentx.orchestration.store import WorkflowStore
from bioagentx.orchestration.workflow import WorkflowEngine


def get_workflow_engine(request: Request) -> WorkflowEngine:
    """FastAPI dependency — returns the application-level workflow engine."""
    return request.app.state.workflow_engine


def get_workflow_store(request: Request) -> WorkflowStore:
    """FastAPI dependency — returns the active workflow store."""
    return request.app.state.workflow_store
