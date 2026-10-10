"""
RELIEFOS Lite — Flood Risk Analysis Schemas
Defines request/response contracts for dataset audits, transparent baseline scoring,
trained machine learning flood-risk classification, and historical comparisons.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class FloodRiskTier(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskEngineMethod(str, Enum):
    RULE_BASED_BASELINE = "RULE_BASED_BASELINE"
    ML_RANDOM_FOREST = "ML_RANDOM_FOREST"
    ML_GRADIENT_BOOSTING = "ML_GRADIENT_BOOSTING"
    FALLBACK_BASELINE = "FALLBACK_BASELINE"


class DatasetAuditItem(BaseModel):
    dataset_name: str
    source_agency: str
    spatial_coverage: str
    observation_timestamps: str
    update_frequency: str
    missing_data_handling: str
    known_sensor_gaps: str
    provenance_classification: str
    quality_trust_tier: str
    limitations: str


class DatasetAuditResponse(BaseModel):
    audit_title: str
    audited_at: str
    total_datasets: int
    datasets: List[DatasetAuditItem]
    governance_compliance: str


class RiskEngineWeights(BaseModel):
    weight_rainfall: float = Field(0.30, ge=0.0, le=1.0, description="Weight for rainfall and forecast hazard (0.0-1.0)")
    weight_hydrology: float = Field(0.30, ge=0.0, le=1.0, description="Weight for river stage and gauge surcharge (0.0-1.0)")
    weight_terrain: float = Field(0.25, ge=0.0, le=1.0, description="Weight for terrain elevation and population exposure (0.0-1.0)")
    weight_drainage: float = Field(0.15, ge=0.0, le=1.0, description="Weight for road closures and drainage impedance (0.0-1.0)")


class FactorContribution(BaseModel):
    factor_name: str
    raw_value: str
    normalized_score_0_to_10: float
    weight_applied: float
    weighted_contribution: float
    provenance: str


class ZoneRiskAssessment(BaseModel):
    zone_code: str
    zone_name: str
    risk_score: float = Field(..., ge=0.0, le=10.0, description="Composite relative risk score (0.0 to 10.0)")
    risk_tier: FloodRiskTier
    scoring_method: RiskEngineMethod
    is_machine_learning: bool
    prediction_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Statistically calibrated prediction confidence (ML only)")
    class_probabilities: Optional[Dict[str, float]] = Field(None, description="Calibrated class probabilities (ML only)")
    fallback_applied: bool = False
    fallback_reason: Optional[str] = None
    primary_driver: str
    contributing_factors: List[FactorContribution]
    affected_population: int
    inundation_area_ha: float
    water_depth_m: Optional[float] = None
    data_freshness_label: str
    limitations: str
    statutory_warning: str = "Relative vulnerability index. Not a hydrodynamic inundation prediction."


class MLModelEvaluationMetrics(BaseModel):
    accuracy: float
    macro_precision: float
    macro_recall: float
    macro_f1: float
    weighted_f1: float
    brier_score_loss: float
    confusion_matrix: List[List[int]]
    classes: List[str]


class MLModelMetadataResponse(BaseModel):
    model_name: str
    model_version: str
    algorithm: str
    trained_at: str
    training_sample_count: int
    train_test_split_ratio: str
    is_stratified_split: bool
    target_variable: str
    feature_definitions: List[Dict[str, str]]
    feature_importances: Dict[str, float]
    evaluation_metrics: MLModelEvaluationMetrics
    hyperparameters: Dict[str, Any]
    required_data_for_future_hydrodynamic_model: List[str]


class HistoricalComparisonItem(BaseModel):
    event_id: str
    event_title: str
    event_period: str
    rainfall_24h_mm: float
    peak_pandu_stage_m: float
    inundation_extent_sq_km: float
    displaced_population: int
    comparison_notes: str


class FloodRiskAnalysisResponse(BaseModel):
    analysis_id: str
    evaluated_at: str
    system_mode: str
    active_method: RiskEngineMethod
    model_version: Optional[str] = None
    citywide_summary: Dict[str, Any]
    zone_assessments: List[ZoneRiskAssessment]
    weights_applied: RiskEngineWeights
    historical_comparisons: List[HistoricalComparisonItem]
    governance_notice: str = "ASDMA Decision Support — Advisory relative flood risk index only. Official Form 8B physical review required before operational mobilization."


class RecalculateRiskRequest(BaseModel):
    weights: Optional[RiskEngineWeights] = None
    force_baseline: bool = False
    target_zone_code: Optional[str] = None
    location_id: Optional[str] = "kamrup_metro"
    operator_name: Optional[str] = "Insp. S. Sharma (EOC Planner)"

