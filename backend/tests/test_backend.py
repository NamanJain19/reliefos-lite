from fastapi.testclient import TestClient
from app.main import app
from app.services.optimization.solver import run_lexicographic_optimization, get_baseline_comparison
from app.services.routing.router import build_guwahati_road_graph, compute_fleet_optimized_routes
import networkx as nx

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "RELIEFOS Lite" in data["system"]
    assert "Kamrup Metropolitan" in data["region"]


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["mode"] in ["OPERATIONAL_LIVE", "DEMO (SIMULATED)"]
    assert "ONLINE" in data["telemetry"]


def test_dashboard_endpoint():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["operational_zones"] == 5
    assert data["summary"]["fleet_vehicles_total"] == 3
    assert "relief_resource_availability" in data
    assert len(data["demand_vs_supply"]) == 5
    assert len(data["operational_alerts"]) >= 4


def test_zones_endpoint():
    response = client.get("/api/zones")
    assert response.status_code == 200
    zones = response.json()
    assert len(zones) == 5
    assert any(z["code"] == "ZONE 01" for z in zones)


def test_zone_by_code_valid_and_invalid():
    # Valid zone
    res_valid = client.get("/api/zones/ZONE 01")
    assert res_valid.status_code == 200
    assert res_valid.json()["code"] == "ZONE 01"

    # Valid zone with alternate format
    res_slug = client.get("/api/zones/zone-02")
    assert res_slug.status_code == 200

    # Non-existent zone
    res_404 = client.get("/api/zones/ZONE-999-NONEXISTENT")
    assert res_404.status_code == 404
    assert res_404.json()["detail"] == "Zone not found"


def test_flood_telemetry_endpoint():
    response = client.get("/api/flood")
    assert response.status_code == 200
    data = response.json()
    assert "Brahmaputra Basin" in data["river_basin"]
    assert data["current_weather"]["discharge_pandu_cumecs"] > 30000
    assert len(data["gauges"]) >= 3


def test_shelters_and_vehicles():
    shelters_res = client.get("/api/shelters")
    assert shelters_res.status_code == 200
    assert len(shelters_res.json()) >= 2

    vehicles_res = client.get("/api/vehicles")
    assert vehicles_res.status_code == 200
    assert len(vehicles_res.json()) == 3


def test_inventory_and_add_stock():
    # Fetch inventory
    get_res = client.get("/api/inventory")
    assert get_res.status_code == 200
    inv = get_res.json()
    assert "depot" in inv
    assert len(inv["items"]) >= 5

    # Add new consignment
    payload = {
        "sku": "TEST-SKU-99",
        "name": "Audit Test Emergency Rations",
        "category": "Food Supplies",
        "quantity": 250,
        "unit": "kg"
    }
    post_res = client.post("/api/inventory/add", json=payload)
    assert post_res.status_code == 200
    assert post_res.json()["item"]["sku"] == "TEST-SKU-99"
    assert post_res.json()["item"]["available_qty"] == 250


def test_demands_and_create_demand():
    # Fetch demands
    get_res = client.get("/api/demands")
    assert get_res.status_code == 200
    demands = get_res.json()
    assert len(demands) >= 5

    # Create demand
    payload = {
        "zone_code": "ZONE 01",
        "resource_type": "Drinking Water",
        "requested_qty": 300,
        "unit": "L",
        "priority": "HIGH"
    }
    post_res = client.post("/api/demands", json=payload)
    assert post_res.status_code == 200
    created = post_res.json()["demand"]
    assert created["zone_code"] == "ZONE 01"
    assert created["requested_qty"] == 300
    assert created["status"] == "PENDING"


def test_allocations_ortools_solver():
    response = client.post("/api/allocations/optimize", json={"prioritize_water": True})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("OPTIMAL", "FEASIBLE")
    assert data["proposed_allocation_kg"] > 0
    assert len(data["zones"]) == 5
    assert data["solver_runtime_ms"] > 0


def test_allocations_comparison():
    res = client.get("/api/allocations/comparison")
    assert res.status_code == 200
    data = res.json()
    assert "baseline" in data
    assert "optimized" in data
    assert data["optimized"]["penalty_reduction_pct"] > 0
    assert data["optimized"]["distance_savings_pct"] > 0


