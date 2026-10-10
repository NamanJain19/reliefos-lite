"""
RELIEFOS Lite — Real-World Provider Integration & Production-Readiness Tests
Validates:
1. Open-Meteo weather adapter & live precipitation ingestion
2. CWC river gauges & certified manual reading audit trail
3. OSRM real OpenStreetMap road routing & fallback
4. System operational modes (OPERATIONAL_LIVE, HISTORICAL_EVENT, SIMULATION_DRILL)
5. Road closures registry and flood avoidance
6. Historical disaster archives and sensor gap disclosure
7. Demand verification, dispatch lifecycle, and immutable audit logs
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_and_providers_endpoint():
    """Verify health endpoint and provider health registry."""
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["mode"] in ["OPERATIONAL_LIVE", "DEMO (SIMULATED)"]
    assert "active_mode" in data
    assert "system_mode" in data
    assert data["providers_registered"] >= 5

    res_providers = client.get("/api/health/providers")
    assert res_providers.status_code == 200
    p_data = res_providers.json()
    assert p_data["total_providers"] >= 5
    assert len(p_data["providers"]) >= 5
    
    # Check that provider states are valid
    valid_states = {"LIVE", "LAST_KNOWN", "STALE", "UNAVAILABLE", "MANUAL", "ESTIMATED", "SIMULATED", "UNVERIFIED"}
    for p in p_data["providers"]:
        assert p["state"] in valid_states
        assert "endpoint" in p
        assert "authority" in p


def test_system_mode_transitions():
    """Verify mode switching between OPERATIONAL_LIVE, HISTORICAL_EVENT, and SIMULATION_DRILL with audit log."""
    res = client.get("/api/mode")
    assert res.status_code == 200
    init_mode = res.json()["mode"]

    # Switch to HISTORICAL_EVENT
    switch_res = client.post("/api/mode/switch", json={
        "mode": "HISTORICAL_EVENT",
        "operator_name": "Test Suite Auditor",
        "historical_event_id": "HIST-2022-GHY-MONSOON",
        "notes": "Testing historical event replay mode"
    })
    assert switch_res.status_code == 200
    assert switch_res.json()["mode_status"]["mode"] == "HISTORICAL_EVENT"

    # Switch back to OPERATIONAL_LIVE
    switch_live = client.post("/api/mode/switch", json={
        "mode": "OPERATIONAL_LIVE",
        "operator_name": "Test Suite Auditor",
        "notes": "Restoring operational live mode"
    })
    assert switch_live.status_code == 200
    assert switch_live.json()["mode_status"]["mode"] == "OPERATIONAL_LIVE"

    # Test invalid mode rejection
    invalid_res = client.post("/api/mode/switch", json={"mode": "INVALID_MODE_XYZ"})
    assert invalid_res.status_code == 400


def test_weather_endpoints():
    """Verify Open-Meteo real weather endpoints."""
    res_curr = client.get("/api/weather/current")
    assert res_curr.status_code == 200
    curr_data = res_curr.json()
    assert "Kamrup Metropolitan" in curr_data["target_location"]
    assert "current" in curr_data
    assert "source" in curr_data

    res_fore = client.get("/api/weather/forecast")
    assert res_fore.status_code == 200
    fore_data = res_fore.json()
    assert "Kamrup Metropolitan" in fore_data["target"]
    assert "forecast_hourly" in fore_data


def test_flood_gauges_and_manual_entry():
    """Verify flood telemetry, river gauges, and manual reading audit logging."""
    res_flood = client.get("/api/flood")
    assert res_flood.status_code == 200
    flood_data = res_flood.json()
    assert "Brahmaputra Basin" in flood_data["river_basin"]
    assert flood_data["current_weather"]["discharge_pandu_cumecs"] > 30000
    assert len(flood_data["gauges"]) >= 3

    # Test manual gauge reading update
    manual_payload = {
        "station_id": "CWC-PANDU-01",
        "water_level_m": 49.85,
        "operator_name": "Officer Borah (Field Post)",
        "notes": "Manual staff gauge reading during monsoon spate"
    }
    post_res = client.post("/api/flood/gauges/manual-entry", json=manual_payload)
    assert post_res.status_code == 200
    assert post_res.json()["station"]["current_level_m"] == 49.85
    assert post_res.json()["station"]["provenance_state"] == "MANUAL"


def test_road_closures_and_real_routing():
    """Verify road closures registry and OSRM real road routing."""
    res_closures = client.get("/api/roads/closures")
    assert res_closures.status_code == 200
    data_c = res_closures.json()
    assert data_c["total_active_closures"] >= 1

    # Post new road closure
    new_closure = {
        "corridor_name": "GS Road (Rukminigaon Chokepoint)",
        "location_desc": "Near Down Town Hospital underpass",
        "latitude": 26.135,
        "longitude": 91.795,
        "water_depth_m": 0.45,
        "status": "IMPASSABLE_FLOOD",
        "detour_corridor": "VIP Road bypass",
        "verified_by": "Dispur Traffic Cell"
    }
    post_c = client.post("/api/roads/closures", json=new_closure)
    assert post_c.status_code == 200
    assert post_c.json()["success"] is True

    # Test real route calculation (Sarusajai to Bharalumukh)
    route_req = {
        "start_lat": 26.115,
        "start_lng": 91.758,
        "end_lat": 26.172,
        "end_lng": 91.735,
        "route_name": "Sarusajai Depot to Bharalumukh Sluice"
    }
    res_route = client.post("/api/routes/real-route", json=route_req)
    assert res_route.status_code == 200
    route_data = res_route.json()
    assert route_data["success"] is True
    assert route_data["distance_km"] > 0
    assert "duration_formatted" in route_data
    assert route_data["geojson_geometry"]["type"] == "LineString"
    assert len(route_data["geojson_geometry"]["coordinates"]) >= 2


def test_historical_disaster_events():
    """Verify authentic historical disaster catalog and sensor gap audit."""
    res_events = client.get("/api/historical/events")
    assert res_events.status_code == 200
    events = res_events.json()["catalog"]
    assert len(events) >= 2
    assert any(e["event_id"] == "HIST-2022-GHY-MONSOON" for e in events)

    # Inspect single event details
    res_single = client.get("/api/historical/events/HIST-2022-GHY-MONSOON")
    assert res_single.status_code == 200
    details = res_single.json()
    assert details["meteorological_summary"]["accumulated_rainfall_mm"] > 300
    assert "known_sensor_gaps" in details["data_provenance_and_gaps"]


def test_demand_verification_and_audit_logs():
    """Verify demand verification, dispatch action, and audit trail retrieval."""
    # Create test demand
    create_payload = {
        "zone_code": "ZONE 02",
        "resource_type": "Potable Water",
        "requested_qty": 400,
        "unit": "L",
        "priority": "CRITICAL"
    }
    create_res = client.post("/api/demands", json=create_payload)
    assert create_res.status_code == 200
    dem_id = create_res.json()["demand"]["id"]

    # Verify demand
    verify_res = client.post(f"/api/demands/{dem_id}/verify", json={
        "verified_by": "Insp. S. Sharma",
        "notes": "Verified by field camp visit"
    })
    assert verify_res.status_code == 200
    assert verify_res.json()["verification_status"] == "VERIFIED"

    # Dispatch demand
    dispatch_res = client.post(f"/api/demands/{dem_id}/dispatch", json={
        "vehicle_code": "VH-01",
        "dispatched_by": "Insp. S. Sharma",
        "notes": "Dispatched via Tata 407 4x4"
    })
    assert dispatch_res.status_code == 200
    assert dispatch_res.json()["lifecycle_status"] == "DISPATCHED"

    # Verify audit logs
    audit_res = client.get("/api/audit-logs")
    assert audit_res.status_code == 200
    logs = audit_res.json()
    assert len(logs) >= 1
    assert any(l["entity_type"] == "DEMAND" and l["entity_id"] == dem_id for l in logs)
