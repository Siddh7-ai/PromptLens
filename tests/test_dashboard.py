import pytest
from fastapi.testclient import TestClient

from src.proxy.server import app
from src.proxy.stats import get_global_metrics

client = TestClient(app)
metrics = get_global_metrics()


def test_dashboard_endpoint_html():
    """Test /dashboard returns 200 OK with HTML content."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "PromptLens" in response.text
    assert "Live Savings Dashboard" in response.text


def test_api_stats_endpoint_json():
    """Test /api/stats returns 200 OK with summary json structure."""
    metrics.reset()
    metrics.record_request(
        path="/v1/messages",
        method="POST",
        baseline_tokens=1000,
        compressed_tokens=250,
        retrieval_id="test_hash_1"
    )

    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()

    assert data["total_requests"] == 1
    assert data["total_baseline_tokens"] == 1000
    assert data["total_compressed_tokens"] == 250
    assert data["total_tokens_saved"] == 750
    assert data["overall_savings_pct"] == 75.0
    assert data["estimated_usd_saved"] > 0
    assert len(data["recent_requests"]) == 1
    assert data["recent_requests"][0]["retrieval_id"] == "test_hash_1"
