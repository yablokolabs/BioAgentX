from fastapi.testclient import TestClient

from bioagentx.core.config import get_settings
from bioagentx.main import create_app


def test_api_query_workflow_and_feedback(monkeypatch) -> None:
    monkeypatch.setenv("USE_DATABASE", "false")
    get_settings.cache_clear()
    try:
        with TestClient(create_app()) as client:
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
    finally:
        get_settings.cache_clear()
