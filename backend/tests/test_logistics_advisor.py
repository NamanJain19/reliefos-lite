"""
RELIEFOS Lite — Comprehensive Test Suite for AI-Assisted Resource Allocation & Logistics Advisor.
Tests:
1. OR-Tools CP-SAT plan generation consistency & physical conservation.
2. Multi-strategy comparison (Lexicographic vs Proportional vs Distance vs Water-First).
3. What-if scenario execution with strict simulation isolation (zero DB mutations).
4. Road closure handling & severed route topology.
5. Inventory bottleneck detection and binding constraints.
6. Form 8B human review authorization and SQLite audit log persistence.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.domain import DemandModel, InventoryItemModel, AuditLogModel, ZoneModel
from app.schemas.logistics_advisor import LogisticsStrategyEnum

client = TestClient(app)


def test_logistics_plan_endpoint():
    """Verify GET /api/logistics-advisor/plan generates a mathematically sound, reviewable plan."""
    resp = client.get("/api/logistics-advisor/plan")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()

    assert data["plan_id"].startswith("LOG-PLAN-")
    assert "OR-Tools" in data["solver_engine"]
    assert data["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert data["active_strategy"] == "LEXICOGRAPHIC_SEVERITY_OPTIMAL"

    # Conservation checks
    assert data["total_allocated_kg"] <= data["total_available_stock_kg"]
    assert data["total_allocated_kg"] <= data["total_fleet_capacity_kg"]
    assert data["total_allocated_kg"] + data["total_unmet_kg"] == data["total_demand_kg"]

    # Zones check
    assert len(data["zones"]) == 5
    for z in data["zones"]:
        assert z["zone_code"] in ("ZONE 01", "ZONE 02", "ZONE 03", "ZONE 04", "ZONE 05")
        assert z["alloc_food_kg"] + z["alloc_water_kg"] == z["total_alloc_kg"]
        assert z["total_alloc_kg"] + z["deficit_kg"] == z["total_demand_kg"]
        assert len(z["ai_allocation_rationale"]) > 10

    # Route check
    assert len(data["routes"]) >= 2
    for r in data["routes"]:
        assert r["vehicle_code"] in ("VH-01", "VH-02", "VH-03")
        assert len(r["polyline_coordinates"]) > 0
        assert r["total_distance_km"] > 0

    # Diagnostics check
    assert "binding_constraints" in data["diagnostics"]
    assert len(data["diagnostics"]["binding_constraints"]) > 0
    assert "cwc_river_gauges" in data["diagnostics"]["telemetry_freshness"]

    # Safety disclaimer
    assert "Form 8B" in data["safety_disclaimer"]


def test_multi_strategy_comparisons():
    """Verify GET /api/logistics-advisor/strategies compares all 4 distinct CP-SAT formulations."""
    resp = client.get("/api/logistics-advisor/strategies")
    assert resp.status_code == 200
    strats = resp.json()

    assert len(strats) == 4
    strat_ids = [s["strategy_id"] for s in strats]
    assert "LEXICOGRAPHIC_SEVERITY_OPTIMAL" in strat_ids
    assert "PROPORTIONAL_EQUAL_SHARE" in strat_ids
    assert "DISTANCE_MINIMIZING_PROXIMITY" in strat_ids
    assert "WATER_FIRST_SURVIVAL" in strat_ids

    lex_strat = next(s for s in strats if s["strategy_id"] == "LEXICOGRAPHIC_SEVERITY_OPTIMAL")
    prop_strat = next(s for s in strats if s["strategy_id"] == "PROPORTIONAL_EQUAL_SHARE")
    dist_strat = next(s for s in strats if s["strategy_id"] == "DISTANCE_MINIMIZING_PROXIMITY")
    water_strat = next(s for s in strats if s["strategy_id"] == "WATER_FIRST_SURVIVAL")

    assert lex_strat["is_recommended"] is True
    assert prop_strat["is_recommended"] is False

    # Lexicographic guarantees superior Critical Zone coverage vs Proportional
    assert lex_strat["critical_zone_coverage_pct"] >= prop_strat["critical_zone_coverage_pct"]

    # All strategies should find optimal or feasible solutions
    for s in strats:
        assert s["solver_status"] in ("OPTIMAL", "FEASIBLE")
        assert s["total_allocated_kg"] > 0
        assert s["est_transit_distance_km"] > 0


def test_what_if_scenario_isolation():
    """Verify POST /api/logistics-advisor/what-if runs in an isolated sandbox with zero DB mutations."""
    db = SessionLocal()
    initial_demand_count = db.query(DemandModel).count()
    initial_inventory_count = db.query(InventoryItemModel).count()
    initial_zone_count = db.query(ZoneModel).count()
    db.close()

    payload = {
        "scenario_title": "Surge Test: Embankment Breach with Stock Reinforcement",
        "custom_stock_food_kg": 6000.0,
        "custom_stock_water_kg": 6000.0,
        "disabled_vehicles": ["VH-03"],
        "severed_zones": [],
        "demand_multiplier": 1.25,
        "strategy": "LEXICOGRAPHIC_SEVERITY_OPTIMAL"
    }

    resp = client.post("/api/logistics-advisor/what-if", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["database_mutated"] is False
    assert data["feasibility_status"] == "FEASIBLE"
    assert "simulated_allocated_kg" in data
    assert "allocated_delta_kg" in data
    assert len(data["ai_impact_analysis"]) > 20

    # Strict assertion: SQLite database must not be modified by simulation
    db = SessionLocal()
    assert db.query(DemandModel).count() == initial_demand_count
    assert db.query(InventoryItemModel).count() == initial_inventory_count
    assert db.query(ZoneModel).count() == initial_zone_count
    db.close()


def test_severed_route_topology_handling():
    """Verify solver enforces zero allocation when a zone is severed by flood inundation."""
    payload = {
        "scenario_title": "Saraighat Bridge Severed Test",
        "severed_zones": ["ZONE 01"],
        "strategy": "LEXICOGRAPHIC_SEVERITY_OPTIMAL"
    }

    resp = client.post("/api/logistics-advisor/what-if", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    # Zone 01 must receive 0 kg allocation when severed
    z01 = next((z for z in data["zones"] if z["zone_code"] == "ZONE 01"), None)
    assert z01 is not None
    assert z01["total_alloc_kg"] == 0.0
    assert z01["is_accessible"] is False


def test_human_review_authorization_and_audit_logging():
    """Verify POST /api/logistics-advisor/review logs human sign-off into SQLite audit trail."""
    review_payload = {
        "action": "APPROVE",
        "operator_name": "Insp. S. Sharma (EOC Planner)",
        "review_notes": "Reviewed against CWC Pandu Gauge (49.68m). Approved for staging at Sarusajai Hub.",
        "form_8b_reference": "ASDMA-F8B-2026-10-04-TEST-01",
        "disclaimer_acknowledged": True
    }

    resp = client.post("/api/logistics-advisor/review", json=review_payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["success"] is True
    assert data["review_status"] == "APPROVED"
    assert data["audit_log_id"] > 0
    assert "staging manifest authorized" in data["operational_next_step"].lower()

    # Verify record in SQLite audit_logs
    db = SessionLocal()
    log_entry = db.query(AuditLogModel).filter(AuditLogModel.id == data["audit_log_id"]).first()
    assert log_entry is not None
    assert log_entry.operator_name == "Insp. S. Sharma (EOC Planner)"
    assert log_entry.entity_type == "LOGISTICS_PLAN"
    db.close()

    # Verify plan endpoint now reflects APPROVED status
    plan_resp = client.get("/api/logistics-advisor/plan")
    assert plan_resp.status_code == 200
    assert plan_resp.json()["review_status"] == "APPROVED"
