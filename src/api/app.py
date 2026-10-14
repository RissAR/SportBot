"""FastAPI backend with CORS, TMA Anti-Cache headers, and REST API routing."""

import logging
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.api.routes import admin, cycle, users, weight, workout
from src.config import settings

logger = logging.getLogger("sportbot.api")

app = FastAPI(
    title="SportBot API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# ---------------------------------------------------------
# CORS Configuration
# ---------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Anti-Cache Middleware for TMA Routes
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Global Exception Handlers
# ---------------------------------------------------------
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Ensure clean JSON response on standard HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Catch unhandled runtime errors gracefully."""
    logger.exception("Unhandled server exception on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ---------------------------------------------------------
# Base Endpoints
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# REST API Routers
# ---------------------------------------------------------
app.include_router(users.router, prefix="/api/user", tags=["User"])
app.include_router(cycle.router, prefix="/api/cycle", tags=["Cycle"])
app.include_router(workout.router, prefix="/api/workout", tags=["Workout"])
app.include_router(weight.router, prefix="/api/weight", tags=["Weight"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