def test_routes_networkx_router():
    response = client.get("/api/routes")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPTIMAL_ROUTING_COMPLETED"
    assert len(data["routes"]) == 3
    assert data["inundations_evaded"] >= 1
    assert data["total_transit_distance_km"] < data["baseline_distance_km"]


def test_routes_recalculate():
    res = client.post("/api/routes/recalculate")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPTIMAL_ROUTING_COMPLETED"
    assert len(data["routes"]) == 3


def test_simulations_endpoint():
    res = client.get("/api/simulations")
    assert res.status_code == 200
    data = res.json()
    assert "active_solver" in data
    assert len(data["scenarios"]) == 10
    assert len(data["benchmark_table"]) >= 5


def test_data_sources_endpoint():
    res = client.get("/api/data-sources")
    assert res.status_code == 200
    data = res.json()
    assert "pipeline_status" in data
    assert len(data["streams"]) >= 5
    assert len(data["provenance_classes"]) == 6


def test_settings_endpoint():
    res = client.get("/api/settings")
    assert res.status_code == 200
    data = res.json()
    assert data["workspace"]["name"] == "RELIEFOS Lite"
    assert "solver_guardrails" in data


def test_cors_preflight_headers():
    headers = {
        "Origin": "http://localhost:3012",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type",
    }
    response = client.options("/api/allocations/optimize", headers=headers)
    assert response.status_code == 200
    assert "http://localhost:3012" in response.headers.get("access-control-allow-origin", "")


def test_ortools_solver_unit():
    """Unit test for lexicographic MILP solver logic."""
    res = run_lexicographic_optimization(prioritize_water=True)
    assert res["status"] in ("OPTIMAL", "FEASIBLE")
    assert res["proposed_allocation_kg"] <= res["total_available_stock_kg"]

    # Verify high priority zones receive allocations
    z01 = next(z for z in res["zones"] if z["zone_code"] == "ZONE 01")
    assert z01["total_alloc_kg"] > 0


def test_networkx_graph_routing_unit():
    """Unit test for NetworkX road graph and shortest path with flood detour."""
    G_clear = build_guwahati_road_graph(include_flood_blockage=False)
    G_blocked = build_guwahati_road_graph(include_flood_blockage=True)

    # Path to Bharalumukh with clear road vs blocked MG road
    path_clear = nx.shortest_path(G_clear, source="DEPOT", target="BHARALU_JCT", weight="length_km")
    path_blocked = nx.shortest_path(G_blocked, source="DEPOT", target="BHARALU_JCT", weight="length_km")

    # With blockage, route must detour via ARYA_NAGAR_JCT (AT Road)
    assert "ARYA_NAGAR_JCT" in path_blocked
    assert "MG_ROAD_WEST" not in path_blocked


def test_simulation_inventory_isolation():
    """
    CRITICAL SAFETY AUDIT: Verify that executing a simulation or optimization run
    does NOT decrement or mutate physical warehouse inventory records.
    """
    # 1. Snapshot initial inventory
    res_before = client.get("/api/inventory")
    assert res_before.status_code == 200
    inv_before = res_before.json()
    items_before = {i["sku"]: (i["available_qty"], i["reserved_qty"]) for i in inv_before["items"]}
    total_stock_before = inv_before["metrics"]["total_stock_kg"]

    # 2. Run simulation & optimization cycles with different configurations
    sim_res1 = client.post("/api/allocations/optimize", json={"prioritize_water": True})
    assert sim_res1.status_code == 200

    sim_res2 = client.post("/api/allocations/optimize", json={"prioritize_water": False})
    assert sim_res2.status_code == 200

    sim_reports = client.get("/api/simulations")
    assert sim_reports.status_code == 200

    # 3. Snapshot inventory after simulations
    res_after = client.get("/api/inventory")
    assert res_after.status_code == 200
    inv_after = res_after.json()
    items_after = {i["sku"]: (i["available_qty"], i["reserved_qty"]) for i in inv_after["items"]}
    total_stock_after = inv_after["metrics"]["total_stock_kg"]

    # 4. Strict assertions: inventory MUST remain 100% identical
    assert total_stock_before == total_stock_after, "Simulation mutated total warehouse stock!"
    for sku, (avail_before, resv_before) in items_before.items():
        assert sku in items_after, f"SKU {sku} disappeared after simulation!"
        avail_after, resv_after = items_after[sku]
        assert avail_before == avail_after, f"SKU {sku} available stock mutated from {avail_before} to {avail_after}!"
        assert resv_before == resv_after, f"SKU {sku} reserved stock mutated from {resv_before} to {resv_after}!"


