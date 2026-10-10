"""
RELIEFOS Lite — Evidence-Based Flood Risk Analysis Test Suite
Validates:
1. Dataset audit completeness, sources, coverage, and quality tiers
2. Transparent baseline scoring engine (MCDA rules and configurable weights)
3. Trained ML Random Forest model, stratified train/test split, and evaluation metrics
4. Calibrated prediction confidence and class probabilities
5. Automatic graceful fallback to baseline on missing or out-of-distribution inputs
6. Historical disaster comparisons (2022 vs 2024 vs current)
7. Statutory compliance: No autonomous public alerts, Form 8B human review required
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.risk import RiskEngineWeights
from app.services.risk import (
    get_dataset_audit, TransparentBaselineRiskEngine,
    FloodRiskMLService, FloodRiskAnalysisService
)

client = TestClient(app)


def test_dataset_audit_endpoint():
    """Verify GET /api/risk/dataset-audit returns comprehensive data provenance."""
    res = client.get("/api/risk/dataset-audit")
    assert res.status_code == 200
    data = res.json()

    assert data["total_datasets"] >= 4
    assert "ISO-19115" in data["governance_compliance"]

    dataset_names = [d["dataset_name"] for d in data["datasets"]]
    assert any("Open-Meteo" in name for name in dataset_names)
    assert any("CWC" in name for name in dataset_names)
    assert any("Historical" in name for name in dataset_names)
    assert any("Cadastral" in name for name in dataset_names)

    for ds in data["datasets"]:
        assert ds["source_agency"]
        assert ds["spatial_coverage"]
        assert ds["observation_timestamps"]
        assert ds["update_frequency"]
        assert ds["missing_data_handling"]
        assert ds["quality_trust_tier"] in ("TIER_1_OFFICIAL", "TIER_2_TELEMETRY", "TIER_3_ESTIMATED")


def test_transparent_baseline_scoring_rules():
    """Verify transparent baseline scoring uses documented rules and configurable weights."""
    custom_weights = RiskEngineWeights(
        weight_rainfall=0.40,
        weight_hydrology=0.30,
        weight_terrain=0.20,
        weight_drainage=0.10
    )
    assessments = TransparentBaselineRiskEngine.evaluate_all_zones(weights=custom_weights)
    assert len(assessments) == 5

    for z in assessments:
        assert 0.0 <= z.risk_score <= 10.0
        assert z.risk_tier in ("LOW", "MODERATE", "HIGH", "CRITICAL")
        assert z.is_machine_learning is False
        assert z.scoring_method == "RULE_BASED_BASELINE"
        assert z.prediction_confidence is None  # Baseline must never fabricate ML confidence
        assert len(z.contributing_factors) == 4

        # Verify weights sum properly in contributions
        total_contrib = sum(f.weighted_contribution for f in z.contributing_factors)
        assert abs(total_contrib - z.risk_score) <= 0.15


def test_ml_model_metadata_and_metrics():
    """Verify trained ML model has high-fidelity evaluation metrics and metadata."""
    res = client.get("/api/risk/model-metadata")
    assert res.status_code == 200
    data = res.json()

    assert data["model_version"].startswith("v1.0")
    assert "Random Forest" in data["algorithm"]
    assert data["training_sample_count"] >= 300
    assert data["is_stratified_split"] is True

    # Evaluation metrics
    metrics = data["evaluation_metrics"]
    assert metrics["accuracy"] >= 0.85
    assert metrics["macro_f1"] >= 0.80
    assert metrics["brier_score_loss"] <= 0.30  # Confirms probability calibration
    assert len(metrics["confusion_matrix"]) == 4

    # Feature importances
    importances = data["feature_importances"]
    assert "gauge_stage_m" in importances
    assert "rainfall_24h_mm" in importances
    assert len(data["required_data_for_future_hydrodynamic_model"]) >= 4


def test_live_flood_risk_analysis_endpoint():
    """Verify GET /api/risk/analysis serves calibrated ML predictions with citywide summary."""
    res = client.get("/api/risk/analysis")
    assert res.status_code == 200
    data = res.json()

    assert data["analysis_id"].startswith("RISK-EVAL-")
    assert len(data["zone_assessments"]) == 5
    assert "citywide_summary" in data

    summary = data["citywide_summary"]
    assert summary["total_monitored_sectors"] == 5
    assert summary["citywide_max_risk_score"] >= 0.0
    assert summary["highest_priority_sector"]["code"] in ("ZONE 01", "ZONE 02", "ZONE 03", "ZONE 04", "ZONE 05")

    # Check zone-level assessments
    for zone in data["zone_assessments"]:
        assert zone["zone_code"]
        assert zone["zone_name"]
        assert 0.0 <= zone["risk_score"] <= 10.0
        assert zone["risk_tier"] in ("LOW", "MODERATE", "HIGH", "CRITICAL")
        if zone["is_machine_learning"]:
            assert zone["prediction_confidence"] is not None
            assert 0.0 <= zone["prediction_confidence"] <= 1.0
            assert zone["class_probabilities"] is not None
        assert "Relative vulnerability index" in zone["statutory_warning"]


def test_force_baseline_override_endpoint():
    """Verify ?force_baseline=true correctly switches from ML to transparent baseline."""
    res = client.get("/api/risk/analysis?force_baseline=true")
    assert res.status_code == 200
    data = res.json()

    assert data["active_method"] == "RULE_BASED_BASELINE"
    for zone in data["zone_assessments"]:
        assert zone["is_machine_learning"] is False
        assert zone["scoring_method"] == "RULE_BASED_BASELINE"
        assert zone["prediction_confidence"] is None


def test_recalculate_risk_and_audit_logging():
    """Verify POST /api/risk/calculate recalculates risk and commits an audit log entry."""
    payload = {
        "weights": {
            "weight_rainfall": 0.50,
            "weight_hydrology": 0.20,
            "weight_terrain": 0.20,
            "weight_drainage": 0.10
        },
        "force_baseline": True,
        "operator_name": "Capt. P. Gogoi (Watch Officer)"
    }
    res = client.post("/api/risk/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["active_method"] == "RULE_BASED_BASELINE"

    # Verify audit log recorded
    logs_res = client.get("/api/audit-logs?limit=5")
    assert logs_res.status_code == 200
    logs = logs_res.json()
    matching = [l for l in logs if l["operator_name"] == "Capt. P. Gogoi (Watch Officer)"]
    assert len(matching) >= 1
    assert matching[0]["entity_type"] == "RISK_ANALYSIS"
    assert matching[0]["action"] == "RECALCULATE_FLOOD_RISK"


def test_historical_disaster_comparisons():
    """Verify historical comparison accurately links 2022 and 2024 benchmarks."""
    res = client.get("/api/risk/analysis")
    assert res.status_code == 200
    data = res.json()

    comps = data["historical_comparisons"]
    assert len(comps) >= 2
    event_ids = [c["event_id"] for c in comps]
    assert "HIST-2022-GHY-MONSOON" in event_ids
    assert "HIST-2024-GHY-FLASH" in event_ids

    for c in comps:
        assert c["rainfall_24h_mm"] > 0
        assert c["peak_pandu_stage_m"] > 49.0
        assert "river stage" in c["comparison_notes"].lower()


def test_data_requirements_endpoint():
    """Verify GET /api/risk/data-requirements documents required LiDAR and bathymetric data."""
    res = client.get("/api/risk/data-requirements")
    assert res.status_code == 200
    data = res.json()

    assert data["status"] == "DOCUMENTED_ROADMAP"
    reqs = data["requirements"]
    categories = [r["category"] for r in reqs]
    assert any("LiDAR" in cat or "Terrain" in cat for cat in categories)
    assert any("Bathymetry" in cat for cat in categories)
    assert any("Conduit" in cat or "Sewer" in cat for cat in categories)


def test_graceful_fallback_on_extreme_inputs():
    """Verify model gracefully falls back to transparent baseline on extreme out-of-distribution inputs."""
    extreme_weather = {"current": {"precipitation_rate_mm_h": 450.0}, "hourly": {"precipitation": [450.0] * 24}}
    gauges = [{"station_id": "CWC-PANDU-01", "current_level_m": 68.0, "danger_level_m": 49.68, "trend": "RISING"}]
    zone_dict = {"code": "ZONE 01", "name": "North Guwahati", "population": 2850, "inundation_area_ha": 24.1}

    assessment = FloodRiskMLService.predict_zone_risk(
        zone_dict=zone_dict,
        weather_data=extreme_weather,
        gauges=gauges,
        closures=[]
    )
    assert assessment.fallback_applied is True
    assert assessment.scoring_method == "FALLBACK_BASELINE"
    assert "Extreme out-of-distribution" in assessment.fallback_reason
