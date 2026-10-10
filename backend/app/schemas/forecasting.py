"""
RELIEFOS Lite — Pydantic Schemas for AI-Assisted Relief Demand Forecasting.
Defines data structures for data sufficiency audits, transparent baseline forecasts,
reference ML benchmark evaluation metrics, and decision-support simulation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class SupportedCategoryAudit(BaseModel):
    category_name: str
    resource_type: str
    unit: str
    active_rows_in_db: int
    has_historical_series: bool
    status: str  # "SUPPORTED", "UNAVAILABLE_HISTORICAL_SERIES"
    notes: str


class DemandDataSufficiencyAudit(BaseModel):
    audited_at: str
    total_active_demands_in_db: int
    active_resource_types: List[str]
    historical_disaster_events_count: int
    has_continuous_timeseries: bool
    is_sufficient_for_ml: bool
    verdict_code: str  # "INSUFFICIENT_FOR_SUPERVISED_ML"
    verdict_explanation: str
    supported_categories: List[SupportedCategoryAudit]
    unsupported_categories: List[SupportedCategoryAudit]
    data_gap_reasons: List[str]
    statutory_data_requirements_to_train_ml: List[str]


class ResourceForecastDetail(BaseModel):
    resource_type: str
    unit: str
    current_verified_demand: float
    forecast_demand: float
    forecast_lower_bound: float
    forecast_upper_bound: float
    variance_from_current: float
    variance_pct: float
    variance_status: str  # "ON_TRACK", "SLIGHT_VARIANCE", "SURGE_PROJECTED", "UNAVAILABLE"
    per_capita_daily_ration: float
    status: str  # "AVAILABLE", "UNAVAILABLE"
    unavailability_reason: Optional[str] = None


class ContributingFactors(BaseModel):
    base_population: int
    estimated_displaced_persons: int
    vulnerability_ratio_pct: float
    flood_risk_score: float
    flood_risk_tier: str
    hazard_escalation_multiplier: float
    forecast_precipitation_24h_mm: float
    river_gauge_variance_m: float
    sphere_ration_standard: str
    terrain_drainage_factor: float


class ZoneDemandForecast(BaseModel):
    zone_code: str
    zone_name: str
    population: int
    estimated_vulnerable_population: int
    vulnerability_ratio_pct: float
    current_risk_tier: str
    current_risk_score: float
    forecast_horizon_hours: int
    hazard_multiplier: float
    contributing_factors: ContributingFactors
    forecasts: List[ResourceForecastDetail]
    data_quality_warnings: List[str]


class CitywideTotals(BaseModel):
    total_current_food_kg: float
    total_current_water_l: float
    total_forecast_food_kg: float
    total_forecast_water_l: float
    total_displaced_persons_est: int
    net_food_variance_kg: float
    net_water_variance_l: float


class DemandForecastResponse(BaseModel):
    generated_at: str
    forecast_horizon_hours: int
    scoring_engine: str  # "TRANSPARENT_BASELINE_SPHERE" | "FALLBACK_BASELINE"
    is_ml_model: bool
    citywide_totals: CitywideTotals
    zones: List[ZoneDemandForecast]
    data_sufficiency: DemandDataSufficiencyAudit
    data_freshness: Dict[str, str]
    governance_notice: str


class MLForecastModelMetadataResponse(BaseModel):
    model_id: str
    model_name: str
    algorithm: str
    training_date_range: str
    temporal_split: Dict[str, Any]
    feature_names: List[str]
    evaluation_metrics: Dict[str, Any]  # MAE, RMSE, MAPE for Food and Water
    operational_status: str
    assumptions: List[str]
    limitations: List[str]
    statutory_data_required_to_promote_to_production: List[str]


class ForecastAllocationSimulationRequest(BaseModel):
    horizon_hours: int = Field(24, ge=12, le=72)
    use_upper_bound: bool = Field(False)


class ZoneSimulationItem(BaseModel):
    zone_code: str
    zone_name: str
    risk_tier: str
    forecast_food_kg: float
    forecast_water_l: float
    simulated_alloc_food_kg: float
    simulated_alloc_water_l: float
    unmet_food_kg: float
    unmet_water_l: float
    fulfillment_pct: float


class ForecastAllocationSimulationResponse(BaseModel):
    simulated_at: str
    horizon_hours: int
    scenario_used: str  # "BASELINE_MEAN" or "UPPER_BOUND_PESSIMISTIC"
    solver_status: str
    depot_stock_adequacy: Dict[str, Any]
    zones: List[ZoneSimulationItem]
    governance_disclaimer: str
