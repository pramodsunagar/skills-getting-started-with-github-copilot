"""Pytest configuration and shared fixtures"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Provide a FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def sample_activity_data(client):
    """Get a copy of activities from the API for reference"""
    response = client.get("/activities")
    return response.json()
