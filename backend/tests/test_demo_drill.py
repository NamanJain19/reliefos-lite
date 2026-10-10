"""
Phase 5 Capstone Verification Test Suite
Guwahati Urban Flood Emergency — Relief Operations Drill
Validates:
1. Drill status reporting & ISO-19115 provenance labeling
2. Deterministic drill scenario loading & sandboxing
3. Lexicographic optimization & NetworkX flood detour execution
4. ASDMA Form 8B dispatch dossier generation & SHA-256 integrity hashing
5. State reset & live operational store immutability
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_demo_drill_status_endpoint():
    """Verify demonstration drill status and ISO-19115 lineage metadata."""
    response = client.get("/api/demo/drill/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "scenario_metadata" in data
    assert data["scenario_metadata"]["incident_code"] == "ASDMA-DRILL-2024-GHY-01"
    assert data["data_provenance"] == "SIMULATED_DRILL_EXERCISE"
    assert "Zero mutation to operational database" in data["isolation_guarantee"]


def test_demo_drill_load_endpoint():
    """Verify loading the deterministic drill scenario into memory sandbox."""
    response = client.post("/api/demo/drill/load")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["incident_code"] == "ASDMA-DRILL-2024-GHY-01"

    # Verify demand reconciliation
    demand = data["demand_summary"]
    assert demand["total_demand_food_kg"] == 2500.0
    assert demand["total_demand_water_l"] == 4000.0
    assert demand["total_demand_payload_kg"] == 6500.0

    # Verify fleet capacity
    fleet = data["fleet_summary"]
    assert fleet["vehicle_count"] == 3
    assert fleet["single_wave_payload_capacity_kg"] == 5000.0

    # Verify supply gap (6500 demand vs 5000 fleet capacity = 1500 kg gap)
    assert data["single_wave_supply_gap_kg"] == 1500.0


def test_demo_drill_run_optimization_and_routing():
    """Verify full end-to-end execution of lexicographic solver and detour router."""
    # Ensure loaded
    client.post("/api/demo/drill/load")

    # Run drill execution
    response = client.post("/api/demo/drill/run")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Validate optimization output
    opt = data["optimization"]
    assert opt["solver_status"] in ["OPTIMAL", "FEASIBLE"]
    assert opt["total_allocated_kg"] <= 5000.0  # Fleet payload limit respected
    assert opt["unmet_demand_payload_kg"] >= 0.0

    # Validate routing and flood detours
    routing = data["routing"]
    assert "routes" in routing
    assert len(routing["routes"]) >= 1
    assert routing["total_distance_km"] > 0
    assert "detours_applied" in routing
    assert routing["detours_applied"] >= 1  # MG Road submerged detour via AT Road


def test_demo_drill_export_dossier():
    """Verify generated ASDMA Form 8B export format and SHA-256 digital signature."""
    client.post("/api/demo/drill/load")
    client.post("/api/demo/drill/run")

    response = client.get("/api/demo/drill/export")
    assert response.status_code == 200
    dossier = response.json()
    assert "asdma_form_8b_manifest" in dossier
    manifest = dossier["asdma_form_8b_manifest"]
    assert manifest["incident_code"] == "ASDMA-DRILL-2024-GHY-01"
    assert manifest["drill_exercise"] is True
    assert "sha256_integrity_hash" in manifest
    assert len(manifest["sha256_integrity_hash"]) == 64  # Valid SHA-256 hex string
    assert len(manifest["manifest_items"]) == 3  # Tata 407, Ashok Leyland, Bolero Pickup


def test_demo_drill_reset_endpoint():
    """Verify clean reset of demonstration environment to default baseline."""
    client.post("/api/demo/drill/load")
    response = client.post("/api/demo/drill/reset")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

    # Check status is now idle
    status_res = client.get("/api/demo/drill/status")
    status_data = status_res.json()
    assert status_data["is_loaded"] is False
    assert status_data["is_executed"] is False


def test_demo_drill_database_immutability():
    """Verify running the drill does NOT mutate operational inventory or demand records."""
    # Capture live inventory and demand before drill
    inv_before = client.get("/api/inventory").json()
    dem_before = client.get("/api/demands").json()

    # Load and execute full drill
    client.post("/api/demo/drill/load")
    client.post("/api/demo/drill/run")

    # Capture live inventory and demand after drill execution
    inv_after = client.get("/api/inventory").json()
    dem_after = client.get("/api/demands").json()

    # Reset drill
    client.post("/api/demo/drill/reset")

    # Live operational database must remain 100% identical
    assert inv_before == inv_after, "Operational inventory was mutated by simulation drill!"
    assert dem_before == dem_after, "Operational demand records were mutated by simulation drill!"
