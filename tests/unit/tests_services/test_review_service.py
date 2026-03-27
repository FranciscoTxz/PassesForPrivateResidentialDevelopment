import json
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

import services.review_service as review_service_module
from services.review_service import ReviewService

# ─── Helpers ──────────────────────────────────────────────────────────────────


def make_mock_completion(approved: bool, reason: str):
    """Builds a mock object mimicking openai's ChatCompletion response."""
    content = json.dumps({"approved": approved, "reason": reason})
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def patch_openai_client(monkeypatch, completion):
    """Replaces the module-level _openai_client with a mock."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = completion
    monkeypatch.setattr(review_service_module, "_openai_client", mock_client)
    return mock_client


# ─── review_pass ──────────────────────────────────────────────────────────────


class TestReviewPass:
    # ── credenciales ausentes ──────────────────────────────────────────────────

    def test_raises_423_when_no_api_endpoint(self, monkeypatch):
        monkeypatch.setattr(review_service_module, "OPENAI_API_ENDPOINT", "")
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "some-key")

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("I need access for a week")

        assert exc_info.value.status_code == 423

    def test_raises_423_when_no_api_key(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "")

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("I need access for a week")

        assert exc_info.value.status_code == 423

    def test_raises_423_when_both_credentials_missing(self, monkeypatch):
        monkeypatch.setattr(review_service_module, "OPENAI_API_ENDPOINT", "")
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "")

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("I need access for a week")

        assert exc_info.value.status_code == 423

    def test_423_detail_message(self, monkeypatch):
        monkeypatch.setattr(review_service_module, "OPENAI_API_ENDPOINT", "")
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "")

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("request")

        assert "unavailable" in exc_info.value.detail.lower()

    # ── respuesta aprobada ────────────────────────────────────────────────────

    def test_returns_approved_review_schema(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        completion = make_mock_completion(
            approved=True, reason="Multi-day construction work with full details."
        )
        patch_openai_client(monkeypatch, completion)

        result = ReviewService.review_pass("Construction crew needs 5-day access.")

        assert result.approved is True
        assert "construction" in result.reason.lower()

    def test_returns_denied_review_schema(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        completion = make_mock_completion(
            approved=False, reason="Vague purpose, no contact info provided."
        )
        patch_openai_client(monkeypatch, completion)

        result = ReviewService.review_pass("need access")

        assert result.approved is False
        assert result.reason != ""

    # ── llamada al cliente OpenAI ─────────────────────────────────────────────

    def test_openai_client_called_with_correct_model(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        completion = make_mock_completion(approved=True, reason="Looks good.")
        mock_client = patch_openai_client(monkeypatch, completion)

        ReviewService.review_pass("Some valid request")

        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["model"] == review_service_module.MODEL

    def test_openai_client_receives_user_message(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        completion = make_mock_completion(approved=True, reason="Looks good.")
        mock_client = patch_openai_client(monkeypatch, completion)

        ReviewService.review_pass("Plumber needs 3-day access for pipe repair.")

        _, kwargs = mock_client.chat.completions.create.call_args
        messages = kwargs["messages"]
        user_turn = next(m for m in messages if m["role"] == "user")
        assert "Plumber needs 3-day access for pipe repair." in str(
            user_turn["content"]
        )

    def test_openai_client_prompt_includes_system_role(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        completion = make_mock_completion(approved=False, reason="Missing details.")
        mock_client = patch_openai_client(monkeypatch, completion)

        ReviewService.review_pass("Some request")

        _, kwargs = mock_client.chat.completions.create.call_args
        roles = [m["role"] for m in kwargs["messages"]]
        assert "system" in roles

    def test_stream_is_false(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        completion = make_mock_completion(approved=True, reason="Fine. is very cooool")
        mock_client = patch_openai_client(monkeypatch, completion)

        ReviewService.review_pass("Valid request")

        _, kwargs = mock_client.chat.completions.create.call_args
        assert kwargs["stream"] is False

    # ── manejo de errores ─────────────────────────────────────────────────────

    def test_raises_500_on_openai_exception(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Connection error")
        monkeypatch.setattr(review_service_module, "_openai_client", mock_client)

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("Some request")

        assert exc_info.value.status_code == 500

    def test_raises_500_on_invalid_json_response(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        message = MagicMock()
        message.content = "this is not valid json {"
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = completion
        monkeypatch.setattr(review_service_module, "_openai_client", mock_client)

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("Some request")

        assert exc_info.value.status_code == 500

    def test_raises_500_on_schema_validation_failure(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        # JSON válido pero con campos incorrectos para ReviewSchema
        message = MagicMock()
        message.content = json.dumps({"unexpected_field": 123})
        choice = MagicMock()
        choice.message = message
        completion = MagicMock()
        completion.choices = [choice]

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = completion
        monkeypatch.setattr(review_service_module, "_openai_client", mock_client)

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("Some request")

        assert exc_info.value.status_code == 500

    def test_500_detail_message(self, monkeypatch):
        monkeypatch.setattr(
            review_service_module, "OPENAI_API_ENDPOINT", "https://fake.endpoint"
        )
        monkeypatch.setattr(review_service_module, "OPENAI_API_KEY", "secret")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Timeout")
        monkeypatch.setattr(review_service_module, "_openai_client", mock_client)

        with pytest.raises(HTTPException) as exc_info:
            ReviewService.review_pass("Some request")

        assert "wrong" in exc_info.value.detail.lower()
