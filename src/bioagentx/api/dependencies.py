from fastapi import Request

from bioagentx.orchestration.store import WorkflowStore
from bioagentx.orchestration.workflow import WorkflowEngine


def get_workflow_engine(request: Request) -> WorkflowEngine:
    return request.app.state.workflow_engine


def get_workflow_store(request: Request) -> WorkflowStore:
    return request.app.state.workflow_store
