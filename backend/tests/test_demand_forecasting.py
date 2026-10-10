"""
RELIEFOS Lite — Relief Demand Forecasting Unit Tests.
Validates:
1. Demand projections adhere strictly to Sphere humanitarian standards (food & water).
2. Bounds (lower, upper) exist and enclose forecast estimates.
3. Unsupported categories (medical kits, shelter beds) are explicitly labeled as UNAVAILABLE.
4. Data sufficiency audit transparently flags INSUFFICIENT_FOR_SUPERVISED_ML without data leakage.
5. Reference benchmark ML metrics (MAE, RMSE, MAPE) are retrievable with statutory requirements.
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_demand_forecast_endpoint_returns_valid_sphere_projections():
    """Verify GET /api/forecasting/forecast returns structured baseline demand."""
    resp = client.get("/api/forecasting/forecast?horizon_hours=24")
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["forecast_horizon_hours"] == 24
    assert data["scoring_engine"] == "TRANSPARENT_BASELINE_SPHERE"
    assert data["is_ml_model"] is False

    citywide = data["citywide_totals"]
    assert citywide["total_forecast_food_kg"] > 0
    assert citywide["total_forecast_water_l"] > 0
    assert citywide["total_displaced_persons_est"] > 0

    zones = data["zones"]
    assert len(zones) == 5

    for z in zones:
        assert "zone_code" in z
        assert z["current_risk_tier"] in ("CRITICAL", "HIGH", "MODERATE", "LOW")
        assert len(z["forecasts"]) >= 3

        food_item = next(f for f in z["forecasts"] if f["resource_type"] == "DRY_FOOD_RATIONS")
        water_item = next(f for f in z["forecasts"] if f["resource_type"] == "POTABLE_WATER")
        med_item = next(f for f in z["forecasts"] if f["resource_type"] == "MEDICAL_TRAUMA_KITS")

        assert food_item["status"] == "AVAILABLE"
        assert food_item["forecast_lower_bound"] <= food_item["forecast_demand"] <= food_item["forecast_upper_bound"]

        assert water_item["status"] == "AVAILABLE"
        assert water_item["forecast_lower_bound"] <= water_item["forecast_demand"] <= water_item["forecast_upper_bound"]

        # Medical kits must be explicitly labeled UNAVAILABLE to prevent hallucinated supply orders
        assert med_item["status"] == "UNAVAILABLE"
        assert med_item["unavailability_reason"] is not None


def test_forecast_horizon_parameter_scaling():
    """Verify 48-hour horizon scales demand proportionally compared to 24-hour horizon."""
    resp_24 = client.get("/api/forecasting/forecast?horizon_hours=24")
    resp_48 = client.get("/api/forecasting/forecast?horizon_hours=48")

    assert resp_24.status_code == 200
    assert resp_48.status_code == 200

    food_24 = resp_24.json()["citywide_totals"]["total_forecast_food_kg"]
    food_48 = resp_48.json()["citywide_totals"]["total_forecast_food_kg"]

    # 48-hour should be approximately 2x 24-hour
    assert food_48 > food_24
    assert abs(food_48 - (2 * food_24)) < 2.0


def test_data_sufficiency_audit():
    """Verify GET /api/forecasting/data-sufficiency transparently documents data limits."""
    resp = client.get("/api/forecasting/data-sufficiency")
    assert resp.status_code == 200
    audit = resp.json()

    assert audit["is_sufficient_for_ml"] is False
    assert audit["verdict_code"] == "INSUFFICIENT_FOR_SUPERVISED_ML"
    assert len(audit["supported_categories"]) >= 2
    assert len(audit["unsupported_categories"]) >= 2
    assert len(audit["data_gap_reasons"]) > 0
    assert len(audit["statutory_data_requirements_to_train_ml"]) > 0


def test_forecasting_model_benchmark_metadata():
    """Verify GET /api/forecasting/model-metadata returns offline reference evaluation metrics."""
    resp = client.get("/api/forecasting/model-metadata")
    assert resp.status_code == 200
    meta = resp.json()

    assert meta["model_id"] == "DEMAND-BENCHMARK-RF-V1.0"
    assert meta["operational_status"] == "OFFLINE_REFERENCE_BENCHMARK_ONLY"
    metrics = meta["evaluation_metrics"]
    assert "food_kits_mae_kg" in metrics
    assert "food_kits_rmse_kg" in metrics
    assert "food_kits_mape_pct" in metrics
    assert "water_liters_mae_l" in metrics
    assert len(meta["statutory_data_required_to_promote_to_production"]) > 0
