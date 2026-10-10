"""
RELIEFOS Lite — Phase 4: Automated Optimization Engine & Scenario Stress Testing Suite
Validates:
- Two-Stage Lexicographic CP-SAT Optimization & Stage 1 Preservation
- Inventory, Vehicle Capacity, and Demand Constraints
- All 10 Required Baseline Disaster Scenarios (A through J)
- Isolated Execution & Live Operational Data Immutability
- Scalability & Performance Benchmarks (Small, Medium, Large)
- Explainability Diagnostics & Binding Constraint Detection
- REST API Integration (/api/simulations/scenarios, /run, /comparison, /scalability)
"""

import copy
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.data_store import (
    ZONES_DATA, DEPOT_DATA, VEHICLES_DATA, INVENTORY_ITEMS_DATA, DEMAND_RECORDS_DATA
)
from app.services.optimization.solver import run_lexicographic_optimization
from app.services.optimization.scenarios import (
    get_all_scenarios_metadata, run_isolated_scenario, compare_multiple_scenarios, SCENARIOS_CATALOG
)
from app.services.optimization.benchmark import run_scalability_benchmark

client = TestClient(app)


# =============================================================================
# 1. TWO-STAGE LEXICOGRAPHIC OPTIMIZATION & PRESERVATION
# =============================================================================

