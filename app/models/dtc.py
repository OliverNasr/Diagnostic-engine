"""
Pydantic models for request/response schemas used by the Diagnostic Engine.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DTCResponse(BaseModel):
    """Full diagnostic record returned for a single DTC lookup."""

    dtc: str = Field(..., description="The OBD-II Diagnostic Trouble Code.")
    description: str = Field(..., description="Short human-readable fault description.")
    subsystem: str = Field(..., description="Vehicle subsystem that triggered the code.")
    category: str = Field(..., description="Top-level category (Engine, Body, Chassis, …).")
    severity: str = Field(..., description="Severity label (Low / Medium / High / Critical).")
    severity_score: int = Field(..., description="Numeric severity score (1–5).")
    safe_to_drive: str = Field(..., description="Whether the vehicle is safe to drive (Yes / No / Depends).")
    immediate_repair: str = Field(..., description="Whether immediate repair is needed (Yes / No).")
    explanation: str = Field(..., description="Detailed technical explanation of the fault.")
    driver_action: str = Field(..., description="Recommended action for the driver.")

    model_config = {"json_schema_extra": {
        "example": {
            "dtc": "P0301",
            "description": "Cylinder 1 Misfire Detected",
            "subsystem": "Ignition",
            "category": "Engine",
            "severity": "High",
            "severity_score": 4,
            "safe_to_drive": "No",
            "immediate_repair": "Yes",
            "explanation": "Cylinder 1 is not firing correctly. Continued driving may damage the catalytic converter.",
            "driver_action": "Stop driving if severe misfire persists. Inspect spark plugs, ignition coils and injectors.",
        }
    }}


class DTCSearchResult(BaseModel):
    """Lightweight record used in search result lists."""

    dtc: str
    description: str
    subsystem: str
    category: str
    severity: str
    severity_score: int
    safe_to_drive: str
    immediate_repair: str


class SearchResponse(BaseModel):
    """Wrapper around a list of DTC search matches."""

    keyword: str = Field(..., description="The keyword that was searched.")
    total: int = Field(..., description="Number of matching records.")
    results: list[DTCSearchResult]


class SeverityDistribution(BaseModel):
    """Count of DTCs per severity label."""

    Low: int = 0
    Medium: int = 0
    High: int = 0
    Critical: int = 0


class StatisticsResponse(BaseModel):
    """Dataset-level statistics returned by /statistics."""

    total_dtcs: int
    severity_distribution: dict[str, int]
    category_distribution: dict[str, int]
    subsystem_distribution: dict[str, int]


class HealthResponse(BaseModel):
    status: str = "healthy"


class RootResponse(BaseModel):
    service: str = "Diagnostic Engine"
    status: str = "running"


class ErrorResponse(BaseModel):
    error: str
