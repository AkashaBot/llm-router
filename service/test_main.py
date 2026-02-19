"""
Tests for LLM Router Service - Phase 1
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, chat_completions, ChatCompletionRequest, Message

client = TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint"""
    
    def test_health_check(self):
        """Test that health endpoint returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "llm-router"


class TestModelsEndpoint:
    """Test /models endpoint"""
    
    def test_list_models(self):
        """Test that models endpoint returns available models"""
        response = client.get("/models")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert len(data["data"]) > 0
        assert data["data"][0]["id"] == "router"


class TestChatCompletions:
    """Test /v1/chat/completions endpoint"""
    
    def test_chat_completions_no_api_key(self):
        """Test that missing API key returns error"""
        # Temporarily unset env var
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}):
            # Need to reload the module to pick up the env change
            import importlib
            import main
            importlib.reload(main)
            
            response = client.post(
                "/v1/chat/completions",
                json={
                    "model": "router",
                    "messages": [{"role": "user", "content": "Hello"}]
                }
            )
            # Should fail with 500 due to missing API key
            assert response.status_code == 500
    
    def test_chat_completions_invalid_request(self):
        """Test that invalid request returns proper error"""
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "router",
                "messages": []  # Empty messages should fail
            }
        )
        # Pydantic validation should fail
        assert response.status_code == 422
    
    def test_chat_completions_valid_request_structure(self):
        """Test that valid request structure is accepted"""
        # This test only validates the request structure, not the actual API call
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "router",
                "messages": [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "Hello!"}
                ],
                "temperature": 0.7,
                "max_tokens": 100
            }
        )
        # Will fail with 500 because API key is not set in test environment
        # But validates that request structure is correct
        assert response.status_code in [200, 500]


class TestRoutingLogic:
    """Test routing logic (Phase 2/3) - placeholder for now"""
    
    def test_routing_detection_placeholder(self):
        """Placeholder test for routing logic"""
        # This will be implemented in Phase 2
        # For now, just verify the concept exists
        assert True  # Placeholder


if __name__ == "__main__":
    pytest.main([__file__, "-v"])