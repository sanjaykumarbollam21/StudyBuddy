import time
import uuid
import json
import logging
from typing import Callable, Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Configure structured JSON logger
logger = logging.getLogger("study_buddy.telemetry")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# Sensitive fields that MUST NEVER be logged
REDACTED_KEYS = {
    "password",
    "token",
    "access_token",
    "authorization",
    "secret",
    "file_content",
    "content_bytes",
    "raw_text",
}


def sanitize_data(data: dict) -> dict:
    """Recursively scrub sensitive keys from log dictionaries."""
    sanitized = {}
    for k, v in data.items():
        if k.lower() in REDACTED_KEYS:
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = sanitize_data(v)
        elif isinstance(v, list) and v and isinstance(v[0], dict):
            sanitized[k] = [sanitize_data(item) for item in v]
        else:
            sanitized[k] = v
    return sanitized


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """
    Production telemetry middleware that logs structured metadata for every request:
    request_id, duration_ms, status_code, endpoint, user_id (if present),
    without logging sensitive documents or auth tokens.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Extract user if available in header (sanitized)
        auth_header = request.headers.get("Authorization")
        has_auth = bool(auth_header and auth_header.startswith("Bearer "))

        response: Optional[Response] = None
        error_category = None

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as exc:
            error_category = exc.__class__.__name__
            status_code = 500
            raise exc
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            log_payload = {
                "telemetry": "request_summary",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "authenticated": has_auth,
                "error_category": error_category,
            }
            logger.info(json.dumps(log_payload))

        if response is not None:
            response.headers["X-Request-ID"] = request_id
        return response
