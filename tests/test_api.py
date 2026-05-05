import pytest
from fastapi.testclient import TestClient

from bioagentx.core.config import get_settings
from bioagentx.main import create_app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("USE_DATABASE", "false")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as c:
            yield c
    finally:
        get_settings.cache_clear()


def test_api_query_workflow_and_feedback(client) -> None:
    response = client.post(
        "/query",
        json={"query": "Explain BRCA1 breast cancer pathway evidence and trial context."},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"]
    assert payload["sources"]
    assert payload["verification"]["tool_coverage"] == 1.0

    workflow = client.get(f"/workflow/{payload['workflow_id']}")
    assert workflow.status_code == 200
    assert workflow.json()["steps"]

    feedback = client.post(
        "/feedback",
        json={"workflow_id": payload["workflow_id"], "label": "helpful", "comment": "solid"},
    )
    assert feedback.status_code == 200
    assert feedback.json()["status"] == "recorded"


def test_health_endpoint(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "BioAgentX"
    assert "version" in data


def test_metrics_endpoint(client) -> None:
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"bioagentx_" in response.content


def test_query_validation_too_short(client) -> None:
    response = client.post("/query", json={"query": "short"})
    assert response.status_code == 422


def test_workflow_not_found(client) -> None:
    response = client.get("/workflow/nonexistent-id")
    assert response.status_code == 404


def test_feedback_not_found(client) -> None:
    response = client.post(
        "/feedback",
        json={"workflow_id": "nonexistent-id", "label": "helpful"},
    )
    assert response.status_code == 404
