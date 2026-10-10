"""
RELIEFOS Lite — Relief Demand Forecasting API Endpoints.
Provides decision-support endpoints for data sufficiency audits, transparent baseline
humanitarian demand forecasts, and reference machine learning model evaluation metrics.
"""

from fastapi import APIRouter, Query, HTTPException, status, Depends
from app.core.location_registry import resolve_location
from app.schemas.forecasting import (
    DemandForecastResponse, DemandDataSufficiencyAudit, MLForecastModelMetadataResponse
)
from app.services.forecasting.service import DemandForecastingService

router = APIRouter(prefix="/forecasting", tags=["Demand Forecasting & Sphere Projections"])


@router.get("/forecast", response_model=DemandForecastResponse, summary="Retrieve zone demand projections")
async def get_demand_forecast_endpoint(
    horizon_hours: int = Query(24, ge=12, le=72, description="Forecast horizon in hours (12-72h)"),
    loc_id: str = Depends(resolve_location)
):
    """
    Returns transparent baseline relief demand projections for Kamrup Metro or unconfigured status for other districts.
    Adheres strictly to Sphere humanitarian standards (2,100 kcal / 0.5kg food and 3.0L water/person/day)
    scaled by real-time hydrometeorological risk multipliers.
    Explicitly discloses un-modeled categories to prevent hallucinated supply orders.
    """
    try:
        return DemandForecastingService.generate_demand_forecast(horizon_hours=horizon_hours, location_id=loc_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demand forecasting calculation failed: {str(e)}"
        )


@router.get("/data-sufficiency", response_model=DemandDataSufficiencyAudit, summary="Audit demand data sufficiency")
async def get_demand_data_sufficiency(
    loc_id: str = Depends(resolve_location)
):
    """
    Audits operational database and historical archive for demand forecasting sufficiency.
    Provides ISO-19115 compliant audit proving why continuous timeseries ML is held in offline benchmark.
    """
    try:
        return DemandForecastingService.audit_data_sufficiency(location_id=loc_id)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demand sufficiency audit failed: {str(e)}"
        )


@router.get("/model-metadata", response_model=MLForecastModelMetadataResponse, summary="Inspect offline reference ML metrics")
async def get_forecasting_model_metadata():
    """
    Returns offline benchmark Random Forest regression metrics (MAE, RMSE, MAPE) evaluated on historical floods
    and statutory criteria required before promotion to autonomous operational production.
    """
    try:
        return DemandForecastingService.get_benchmark_metadata()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve forecasting benchmark metadata: {str(e)}"
        )