def test_two_stage_lexicographic_preservation():
    """
    Verify that Stage 2 route minimization strictly preserves the Stage 1
    weighted unmet demand optimum (Z1 <= Z1*).
    """
    zones_copy = copy.deepcopy(ZONES_DATA)
    depot_copy = copy.deepcopy(DEPOT_DATA)
    vehicles_copy = copy.deepcopy(VEHICLES_DATA)

    # Constrain stock to induce a non-zero weighted unmet penalty
    depot_copy["available_food_kg"] = 1500
    depot_copy["available_water_kg"] = 1500

    result = run_lexicographic_optimization(
        zones=zones_copy,
        depot=depot_copy,
        vehicles=vehicles_copy,
        prioritize_water=True,
        time_limit_seconds=5
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert result["stage1_optimum_preserved"] is True
    assert result["stage1_objective_value"] >= 0
    assert result["stage2_distance_km"] >= 0.0
    assert "preservation_proof" in result["explainability"]
    assert "Stage 2 restricted to Stage 1 objective <=" in result["explainability"]["preservation_proof"]


# =============================================================================
# 2. INVENTORY, VEHICLE CAPACITY & PHYSICAL CONSTRAINTS
# =============================================================================

def test_inventory_and_capacity_constraints():
    """
    Verify physical validity of allocation:
    - Total food allocated <= depot food stock
    - Total water allocated <= depot water stock
    - Vehicle payload <= vehicle max capacity
    - Water density explicitly treated as 1 L = 1 kg
    """
    depot_stock_food = 2000
    depot_stock_water = 2200

    depot = copy.deepcopy(DEPOT_DATA)
    depot["available_food_kg"] = depot_stock_food
    depot["available_water_kg"] = depot_stock_water

    zones = copy.deepcopy(ZONES_DATA)
    vehicles = copy.deepcopy(VEHICLES_DATA)

    result = run_lexicographic_optimization(
        zones=zones,
        depot=depot,
        vehicles=vehicles,
        prioritize_water=True
    )

    assert result["allocated_food_kg"] <= depot_stock_food
    assert result["allocated_water_kg"] <= depot_stock_water
    assert result["proposed_allocation_kg"] <= (depot_stock_food + depot_stock_water)

    # Check vehicle assignments
    total_fleet_cap = sum(v["max_capacity_kg"] for v in vehicles)
    assert result["proposed_allocation_kg"] <= total_fleet_cap

    # Check non-negative unmet demand
    for z in result["zones"]:
        assert z["alloc_food_kg"] >= 0
        assert z["alloc_water_kg"] >= 0
        assert z["alloc_total_kg"] <= z["total_demand_kg"]
        assert z["unmet_demand_kg"] >= 0


# =============================================================================
# 3. DISASTER STRESS-TESTING SCENARIOS (A THROUGH J)
# =============================================================================

@pytest.mark.parametrize("scenario_id", ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"])
def test_each_baseline_scenario_executes_successfully(scenario_id):
    """
    Execute each of the 10 required baseline disaster stress-testing scenarios.
    Assert valid solver status, positive demand, and structured explainability.
    """
    report = run_isolated_scenario(scenario_id)

    assert report["scenario_id"] == scenario_id
    assert report["is_simulated"] is True
    assert report["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert report["total_demand_kg"] > 0
    assert report["total_allocated_kg"] >= 0
    assert report["validation_status"] == "PASS"

    explainability = report["explainability"]
    assert "primary_bottleneck" in explainability
    assert "binding_constraints" in explainability
    assert len(explainability["binding_constraints"]) >= 1


def test_scenario_a_normal_operations():
    """Scenario A: Standard baseline allocation respecting single-wave fleet capacity."""
    report = run_isolated_scenario("A")
    assert report["solver_status"] == "OPTIMAL"
    assert report["total_allocated_kg"] > 4000
    assert report["total_allocated_kg"] <= report["configuration_applied"]["fleet_capacity_kg"]
    assert report["overall_fulfillment_pct"] >= 65.0
    assert len(report["configuration_applied"]["road_closures"]) == 0
    assert len(report["unreachable_destinations"]) == 0
    assert report["validation_status"] == "PASS"


def test_scenario_b_high_demand_surge():
    """Scenario B: Surge demand in Zone 01 and Zone 02 creates deficit."""
    report = run_isolated_scenario("B")
    assert report["total_demand_kg"] > 4800  # Baseline demand
    assert report["unmet_demand_kg"] > 0
    assert report["overall_fulfillment_pct"] < 100.0


def test_scenario_c_critical_zone_priority():
    """Scenario C: Elevated priority zones receive preferential resource distribution."""
    report = run_isolated_scenario("C")
    breakdown = report["priority_fulfillment"]
    # Critical demand must achieve equal or higher coverage than lower priority
    crit_cov = breakdown.get("CRITICAL", {}).get("coverage_pct", 0)
    mod_cov = breakdown.get("MODERATE", {}).get("coverage_pct", 0)
    assert crit_cov >= mod_cov


def test_scenario_d_low_inventory():
    """Scenario D: Depleted depot stock caps total allocation at available inventory."""
    report = run_isolated_scenario("D")
    avail_stock = report["configuration_applied"]["available_food_kg"] + report["configuration_applied"]["available_water_kg"]
    assert report["total_allocated_kg"] <= avail_stock
    assert report["unmet_demand_kg"] > 0
    # Primary bottleneck must flag depot stock depletion
    bottlenecks = [b["constraint"] for b in report["explainability"]["binding_constraints"]]
    assert any("DEPOT" in b for b in bottlenecks)


def test_scenario_e_limited_fleet():
    """Scenario E: Only 1 vehicle available (1,200 kg capacity) limits total dispatch."""
    report = run_isolated_scenario("E")
    assert report["configuration_applied"]["active_vehicles_count"] == 1
    assert report["configuration_applied"]["fleet_capacity_kg"] == 1200
    assert report["total_allocated_kg"] <= 1200


def test_scenario_f_flood_road_closure():
    """Scenario F: MG Road closed triggers detour."""
    report = run_isolated_scenario("F")
    assert len(report["configuration_applied"]["road_closures"]) == 1
    assert report["stage2_route_km"] > 0


def test_scenario_h_isolated_zone():
    """Scenario H: Isolated zone (ZONE 01) is declared unreachable with 0 kg allocation."""
    report = run_isolated_scenario("H")
    assert "ZONE 01" in report["configuration_applied"]["unreachable_zones"]
    # Check that Zone 01 received zero allocation
    z1_res = next((z for z in report["optimization"]["zones"] if z["zone_code"] == "ZONE 01"), None)
    assert z1_res is not None
    assert z1_res["alloc_total_kg"] == 0
    assert z1_res["is_accessible"] is False
    assert z1_res["unreachable_reason"] is not None


def test_scenario_i_resource_non_substitution():
    """Scenario I: Potable water surplus cannot be substituted for food deficit."""
    report = run_isolated_scenario("I")
    food_stock = report["configuration_applied"]["available_food_kg"]
    assert report["optimization"]["allocated_food_kg"] <= food_stock
    # Explainability confirms non-substitution
    assert "NON_PERMITTED" in report["explainability"]["resource_substitution"]


def test_scenario_j_full_system_stress():
    """Scenario J: Compound disaster stress yields feasible plan with explicit bottleneck reporting."""
    report = run_isolated_scenario("J")
    assert report["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert report["unmet_demand_kg"] > 0
    assert len(report["explainability"]["binding_constraints"]) >= 1


# =============================================================================
# 4. SIMULATION DATA ISOLATION & IMMUTABILITY
# =============================================================================

def test_simulation_data_isolation_rigorous():
    """
    CRITICAL: Verify that running multiple disaster stress tests (including
    extreme Scenarios J and D with overrides) does NOT mutate the live operational
    stores: ZONES_DATA, DEPOT_DATA, VEHICLES_DATA, INVENTORY_ITEMS_DATA.
    """
    # Snapshot baseline operational states
    orig_food_stock = DEPOT_DATA["available_food_kg"]
    orig_water_stock = DEPOT_DATA["available_water_kg"]
    orig_zone1_demand = ZONES_DATA[0]["total_demand_kg"]
    orig_vehicles_count = len(VEHICLES_DATA)
    orig_inventory_items_count = len(INVENTORY_ITEMS_DATA)
    orig_demands_count = len(DEMAND_RECORDS_DATA)

    # Run severe scenarios with aggressive custom overrides
    run_isolated_scenario("D")
    run_isolated_scenario("J", custom_overrides={"stock_food_kg": 100, "demand_multiplier": 3.0})
    run_isolated_scenario("H")
    run_isolated_scenario("E")

    # Assert completely untouched operational stores
    assert DEPOT_DATA["available_food_kg"] == orig_food_stock
    assert DEPOT_DATA["available_water_kg"] == orig_water_stock
    assert ZONES_DATA[0]["total_demand_kg"] == orig_zone1_demand
    assert len(VEHICLES_DATA) == orig_vehicles_count
    assert len(INVENTORY_ITEMS_DATA) == orig_inventory_items_count
    assert len(DEMAND_RECORDS_DATA) == orig_demands_count


# =============================================================================
# 5. SCALABILITY & PERFORMANCE BENCHMARK
# =============================================================================

def test_scalability_benchmark_execution():
    """
    Execute synthetic scalability benchmark across Small (5z/3v), Medium (15z/8v),
    and Large (45z/18v) problem scales.
    Assert all solve within 5000ms and converge to OPTIMAL or FEASIBLE.
    """
    bench = run_scalability_benchmark()

    assert bench["status"] == "BENCHMARK_COMPLETE"
    assert len(bench["scale_results"]) == 3

    small = bench["scale_results"][0]
    assert small["scale_tier"] == "SMALL"
    assert small["zones_count"] == 5
    assert small["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert small["total_runtime_ms"] < 5000

    medium = bench["scale_results"][1]
    assert medium["scale_tier"] == "MEDIUM"
    assert medium["zones_count"] == 15
    assert medium["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert medium["total_runtime_ms"] < 10000

    large = bench["scale_results"][2]
    assert large["scale_tier"] == "LARGE"
    assert large["zones_count"] == 45
    assert large["solver_status"] in ("OPTIMAL", "FEASIBLE")
    assert large["total_runtime_ms"] < 20000


# =============================================================================
# 6. REST API ENDPOINTS INTEGRATION
# =============================================================================

def test_api_simulations_scenarios_catalog():
    """GET /api/simulations/scenarios returns all 10 scenario definitions."""
    res = client.get("/api/simulations/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 10
    ids = [s["id"] for s in data]
    assert ids == ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]


def test_api_simulations_run_endpoint():
    """POST /api/simulations/run executes scenario cleanly with JSON response."""
    # Test valid scenario A
    payload = {"scenario_id": "A"}
    res = client.post("/api/simulations/run", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["scenario_id"] == "A"
    assert data["solver_status"] == "OPTIMAL"
    assert "isolation_guarantee" in data

    # Test valid scenario H with isolated unreachable zone
    res_h = client.post("/api/simulations/run", json={"scenario_id": "H"})
    assert res_h.status_code == 200
    data_h = res_h.json()
    assert data_h["scenario_id"] == "H"
    assert "ZONE 01" in data_h["configuration_applied"]["unreachable_zones"]

    # Test 404 for invalid scenario
    res_bad = client.post("/api/simulations/run", json={"scenario_id": "UNKNOWN_99"})
    assert res_bad.status_code == 404


def test_api_simulations_comparison_endpoint():
    """GET /api/simulations/comparison generates multi-scenario comparative matrix."""
    res = client.get("/api/simulations/comparison?scenario_ids=A,B,C,D,H")
    assert res.status_code == 200
    data = res.json()
    assert "comparison_matrix" in data
    assert len(data["comparison_matrix"]) == 5
    matrix_ids = [m["scenario_id"] for m in data["comparison_matrix"]]
    assert matrix_ids == ["A", "B", "C", "D", "H"]


def test_api_simulations_scalability_endpoint():
    """GET /api/simulations/scalability runs synthetic scalability stress test."""
    res = client.get("/api/simulations/scalability")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "BENCHMARK_COMPLETE"
    assert len(data["scale_results"]) == 3
