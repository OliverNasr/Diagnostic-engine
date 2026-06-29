"""
Diagnostic Engine — FastAPI application entry point.

Startup sequence
----------------
1. Configure logging.
2. Instantiate :class:`~app.services.DiagnosticService`.
3. Call ``load_dataset()`` — reads CSV into memory once.
4. Attach the service to ``app.state`` so every route can retrieve it
   via dependency injection.

The application is intentionally assembled here (not in a factory
function) so that ``uvicorn app.main:app`` works without extra wiring.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.config import settings
from app.services.diagnostic_service import DiagnosticService
from app.utils.logger import configure_logging, get_logger

# ---------------------------------------------------------------------------
# Logging — configured before anything else so startup messages are captured
# ---------------------------------------------------------------------------
configure_logging()
logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — dataset is loaded here so it happens exactly once
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI lifespan context manager.

    *Startup*: load the DTC dataset into the ``DiagnosticService`` and
    store the instance on ``app.state``.

    *Shutdown*: log a goodbye message (no teardown needed for in-memory
    data).
    """
    logger.info("=== Diagnostic Engine starting up ===")

    service = DiagnosticService(dataset_path=settings.DATASET_PATH)
    try:
        service.load_dataset()
    except (FileNotFoundError, ValueError) as exc:
        logger.critical("Failed to load dataset: %s", exc)
        raise SystemExit(1) from exc

    application.state.diagnostic_service = service
    logger.info("=== Diagnostic Engine ready — dataset loaded. ===")

    yield  # — application is running —

    logger.info("=== Diagnostic Engine shutting down. ===")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.SERVICE_VERSION,
    description=settings.SERVICE_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS — permissive defaults; tighten in production via env vars
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler — ensures unexpected errors return JSON
# ---------------------------------------------------------------------------


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"error": "An internal server error occurred."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(router)
