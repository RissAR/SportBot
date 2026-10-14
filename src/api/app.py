"""FastAPI backend with CORS and TMA Anti-Cache headers."""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings

app = FastAPI(title="SportBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AntiCacheMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing anti-cache headers on /app* endpoints for Telegram Mini App."""

    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        if request.url.path.startswith("/app"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        return response


app.add_middleware(AntiCacheMiddleware)


@app.get("/health")
async def health():
    """Health check endpoint for container monitoring."""
    return {"status": "ok"}


@app.get("/app/version")
async def app_version():
    """TMA metadata and cycle configuration."""
    return {
        "version": "1.0.0",
        "cycle_days": settings.CYCLE_DAYS,
    }
