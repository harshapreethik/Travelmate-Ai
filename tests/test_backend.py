"""
TravelMate AI — Backend API Test Suite
Tests health checks, routing, input validations, error handlers, and HTTP responses.
"""

import json
import pytest
from app import app


@pytest.fixture
def client():
    """Configures Flask application test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Verifies home dashboard HTML route returns 200 OK."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"TravelMate AI" in response.data


def test_health_check_endpoint(client):
    """Verifies system health check endpoint payload."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["app_name"] == "TravelMate AI"
    assert "supported_languages" in data


def test_chat_endpoint_missing_payload(client):
    """Verifies chat endpoint returns 400 when message is empty."""
    response = client.post("/api/chat", json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["status"] == "error"
    assert "Message parameter is required" in data["message"]


def test_recommendations_endpoint_structure(client):
    """Verifies recommendations endpoint returns valid structured JSON payload."""
    payload = {
        "destination": "Hyderabad",
        "interests": ["History", "Food"],
        "budget_level": "Budget",
        "traveller_type": "Solo",
        "lang": "en"
    }
    response = client.post("/api/recommendations", json=payload)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "recommendations" in data["data"]
    assert "ai_insights" in data["data"]


def test_404_error_handler(client):
    """Verifies custom 404 error handler for invalid endpoints."""
    response = client.get("/api/nonexistent_endpoint")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["status"] == "error"
    assert "not found" in data["message"]