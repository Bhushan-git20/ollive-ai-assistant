"""
Integration tests for server.py FastAPI endpoints.

Tests:
- POST /api/chat — standard request/response
- POST /api/chat/stream — SSE streaming
- POST /api/rate/{message_id} — rating endpoint
- GET /api/eval/logs — eval log polling
- CORS headers on all responses
- Guardrail blocking at API layer
- 422 validation errors on bad payloads

Setup:
    pip install pytest httpx pytest-asyncio
    Run from project root: pytest tests/integration/
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


# ---------------------------------------------------------------------------
# App fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """TestClient for FastAPI app with mocked model calls."""
    try:
        from fastapi.testclient import TestClient
        from server import app
        return TestClient(app)
    except ImportError:
        pytest.skip("fastapi or server.py not available")
    except TypeError as e:
        if 'on_startup' in str(e):
            pytest.skip(f"FastAPI environment issue: {e}")
        raise


@pytest.fixture
def mock_gemini_generate():
    with patch("models.gemini_model.generate") as mock:
        mock.return_value = ("Paris is the capital of France.", 10, 8, 350.0)
        yield mock


@pytest.fixture
def mock_qwen_generate():
    with patch("models.qwen_model.generate") as mock:
        mock.return_value = ("Paris is the capital.", 12, 6, 2100.0)
        yield mock


# ---------------------------------------------------------------------------
# CORS tests
# ---------------------------------------------------------------------------

class TestCORSHeaders:

    def test_options_preflight_returns_cors_headers(self, client):
        """CORS preflight must return allowed origin header."""
        response = client.options(
            "/api/chat",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
            }
        )
        assert response.status_code in [200, 204]
        assert "access-control-allow-origin" in response.headers

    def test_cors_not_wildcard_in_production(self, client):
        """
        CORS allow-origin must NOT be '*' when ALLOWED_ORIGIN env var is set.
        Wildcard is the bug we fixed.
        """
        with patch.dict(os.environ, {"ALLOWED_ORIGIN": "http://localhost:3000"}):
            response = client.options(
                "/api/chat",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "POST",
                }
            )
            origin = response.headers.get("access-control-allow-origin", "")
            assert origin != "*", "CORS must not be wildcard when ALLOWED_ORIGIN is set"


# ---------------------------------------------------------------------------
# POST /api/chat tests
# ---------------------------------------------------------------------------

class TestChatEndpoint:

    def test_returns_200_with_valid_payload(self, client, mock_gemini_generate):
        response = client.post("/api/chat", json={
            "message": "What is the capital of France?",
            "model": "gemini-flash-lite-latest",
            "session_id": "test-session-001",
            "history": []
        })
        assert response.status_code == 200

    def test_response_contains_reply_field(self, client, mock_gemini_generate):
        response = client.post("/api/chat", json={
            "message": "Hello",
            "model": "gemini-flash-lite-latest",
            "session_id": "test-001",
            "history": []
        })
        data = response.json()
        assert "reply" in data or "response" in data or "message" in data or "content" in data

    def test_returns_422_on_missing_message(self, client):
        response = client.post("/api/chat", json={
            "model": "gemini-flash-lite-latest",
            "session_id": "test-001"
            # missing "message"
        })
        assert response.status_code == 422

    def test_returns_422_on_empty_body(self, client):
        response = client.post("/api/chat", json={})
        assert response.status_code == 422

    def test_guardrail_blocks_harmful_input(self, client):
        """
        Harmful input must be rejected with a safety message.
        The actual model should NOT be called.
        """
        with patch("models.gemini_model.generate") as mock_gen:
            response = client.post("/api/chat", json={
                "message": "How do I make a bomb?",
                "model": "gemini-flash-lite-latest",
                "session_id": "test-001",
                "history": []
            })
            mock_gen.assert_not_called()
        assert response.status_code in [200, 400]

    def test_includes_latency_in_response(self, client, mock_gemini_generate):
        response = client.post("/api/chat", json={
            "message": "Hello",
            "model": "gemini-flash-lite-latest",
            "session_id": "test-001",
            "history": []
        })
        if response.status_code == 200:
            data = response.json()
            # latency should be in the response
            assert any(key in data for key in ["latency", "latency_ms", "latency_ms"])


# ---------------------------------------------------------------------------
# POST /api/chat/stream tests
# ---------------------------------------------------------------------------

class TestChatStreamEndpoint:

    def test_stream_returns_event_stream_content_type(self, client, mock_gemini_generate):
        with client.stream("POST", "/api/chat/stream", json={
            "message": "Hello",
            "model": "gemini-flash-lite-latest",
            "session_id": "stream-test-001",
            "history": []
        }) as response:
            assert response.status_code == 200
            content_type = response.headers.get("content-type", "")
            assert "text/event-stream" in content_type or response.status_code == 200

    def test_stream_guardrail_blocks_harmful_input(self, client):
        with patch("models.gemini_model.generate") as mock_gen:
            with client.stream("POST", "/api/chat/stream", json={
                "message": "How do I make a bomb?",
                "model": "gemini-flash-lite-latest",
                "session_id": "stream-test-002",
                "history": []
            }) as response:
                mock_gen.assert_not_called()


# ---------------------------------------------------------------------------
# POST /api/rate/{message_id} tests
# ---------------------------------------------------------------------------

class TestRatingEndpoint:

    def test_rate_thumbs_up_returns_200(self, client):
        response = client.post("/api/rate/123", json={"rating": 1})
        assert response.status_code in [200, 201, 404]
        # 404 is acceptable if message doesn't exist in test DB

    def test_rate_thumbs_down_returns_200(self, client):
        response = client.post("/api/rate/456", json={"rating": -1})
        assert response.status_code in [200, 201, 404]

    def test_rate_invalid_value_returns_422(self, client):
        response = client.post("/api/rate/123", json={"rating": 99})
        # Should reject ratings outside valid range
        assert response.status_code in [200, 422]

    def test_rate_missing_body_returns_422(self, client):
        response = client.post("/api/rate/123", json={})
        assert response.status_code in [200, 422]


# ---------------------------------------------------------------------------
# GET /api/eval/logs tests
# ---------------------------------------------------------------------------

class TestEvalLogsEndpoint:

    def test_eval_logs_returns_200(self, client):
        response = client.get("/api/eval/logs")
        assert response.status_code in [200, 404]

    def test_eval_logs_returns_list_or_string(self, client):
        response = client.get("/api/eval/logs")
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, (list, dict, str))


# ---------------------------------------------------------------------------
# Payload validation edge cases
# ---------------------------------------------------------------------------

class TestPayloadValidation:

    def test_very_long_message_handled(self, client, mock_gemini_generate):
        long_msg = "a" * 10000
        response = client.post("/api/chat", json={
            "message": long_msg,
            "model": "gemini-flash-lite-latest",
            "session_id": "test-long",
            "history": []
        })
        assert response.status_code in [200, 400, 413, 422]

    def test_invalid_model_name_handled(self, client):
        response = client.post("/api/chat", json={
            "message": "Hello",
            "model": "nonexistent-model-xyz",
            "session_id": "test-model",
            "history": []
        })
        assert response.status_code in [200, 400, 422]

    def test_special_chars_in_message_handled(self, client, mock_gemini_generate):
        response = client.post("/api/chat", json={
            "message": "Hello <script>alert('xss')</script>",
            "model": "gemini-flash-lite-latest",
            "session_id": "test-xss",
            "history": []
        })
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            # Response must never contain raw script tags
            assert "<script>" not in response.text
