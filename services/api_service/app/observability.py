import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        for key in (
            "request_id",
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client",
            "component",
            "job_id",
        ):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload)


class TextFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        request_id = getattr(record, "request_id", None)
        if request_id:
            return f"{base} request_id={request_id}"
        return base


def configure_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    level = os.getenv("LOG_LEVEL", "INFO").upper()
    formatter_choice = os.getenv("LOG_FORMAT", "json").lower()
    handler = logging.StreamHandler(sys.stdout)
    if formatter_choice == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(TextFormatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    handler.addFilter(RequestIdFilter())

    logger.setLevel(level)
    logger.addHandler(handler)
    logger.propagate = False
    return logger


@dataclass
class MetricsCollector:
    lock: Lock = field(default_factory=Lock)
    request_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    status_counts: Dict[str, int] = field(default_factory=dict)
    path_counts: Dict[str, int] = field(default_factory=dict)

    def record(self, method: str, path: str, status_code: int, duration_ms: float) -> None:
        key = f"{method} {path}"
        with self.lock:
            self.request_count += 1
            self.total_latency_ms += duration_ms
            if status_code >= 400:
                self.error_count += 1
            self.status_counts[str(status_code)] = self.status_counts.get(str(status_code), 0) + 1
            self.path_counts[key] = self.path_counts.get(key, 0) + 1

    def snapshot(self) -> Dict[str, object]:
        with self.lock:
            avg_latency = (
                self.total_latency_ms / self.request_count
                if self.request_count
                else 0.0
            )
            return {
                "requests_total": self.request_count,
                "errors_total": self.error_count,
                "avg_latency_ms": round(avg_latency, 2),
                "status_counts": dict(self.status_counts),
                "path_counts": dict(self.path_counts),
            }


metrics = MetricsCollector()


class RequestIdMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger_name: str = "optimisation.api"):
        super().__init__(app)
        self.logger = configure_logger(logger_name)

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or uuid.uuid4().hex
        token = request_id_ctx.set(request_id)
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            metrics.record(request.method, request.url.path, 500, duration_ms)
            self.logger.exception(
                "request.error",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": 500,
                    "duration_ms": round(duration_ms, 2),
                    "client": request.client.host if request.client else None,
                },
            )
            request_id_ctx.reset(token)
            raise

        duration_ms = (time.perf_counter() - start) * 1000
        metrics.record(request.method, request.url.path, response.status_code, duration_ms)
        response.headers["X-Request-Id"] = request_id
        self.logger.info(
            "request.complete",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client": request.client.host if request.client else None,
            },
        )
        request_id_ctx.reset(token)
        return response
