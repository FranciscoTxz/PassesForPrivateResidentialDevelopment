import asyncio
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from commons.exceptions_handler import register_exception_handlers
from commons import exceptions_handler as exception_module


def _build_request(path: str = "/test") -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_register_exception_handlers_registers_expected_handlers():
    app = FastAPI()

    register_exception_handlers(app)

    assert RequestValidationError in app.exception_handlers
    assert StarletteHTTPException in app.exception_handlers
    assert Exception in app.exception_handlers


def test_validation_handler_returns_400_with_errors(monkeypatch):
    app = FastAPI()
    mock_logger = MagicMock()
    monkeypatch.setattr(exception_module, "_LOG", mock_logger)
    register_exception_handlers(app)

    handler = app.exception_handlers[RequestValidationError]
    request = _build_request("/validation")
    exc = RequestValidationError(
        [{"loc": ("body", "email"), "msg": "Field required", "type": "missing"}]
    )

    response = asyncio.run(handler(request, exc))

    assert response.status_code == 400
    assert response.body == (
        b'{"message":"Validation error","errors":[{"loc":["body","email"],"msg":"Field required","type":"missing"}]}'
    )
    mock_logger.warning.assert_called_once()


def test_http_exception_handler_returns_original_status_for_4xx(monkeypatch):
    app = FastAPI()
    mock_logger = MagicMock()
    monkeypatch.setattr(exception_module, "_LOG", mock_logger)
    register_exception_handlers(app)

    handler = app.exception_handlers[StarletteHTTPException]
    request = _build_request("/not-found")
    exc = StarletteHTTPException(status_code=404, detail="Not found")

    response = asyncio.run(handler(request, exc))

    assert response.status_code == 404
    assert response.body == b'{"message":"Not found"}'
    mock_logger.warning.assert_called_once()
    mock_logger.error.assert_not_called()


def test_http_exception_handler_returns_500_for_5xx(monkeypatch):
    app = FastAPI()
    mock_logger = MagicMock()
    monkeypatch.setattr(exception_module, "_LOG", mock_logger)
    monkeypatch.setattr(exception_module.traceback, "format_exc", lambda: "fake-trace")
    register_exception_handlers(app)

    handler = app.exception_handlers[StarletteHTTPException]
    request = _build_request("/server-error")
    exc = StarletteHTTPException(status_code=500, detail="Internal detail")

    response = asyncio.run(handler(request, exc))

    assert response.status_code == 500
    assert response.body == b'{"message":"Internal server error"}'
    mock_logger.error.assert_called_once()
    mock_logger.warning.assert_not_called()


def test_general_handler_returns_500(monkeypatch):
    app = FastAPI()
    mock_logger = MagicMock()
    monkeypatch.setattr(exception_module, "_LOG", mock_logger)
    monkeypatch.setattr(
        exception_module.traceback, "format_exc", lambda: "general-trace"
    )
    register_exception_handlers(app)

    handler = app.exception_handlers[Exception]
    request = _build_request("/unexpected")
    exc = RuntimeError("boom")

    response = asyncio.run(handler(request, exc))

    assert response.status_code == 500
    assert response.body == b'{"message":"Internal server error"}'
    mock_logger.error.assert_called_once()