def test_inventory_crud_extended():
    """Verify complete CRUD lifecycle, validations, and rejection of invalid data."""
    # 1. Read single valid item
    res_get = client.get("/api/inventory/FOOD-001")
    assert res_get.status_code == 200
    assert res_get.json()["sku"] == "FOOD-001"

    # 2. Read non-existent item -> 404
    res_get_404 = client.get("/api/inventory/NON-EXISTENT-SKU")
    assert res_get_404.status_code == 404

    # 3. Reject negative and zero quantity -> 422
    res_neg = client.post("/api/inventory/add", json={
        "sku": "NEG-001",
        "name": "Invalid Negative Stock",
        "category": "Food Supplies",
        "quantity": -50,
        "unit": "kg"
    })
    assert res_neg.status_code == 422

    res_zero = client.post("/api/inventory/add", json={
        "sku": "ZERO-001",
        "name": "Invalid Zero Stock",
        "category": "Food Supplies",
        "quantity": 0,
        "unit": "kg"
    })
    assert res_zero.status_code == 422

    # 4. Reject empty name -> 422
    res_empty_name = client.post("/api/inventory/add", json={
        "sku": "NONAME-001",
        "name": "",
        "category": "Food Supplies",
        "quantity": 100,
        "unit": "kg"
    })
    assert res_empty_name.status_code == 422

    # 5. Add unique consignment
    test_sku = "TEST-CONSIGN-01"
    res_create = client.post("/api/inventory/add", json={
        "sku": test_sku,
        "name": "Test Emergency High Energy Bars",
        "category": "Packaged Food",
        "quantity": 300,
        "unit": "kg"
    })
    assert res_create.status_code == 200

    # 6. Reject duplicate SKU -> 409
    res_dup = client.post("/api/inventory/add", json={
        "sku": test_sku,
        "name": "Duplicate Consignment",
        "category": "Packaged Food",
        "quantity": 100,
        "unit": "kg"
    })
    assert res_dup.status_code == 409

    # 7. Update item via PUT
    res_update = client.put(f"/api/inventory/{test_sku}", json={
        "name": "Updated High Energy Bars (Fortified)",
        "available_qty": 350
    })
    assert res_update.status_code == 200
    assert res_update.json()["item"]["available_qty"] == 350

    # 8. Delete unreserved item
    res_delete = client.delete(f"/api/inventory/{test_sku}")
    assert res_delete.status_code == 200

    # 9. Verify deletion -> 404
    res_after_del = client.get(f"/api/inventory/{test_sku}")
    assert res_after_del.status_code == 404

    # 10. Reject deletion of item with reserved buffer -> 400
    res_del_reserved = client.delete("/api/inventory/FOOD-001")
    assert res_del_reserved.status_code == 400
    assert "reserved buffer" in res_del_reserved.json()["detail"]


def test_demand_management_extended():
    """Verify demand validations, status transitions, and single-record retrieval."""
    # 1. Fetch single demand record
    res_get = client.get("/api/demands/DEM-2024-001")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == "DEM-2024-001"

    # 2. Non-existent demand -> 404
    res_get_404 = client.get("/api/demands/DEM-NON-EXISTENT")
    assert res_get_404.status_code == 404

    # 3. Reject negative quantity -> 422
    res_neg = client.post("/api/demands", json={
        "zone_code": "ZONE 01",
        "resource_type": "Food Supplies",
        "requested_qty": -100,
        "unit": "kg",
        "priority": "HIGH"
    })
    assert res_neg.status_code == 422

    # 4. Reject invalid zone code -> 400
    res_bad_zone = client.post("/api/demands", json={
        "zone_code": "ZONE 99 INVALID",
        "resource_type": "Food Supplies",
        "requested_qty": 200,
        "unit": "kg",
        "priority": "HIGH"
    })
    assert res_bad_zone.status_code == 400

    # 5. Reject invalid priority -> 400
    res_bad_pri = client.post("/api/demands", json={
        "zone_code": "ZONE 01",
        "resource_type": "Food Supplies",
        "requested_qty": 200,
        "unit": "kg",
        "priority": "ULTRA_CRITICAL_INVALID"
    })
    assert res_bad_pri.status_code == 400

    # 6. Create valid demand
    res_create = client.post("/api/demands", json={
        "zone_code": "ZONE 03",
        "resource_type": "Potable Water",
        "requested_qty": 450,
        "unit": "L",
        "priority": "CRITICAL"
    })
    assert res_create.status_code == 200
    created_id = res_create.json()["demand"]["id"]

    # 7. Update status to APPROVED
    res_status = client.patch(f"/api/demands/{created_id}/status", json={"status": "APPROVED"})
    assert res_status.status_code == 200
    assert res_status.json()["demand"]["status"] == "APPROVED"

    # 8. Reject invalid status -> 400
    res_bad_status = client.patch(f"/api/demands/{created_id}/status", json={"status": "INVALID_STATUS"})
    assert res_bad_status.status_code == 400


