"""
FastAPI dependency providers.

The ``DiagnosticService`` instance is created once during the application
lifespan and stored on ``app.state``.  The ``get_diagnostic_service``
dependency retrieves it from the request's ``app.state``, ensuring every
route handler receives the same pre-loaded service without re-reading the
CSV on every call.
"""

from fastapi import Depends, Request

from app.services.diagnostic_service import DiagnosticService


def get_diagnostic_service(request: Request) -> DiagnosticService:
    """
    FastAPI dependency that returns the application-scoped
    :class:`~app.services.DiagnosticService` instance.

    The instance is attached to ``app.state.diagnostic_service`` during
    the startup lifespan event in :mod:`app.main`.

    Parameters
    ----------
    request:
        Injected automatically by FastAPI.

    Returns
    -------
    DiagnosticService
        The shared, dataset-loaded service instance.
    """
    return request.app.state.diagnostic_service


# Convenience alias so route files can write:
#   ServiceDep = Annotated[DiagnosticService, Depends(get_diagnostic_service)]
DiagnosticServiceDep = Depends(get_diagnostic_service)
