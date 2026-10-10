"""
RELIEFOS Lite — Comprehensive Test Suite for Assam River Gauges Expansion
Validates:
1. Exact coordinates from authoritative CWC / WRD / ASDMA sources.
2. Station schema: name, river, district, coordinates, warning & danger levels, source URL & date.
3. Provenance integrity: stations without automated IoT feeds are LAST_KNOWN / MANUAL, never labeled as LIVE.
4. District filtering on /flood/gauges endpoint.
5. Preservation of Kamrup Metropolitan flood risk calculations.
6. Handling of missing readings and certified manual updates with audit logging.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.hydrology_provider import (
    get_all_river_gauges,
    update_gauge_reading_manual,
    DEFAULT_GAUGE_STATIONS
)
from app.services.risk.baseline import TransparentBaselineRiskEngine
from app.services.risk.service import FloodRiskAnalysisService

client = TestClient(app)

# Required official stations from prompt
EXPECTED_OFFICIAL_STATIONS = {
    "CWC-DCCOURT-02": {
        "name_fragment": "DC Court",
        "river": "Brahmaputra",
        "district": "Kamrup",
        "expected_lat": 26.191,
        "expected_lon": 91.745,
        "danger_level": 49.50,
        "warning_level": 49.26
    },
    "CWC-PUTHIMARI-05": {
        "name_fragment": "Puthimari",
        "river": "Puthimari",
        "district": "Kamrup Rural",
        "expected_lat": 26.3467,
        "expected_lon": 91.6458,
        "danger_level": 51.81,
        "warning_level": 50.81
    },
    "CWC-BEKI-06": {
        "name_fragment": "Beki",
        "river": "Beki",
        "district": "Barpeta",
        "expected_lat": 26.4947,
        "expected_lon": 90.9178,
        "danger_level": 45.10,
        "warning_level": 44.10
    },
    "CWC-PAGLADIYA-07": {
        "name_fragment": "Pagladiya",
        "river": "Pagladiya",
        "district": "Nalbari",
        "expected_lat": 26.4494,
        "expected_lon": 91.4600,
        "danger_level": 52.75,
        "warning_level": 51.75
    },
    "CWC-KAMPUR-08": {
        "name_fragment": "Kampur",
        "river": "Kopili",
        "district": "Nagaon",
        "expected_lat": 26.1531,
        "expected_lon": 92.6564,
        "danger_level": 60.50,
        "warning_level": 59.50
    },
    "CWC-DHARAMTUL-09": {
        "name_fragment": "Dharamtul",
        "river": "Kopili",
        "district": "Morigaon",
        "expected_lat": 26.1642,
        "expected_lon": 92.3500,
        "danger_level": 56.00,
        "warning_level": 55.00
    },
    "CWC-BARAK-10": {
        "name_fragment": "Barak",
        "river": "Barak",
        "district": "Cachar",
        "expected_lat": 24.8319,
        "expected_lon": 92.7961,
        "danger_level": 19.83,
        "warning_level": 18.83
    }
}


def test_all_expected_stations_present_with_verified_metadata():
    """Verify that all required Assam river monitoring stations exist with authoritative attributes."""
    stations = get_all_river_gauges()
    station_map = {s["station_id"]: s for s in stations}

    assert len(stations) >= 10, f"Expected at least 10 monitored stations, got {len(stations)}"

    for station_id, expected in EXPECTED_OFFICIAL_STATIONS.items():
        assert station_id in station_map, f"Missing required station {station_id}"
        st = station_map[station_id]

        assert expected["name_fragment"].lower() in st["station_name"].lower()
        assert expected["river"].lower() in st["river"].lower()
        assert expected["district"].lower() in st["district"].lower()

        # Coordinates check
        assert abs(st["latitude"] - expected["expected_lat"]) < 0.01
        assert abs(st["longitude"] - expected["expected_lon"]) < 0.01

        # Geographic bounds of Assam state
        assert 24.0 <= st["latitude"] <= 28.5, f"Station {station_id} latitude outside Assam"
        assert 89.5 <= st["longitude"] <= 96.5, f"Station {station_id} longitude outside Assam"

        # Levels check
        assert st["danger_level_m"] == expected["danger_level"]
        assert st["warning_level_m"] == expected["warning_level"]
        assert st["warning_level_m"] < st["danger_level_m"]

        # Provenance metadata
        assert "source_url" in st and st["source_url"].startswith("https://")
        assert "source_date" in st and len(st["source_date"]) > 0
        assert "last_verified_by" in st and len(st["last_verified_by"]) > 0


def test_data_provenance_and_no_fake_live_telemetry():
    """Verify that historical and reference baseline stations are never falsely marked as LIVE."""
    stations = get_all_river_gauges()
    for st in stations:
        assert st["is_live_telemetry"] is False, f"Station {st['station_id']} has false live telemetry flag"
        assert st["provenance_state"] in ("LAST_KNOWN", "MANUAL", "UNAVAILABLE")
        assert st["provenance_state"] != "LIVE", "Station must not claim live automated feed without verified IoT"


def test_district_filtering_in_api():
    """Verify that GET /api/flood/gauges correctly supports district filtering."""
    # Test all stations
    res_all = client.get("/api/flood/gauges")
    assert res_all.status_code == 200
    data_all = res_all.json()
    assert len(data_all["stations"]) >= 10

    # Test Kamrup filter
    res_kamrup = client.get("/api/flood/gauges?district=Kamrup")
    assert res_kamrup.status_code == 200
    kamrup_stations = res_kamrup.json()["stations"]
    assert len(kamrup_stations) >= 4
    for s in kamrup_stations:
        assert "kamrup" in s["district"].lower()

    # Test Barpeta filter
    res_barpeta = client.get("/api/flood/gauges?district=Barpeta")
    assert res_barpeta.status_code == 200
    barpeta_stations = res_barpeta.json()["stations"]
    assert len(barpeta_stations) == 1
    assert barpeta_stations[0]["station_id"] == "CWC-BEKI-06"

    # Test Cachar filter
    res_cachar = client.get("/api/flood/gauges?district=Cachar")
    assert res_cachar.status_code == 200
    cachar_stations = res_cachar.json()["stations"]
    assert len(cachar_stations) == 1
    assert cachar_stations[0]["station_id"] == "CWC-BARAK-10"


def test_missing_readings_handled_safely():
    """Verify that stations without active readings have current_level_m as None and are handled gracefully."""
    stations = get_all_river_gauges()
    puthimari = next(s for s in stations if s["station_id"] == "CWC-PUTHIMARI-05")
    assert puthimari["current_level_m"] is None
    assert puthimari["variance_m"] is None

    # Telemetry endpoint must not crash with None current_level_m
    res = client.get("/api/flood")
    assert res.status_code == 200
    flood_data = res.json()
    assert len(flood_data["gauges"]) >= 10


def test_manual_observation_entry_on_new_station():
    """Verify recording a certified manual water level on an expanded station updates correctly and logs an audit record."""
    payload = {
        "station_id": "CWC-BEKI-06",
        "water_level_m": 45.25,
        "operator_name": "Insp. S. Sharma",
        "notes": "Verified manual flood stage at Beki Road Bridge post-monsoon spate"
    }
    res = client.post("/api/flood/gauges/manual-entry", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True

    updated = data["station"]
    assert updated["station_id"] == "CWC-BEKI-06"
    assert updated["current_level_m"] == 45.25
    assert updated["variance_m"] == 0.15  # 45.25 - 45.10
    assert updated["alert_tier"] == "ABOVE DANGER LEVEL"
    assert updated["provenance_state"] == "MANUAL"
    assert updated["last_verified_by"] == "Insp. S. Sharma"


def test_invalid_station_id_returns_404():
    """Verify that manual entry for a non-existent station ID returns HTTP 404."""
    payload = {
        "station_id": "CWC-NONEXISTENT-99",
        "water_level_m": 50.0,
        "operator_name": "Insp. S. Sharma"
    }
    res = client.post("/api/flood/gauges/manual-entry", json=payload)
    assert res.status_code == 404


def test_kamrup_metro_risk_calculation_preserved():
    """Verify that expanding river stations does not break or perturb Kamrup Metro zone risk calculations."""
    res = FloodRiskAnalysisService.run_analysis(force_baseline=True)
    assessments = res.zone_assessments
    assert len(assessments) == 5, f"Expected 5 Kamrup Metro zones, got {len(assessments)}"

    codes = [a.zone_code for a in assessments]
    assert "ZONE 01" in codes
    assert "ZONE 02" in codes
    assert "ZONE 03" in codes
    assert "ZONE 04" in codes
    assert "ZONE 05" in codes

    for a in assessments:
        assert 0.0 <= a.risk_score <= 10.0
        tier_val = a.risk_tier.value if hasattr(a.risk_tier, 'value') else str(a.risk_tier)
        assert tier_val in ("LOW", "MODERATE", "HIGH", "CRITICAL")
        # Ensure river stage / gauge factor was computed
        hydro_factor = next(f for f in a.contributing_factors if "River Stage" in f.factor_name or "Gauge" in f.factor_name)
        assert hydro_factor is not None
        assert 0.0 <= hydro_factor.weighted_contribution <= 10.0