def test_solver_deterministic_and_boundary_cases():
    """Verify solver output against manually calculated small reference scenarios."""
    # Scenario A: Demand exceeds available stock
    custom_zone = [{
        "code": "ZONE 01",
        "name": "North Guwahati",
        "food_demand_kg": 500,
        "water_demand_kg": 400,
        "total_demand_kg": 900,
        "severity_weight": 10.0,
        "risk_tier": "CRITICAL"
    }]
    custom_depot = {
        "available_food_kg": 300,
        "available_water_kg": 200
    }
    custom_vehicle = [{
        "code": "VH-01",
        "max_capacity_kg": 1000
    }]

    result = run_lexicographic_optimization(
        zones=custom_zone,
        depot=custom_depot,
        vehicles=custom_vehicle,
        prioritize_water=True
    )
    assert result["status"] == "OPTIMAL"
    # Allocation cannot exceed available stock
    assert result["proposed_allocation_kg"] == 500  # 300 food + 200 water
    assert result["projected_deficit_kg"] == 400   # 900 demand - 500 alloc
    assert result["zones"][0]["alloc_food_kg"] == 300
    assert result["zones"][0]["alloc_water_kg"] == 200

    # Scenario B: Stock exceeds demand
    surplus_depot = {
        "available_food_kg": 1000,
        "available_water_kg": 1000
    }
    result_surplus = run_lexicographic_optimization(
        zones=custom_zone,
        depot=surplus_depot,
        vehicles=custom_vehicle,
        prioritize_water=True
    )
    assert result_surplus["status"] == "OPTIMAL"
    assert result_surplus["proposed_allocation_kg"] == 900  # Full demand satisfied
    assert result_surplus["projected_deficit_kg"] == 0
    assert result_surplus["coverage_ratio_pct"] == 100.0


def test_routing_graph_unreachable_handling():
    """Verify NetworkX handling when a destination is disconnected from depot."""
    G = build_guwahati_road_graph(include_flood_blockage=False)
    # Remove all edges to North Guwahati
    G.remove_edge("AMINGAON_NORTH", "ZONE_01_DEST")

    assert not nx.has_path(G, "DEPOT", "ZONE_01_DEST")
    try:
        nx.shortest_path(G, "DEPOT", "ZONE_01_DEST")
        assert False, "Should have raised NetworkXNoPath"
    except nx.NetworkXNoPath:
        pass  # Expected behavior


def test_database_persistence_integrity():
    """Verify that SQLite database tables contain persistent records."""
    from app.core.database import SessionLocal
    from app.models.domain import ZoneModel, DepotModel, VehicleModel, InventoryItemModel, DemandModel

    db = SessionLocal()
    try:
        assert db.query(ZoneModel).count() == 5, "Database must persist 5 monitored zones"
        assert db.query(DepotModel).count() == 1, "Database must persist Sarusajai central depot"
        assert db.query(VehicleModel).count() == 3, "Database must persist 3 relief vehicles"
        assert db.query(InventoryItemModel).count() >= 5, "Database must persist inventory stock records"
        assert db.query(DemandModel).count() >= 5, "Database must persist demand records"

        # Verify specific record fields
        z01 = db.query(ZoneModel).filter(ZoneModel.code == "ZONE 01").first()
        assert z01 is not None
        assert z01.risk_level == "CRITICAL"
        assert 26.0 < z01.latitude < 27.0
        assert 91.0 < z01.longitude < 92.0
    finally:
        db.close()

