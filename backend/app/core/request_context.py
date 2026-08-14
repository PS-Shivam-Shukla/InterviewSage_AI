"""
Request Context Subsystem for InterviewSage AI.
Manages thread-local / async context variables for request correlation IDs, user IDs, and interview IDs.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Context variables for correlation and request tracing
_request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
_user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")
_interview_id_ctx: ContextVar[str] = ContextVar("interview_id", default="")


def set_request_context(
    request_id: str | None = None,
    user_id: str | None = None,
    interview_id: str | None = None,
) -> None:
    """Set request context variables for the current thread/task execution scope."""
    if request_id is not None:
        _request_id_ctx.set(request_id)
    if user_id is not None:
        _user_id_ctx.set(user_id)
    if interview_id is not None:
        _interview_id_ctx.set(interview_id)


def get_request_id() -> str:
    """Retrieve current request correlation ID."""
    return _request_id_ctx.get()


def get_user_id() -> str:
    """Retrieve current request user ID."""
    return _user_id_ctx.get()


def get_interview_id() -> str:
    """Retrieve current request interview ID."""
    return _interview_id_ctx.get()


def clear_request_context() -> None:
    """Clear all request context variables."""
    _request_id_ctx.set("")
    _user_id_ctx.set("")
    _interview_id_ctx.set("")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware that extracts or generates correlation X-Request-ID,
    populates request context variables, and attaches X-Request-ID header to responses.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Extract X-Request-ID header or generate a new UUID
        request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"

        # Extract user_id or interview_id if present in headers or query
        user_id = request.headers.get("X-User-ID", "")
        interview_id = request.headers.get("X-Interview-ID", "")

        # Set context variables
        set_request_context(request_id=request_id, user_id=user_id, interview_id=interview_id)

        # Process request
        response = await call_next(request)

        # Inject X-Request-ID into response headers
        response.headers["X-Request-ID"] = request_id

        return response
