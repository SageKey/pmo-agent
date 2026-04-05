"""HTTP middleware.

- ShareKeyMiddleware:   when SHARED_PASSWORD is set, every request must carry
  a matching `X-Share-Key` header. A small allowlist (health, OpenAPI docs)
  stays open so the frontend can bootstrap before prompting for the key.
"""

from typing import Set

from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


# Paths that never require the share key (needed for the frontend to boot
# and for platforms like Railway/Render to health-check).
PUBLIC_PATHS: Set[str] = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}
PUBLIC_PATH_PREFIXES = (
    "/docs/",
    "/api/v1/meta/",  # health + version check so the login prompt knows auth is enabled
)


class ShareKeyMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, shared_password: str):
        super().__init__(app)
        self._password = shared_password

    async def dispatch(self, request: Request, call_next) -> Response:
        # CORS preflight: let it through so browsers don't see a 401 on OPTIONS
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        if path in PUBLIC_PATHS or any(
            path.startswith(p) for p in PUBLIC_PATH_PREFIXES
        ):
            return await call_next(request)

        provided = request.headers.get("x-share-key", "")
        if provided != self._password:
            return JSONResponse(
                status_code=401,
                content={
                    "detail": (
                        "Missing or invalid X-Share-Key header. This instance "
                        "is gated by a shared password."
                    )
                },
            )
        return await call_next(request)
