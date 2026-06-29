"""
Route definitions for the Diagnostic Engine API.

All routes are registered on a single ``APIRouter`` and mounted in
:mod:`app.main`.  Route handlers are intentionally thin — they delegate
all logic to :class:`~app.services.DiagnosticService` and map the
result to the appropriate HTTP response.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse

from app.api.dependencies import get_diagnostic_service
from app.models.dtc import (
    DTCResponse,
    ErrorResponse,
    HealthResponse,
    RootResponse,
    SearchResponse,
    StatisticsResponse,
)
from app.services.diagnostic_service import DiagnosticService
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Type alias for the injected service
# ---------------------------------------------------------------------------
_Service = Annotated[DiagnosticService, Depends(get_diagnostic_service)]


# ---------------------------------------------------------------------------
# Health & root
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=RootResponse,
    summary="Service identity",
    tags=["Health"],
)
async def root() -> RootResponse:
    """
    Return a simple service-identity payload.

    Useful for load-balancer or gateway health probes that only need to
    confirm the service is reachable.
    """
    logger.debug("GET / — root endpoint called.")
    return RootResponse()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    tags=["Health"],
)
async def health(service: _Service) -> HealthResponse:
    """
    Return ``{"status": "healthy"}`` when the dataset is loaded.

    Returns 503 Service Unavailable if the dataset has not been
    loaded yet (e.g. during a failed startup).
    """
    logger.debug("GET /health — health check called.")
    if not service.is_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Dataset not loaded.",
        )
    return HealthResponse()


# ---------------------------------------------------------------------------
# DTC lookup
# ---------------------------------------------------------------------------


@router.get(
    "/diagnostics/{dtc_code}",
    response_model=DTCResponse,
    responses={
        404: {"model": ErrorResponse, "description": "DTC code not found"},
    },
    summary="Lookup a single DTC code",
    tags=["Diagnostics"],
)
async def get_diagnostic(dtc_code: str, service: _Service) -> DTCResponse:
    """
    Return the full diagnostic record for the given OBD-II DTC code.

    * Path parameter is **case-insensitive** (``p0301`` == ``P0301``).
    * Returns **HTTP 404** with ``{"error": "DTC code not found"}`` when
      the code does not exist in the dataset.

    Example
    -------
    ``GET /diagnostics/P0301``
    """
    logger.info("GET /diagnostics/%s", dtc_code)
    result = service.get_dtc(dtc_code)

    if result is None:
        logger.warning("DTC '%s' not found — returning 404.", dtc_code)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "DTC code not found"},
        )

    return result


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search DTCs by keyword",
    tags=["Diagnostics"],
)
async def search_diagnostics(
    service: _Service,
    keyword: Annotated[
        str,
        Query(
            min_length=1,
            description=(
                "Keyword to search across description, subsystem, and category."
            ),
        ),
    ],
) -> SearchResponse:
    """
    Case-insensitive substring search across the ``description``,
    ``subsystem``, and ``category`` columns of the dataset.

    Returns a list of matching :class:`~app.models.DTCSearchResult`
    objects.  An empty list is returned when there are no matches —
    this is **not** a 404 condition.

    Example
    -------
    ``GET /search?keyword=misfire``
    """
    logger.info("GET /search?keyword=%s", keyword)
    return service.search(keyword)


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------


@router.get(
    "/statistics",
    response_model=StatisticsResponse,
    summary="Dataset statistics",
    tags=["Analytics"],
)
async def get_statistics(service: _Service) -> StatisticsResponse:
    """
    Return aggregate statistics computed from the in-memory dataset.

    Includes:

    * ``total_dtcs`` — number of codes in the dataset.
    * ``severity_distribution`` — count per severity label.
    * ``category_distribution`` — count per top-level category.
    * ``subsystem_distribution`` — count per subsystem.
    """
    logger.info("GET /statistics")
    return service.get_statistics()
