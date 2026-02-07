from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _request_id(request: Request) -> Optional[str]:
    return getattr(getattr(request, "state", None), "request_id", None)


def _error_payload(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]],
    request_id: Optional[str],
) -> Dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
            "timestamp": _timestamp(),
        }
    }


def _map_status_to_code(status_code: int) -> str:
    return {
        400: "INVALID_REQUEST",
        401: "AUTHENTICATION_FAILED",
        403: "AUTHORIZATION_FAILED",
        404: "RESOURCE_NOT_FOUND",
        408: "TIMEOUT",
        422: "INVALID_REQUEST",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        503: "SERVICE_UNAVAILABLE",
    }.get(status_code, "INTERNAL_ERROR")


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    code = _map_status_to_code(exc.status_code)
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message", "Request failed")
        details = exc.detail.get("details", exc.detail)
    else:
        message = exc.detail if isinstance(exc.detail, str) else "Request failed"
        details = None
    payload = _error_payload(code, message, details, _request_id(request))
    return JSONResponse(status_code=exc.status_code, content=payload)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    payload = _error_payload(
        "INVALID_REQUEST",
        "Validation error",
        {"errors": exc.errors()},
        _request_id(request),
    )
    return JSONResponse(status_code=422, content=payload)


async def unhandled_exception_handler(request: Request, exc: Exception):
    payload = _error_payload(
        "INTERNAL_ERROR",
        "Unexpected error",
        None,
        _request_id(request),
    )
    return JSONResponse(status_code=500, content=payload)
