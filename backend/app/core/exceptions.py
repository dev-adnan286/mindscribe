"""Domain exceptions and RFC 7807 (application/problem+json) handlers."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

PROBLEM_BASE = "https://mindscribe.dev/problems"
HTTP_422 = 422


class AppError(Exception):
    status_code: int = status.HTTP_400_BAD_REQUEST
    title: str = "Bad Request"
    problem_type: str = "bad-request"

    def __init__(self, detail: str | None = None, **extra: Any) -> None:
        self.detail = detail or self.title
        self.extra = extra
        super().__init__(self.detail)

    def to_problem(self, instance: str | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {
            "type": f"{PROBLEM_BASE}/{self.problem_type}",
            "title": self.title,
            "status": self.status_code,
            "detail": self.detail,
        }
        if instance:
            body["instance"] = instance
        body.update(self.extra)
        return body


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    title = "Not Found"
    problem_type = "not-found"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    title = "Unauthorized"
    problem_type = "unauthorized"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    title = "Forbidden"
    problem_type = "forbidden"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    title = "Conflict"
    problem_type = "conflict"


class ValidationFailedError(AppError):
    status_code = HTTP_422
    title = "Validation Failed"
    problem_type = "validation-failed"


class RateLimitedError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    title = "Too Many Requests"
    problem_type = "rate-limited"


class ServiceUnavailableError(AppError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    title = "Service Unavailable"
    problem_type = "service-unavailable"


def _problem_response(
    request: Request, body: dict[str, Any], status_code: int, headers: dict[str, str] | None = None
) -> JSONResponse:
    body.setdefault("instance", str(request.url.path))
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        body["request_id"] = request_id
    return JSONResponse(
        status_code=status_code,
        content=body,
        media_type="application/problem+json",
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        headers: dict[str, str] = {}
        if isinstance(exc, UnauthorizedError):
            headers["WWW-Authenticate"] = "Bearer"
        if isinstance(exc, RateLimitedError) and "retry_after" in exc.extra:
            headers["Retry-After"] = str(exc.extra["retry_after"])
        return _problem_response(request, exc.to_problem(), exc.status_code, headers or None)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {
                "loc": [str(part) for part in err.get("loc", [])],
                "msg": err.get("msg"),
                "type": err.get("type"),
            }
            for err in exc.errors()
        ]
        body = {
            "type": f"{PROBLEM_BASE}/validation-failed",
            "title": "Validation Failed",
            "status": HTTP_422,
            "detail": "Request validation failed",
            "errors": errors,
        }
        return _problem_response(request, body, HTTP_422)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        body = {
            "type": f"{PROBLEM_BASE}/http-error",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": exc.detail if isinstance(exc.detail, str) else "HTTP error",
        }
        headers = dict(exc.headers) if exc.headers else None
        return _problem_response(request, body, exc.status_code, headers)

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        body = {
            "type": f"{PROBLEM_BASE}/internal-error",
            "title": "Internal Server Error",
            "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "detail": "An unexpected error occurred",
        }
        return _problem_response(request, body, status.HTTP_500_INTERNAL_SERVER_ERROR)
