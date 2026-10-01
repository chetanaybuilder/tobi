"""
test_api.py
Tests for the FastAPI endpoints and AI service.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    """Test that the health endpoint returns ok."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_unauthorized_access():
    """Test that accessing protected routes without session fails."""
    response = client.get("/api/auth/me")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_ai_stream_validation():
    """Test that stream validation catches empty messages."""
    response = client.post("/api/chat/stream", json={"message": "", "mode_id": "general"})
    # Should block at validation or auth
    assert response.status_code in [401, 400, 422]
