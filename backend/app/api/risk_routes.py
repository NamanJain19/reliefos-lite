"""
RELIEFOS Lite — Flood Risk Analysis API Routes
Exposes evidence-based flood risk assessments, dataset audits, transparent baseline scoring,
trained ML classification, model metadata, and historical comparisons.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends
from typing import Optional, Dict, Any

from app.core.auth import require_role, WRITE_ROLES

from app.schemas.risk import (
    DatasetAuditResponse, FloodRiskAnalysisResponse,
    MLModelMetadataResponse, RecalculateRiskRequest, RiskEngineWeights
)
from app.services.risk import (
    get_dataset_audit, FloodRiskMLService,
    get_hydrodynamic_data_requirements, FloodRiskAnalysisService
)
from app.core.database import SessionLocal
from app.models.domain import AuditLogModel

from app.core.location_registry import resolve_location

router = APIRouter(prefix="/risk", tags=["Flood Risk Analysis & Machine Learning"])


@router.get(
    "/dataset-audit",
    response_model=DatasetAuditResponse,
    summary="Audit of all operational datasets, provenance, sensor gaps, and quality tiers"
)
async def get_dataset_audit_endpoint(
    loc_id: str = Depends(resolve_location)
):
    """
    Returns an authoritative ISO-19115 compliant audit of all operational datasets
    powering the flood risk engine: Open-Meteo, CWC Hydrology, ASDMA Historical Archive,
    Kamrup Cadastral Zones, and PWD Road Closures.
    """
    return get_dataset_audit()


@router.get(
    "/analysis",
    response_model=FloodRiskAnalysisResponse,
    summary="Evaluate relative flood risk for all operational zones using ML with baseline fallback"
)
async def get_flood_risk_analysis(
    force_baseline: bool = Query(False, description="Force transparent rule-based MCDA baseline instead of ML"),
    zone_code: Optional[str] = Query(None, description="Optional target zone code to filter (e.g. 'ZONE 01')"),
    loc_id: str = Depends(resolve_location)
):
    """
    Estimates relative flood risk across Kamrup Metropolitan or monitored Assam operational zones.
    - Evaluates live rainfall, NWP forecast, CWC gauge stages, terrain elevation, and road closures.
    - Uses trained Random Forest classifier with statistically calibrated confidence.
    - Automatically falls back to transparent rule-based MCDA baseline on missing or extreme inputs.
    - Never fabricates hydrodynamic flood depth or exact wave propagation timing.
    """
    return FloodRiskAnalysisService.run_analysis(
        force_baseline=force_baseline,
        target_zone_code=zone_code,
        location_id=loc_id
    )


@router.post(
    "/calculate",
    response_model=FloodRiskAnalysisResponse,
    summary="Recalculate relative flood risk with custom planner weights or baseline override"
)
async def recalculate_flood_risk(
    request: RecalculateRiskRequest,
    current_user: Dict[str, Any] = Depends(require_role(WRITE_ROLES))
):
    """
    Allows emergency operations center planners to adjust sub-index weights or force baseline mode.
    Records an immutable audit log entry in the operational database.
    """
    response = FloodRiskAnalysisService.run_analysis(
        weights=request.weights,
        force_baseline=request.force_baseline,
        target_zone_code=request.target_zone_code,
        location_id=getattr(request, "location_id", "kamrup_metro")
    )

    # Record planner calculation in audit log
    db = SessionLocal()
    try:
        log_entry = AuditLogModel(
            operator_name=request.operator_name or "Insp. S. Sharma (EOC Planner)",
            entity_type="RISK_ANALYSIS",
            entity_id=response.analysis_id,
            action="RECALCULATE_FLOOD_RISK",
            old_value="DEFAULT_WEIGHTS",
            new_value=f"FORCE_BASELINE={request.force_baseline}",
            notes=f"Planner evaluated risk with custom parameters for {request.target_zone_code or 'ALL_ZONES'}"
        )
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    return response


@router.get(
    "/model-metadata",
    response_model=MLModelMetadataResponse,
    summary="Retrieve trained ML model architecture, evaluation metrics, and feature importances"
)
async def get_ml_model_metadata():
    """
    Returns complete metadata of the trained Random Forest flood-risk classifier:
    - 80/20 Stratified train/test split metrics (Accuracy, Precision, Recall, Macro F1, Brier Score)
    - Confusion matrix and feature importances
    - Hyperparameters and training dataset specification
    - Roadmap of required datasets for future 2D hydrodynamic modeling
    """
    return FloodRiskMLService.get_metadata()


@router.get(
    "/data-requirements",
    summary="Documented data requirements roadmap for high-resolution hydrodynamic modeling"
)
async def get_data_requirements_endpoint():
    """
    Returns the exact sensory, bathymetric, LiDAR, and stormwater conduit specifications
    required to advance from relative risk classification to 2D hydrodynamic inundation modeling.
    """
    return {
        "status": "DOCUMENTED_ROADMAP",
        "governance_standard": "NDMA / CWC Flood Modeling Guidelines v3.1",
        "requirements": get_hydrodynamic_data_requirements()
    }
