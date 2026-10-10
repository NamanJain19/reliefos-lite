"""
RELIEFOS Lite — Multi-Location Operational Data & Isolation Regression Test Suite.
Validates:
1. Every configured location has genuine operational coverage across all core modules.
2. Strict data isolation: Switching between locations isolates zones, inventory, fleet, shelters, routes, and telemetry.
3. No cross-district leakage: Kamrup Metro data does NOT contaminate Barpeta, Nalbari, Cachar, etc.
4. End-to-end roundtrip test: Kamrup Metro -> Barpeta -> Nalbari -> Cachar -> Kamrup Metro.
5. Location resolution via both query param (?location_id=...) and X-Location-ID HTTP header.
6. Validation of zone-scoped demand requisition creation.
7. Simulation sandboxing preserving live operational stores.
8. AI Copilot context compiling genuinely scoped to selected location.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.location_registry import SUPPORTED_LOCATIONS, DEFAULT_LOCATION_ID, get_location_meta

client = TestClient(app)


def test_location_registry_endpoint():
    """Verify GET /api/locations returns all 9 configured Assam operational districts."""
    res = client.get("/api/locations")
    assert res.status_code == 200
    data = res.json()
    assert data["total_locations"] == 9
    assert data["default_location_id"] == "kamrup_metro"
    loc_ids = [l["id"] for l in data["locations"]]
    expected_all = [
        "kamrup_metro", "kamrup_rural", "barpeta", "nalbari",
        "darrang", "morigaon", "goalpara", "nagaon", "cachar"
    ]
    for exp in expected_all:
        assert exp in loc_ids


def test_kamrup_metro_baseline_experience():
    """Verify default Kamrup Metropolitan data has all micro-zones, depots, and allocations intact."""
    # 1. Dashboard
    res_dash = client.get("/api/dashboard?location_id=kamrup_metro")
    assert res_dash.status_code == 200
    dash = res_dash.json()
    assert dash["location_id"] == "kamrup_metro"
    assert dash["summary"]["operational_zones"] == 5
    assert dash["relief_resource_availability"]["depot_code"] == "DEPOT-GAU-01"

    # 2. Zones
    res_zones = client.get("/api/zones?location_id=kamrup_metro")
    assert res_zones.status_code == 200
    zones = res_zones.json()
    assert len(zones) == 5
    codes = [z["code"] for z in zones]
    assert "ZONE 01" in codes
    assert "ZONE 05" in codes

    # 3. Inventory
    res_inv = client.get("/api/inventory?location_id=kamrup_metro")
    assert res_inv.status_code == 200
    inv = res_inv.json()
    assert inv["depot"]["code"] == "DEPOT-GAU-01"
    assert len(inv["items"]) > 0

    # 4. Shelters & Vehicles
    res_shelters = client.get("/api/shelters?location_id=kamrup_metro")
    assert res_shelters.status_code == 200
    assert len(res_shelters.json()) == 2

    res_veh = client.get("/api/vehicles?location_id=kamrup_metro")
    assert res_veh.status_code == 200
    assert len(res_veh.json()) == 3

    # 5. Allocations
    res_alloc = client.get("/api/allocations?location_id=kamrup_metro")
    assert res_alloc.status_code == 200


def test_barpeta_operational_coverage_and_isolation():
    """Verify Barpeta receives genuine Barpeta revenue circles, depot, fleet, and zero Kamrup Metro leakage."""
    headers = {"X-Location-ID": "barpeta"}

    # 1. Dashboard
    res_dash = client.get("/api/dashboard", headers=headers)
    assert res_dash.status_code == 200
    dash = res_dash.json()
    assert dash["location_id"] == "barpeta"
    assert dash["district_name"] == "Barpeta"
    assert dash["summary"]["operational_zones"] == 4
    assert dash["summary"]["fleet_vehicles_total"] == 3
    assert dash["relief_resource_availability"]["depot_code"] == "DEPOT-BRP-01"

    # 2. Zones: Barpeta Revenue Circles
    res_zones = client.get("/api/zones", headers=headers)
    assert res_zones.status_code == 200
    zones = res_zones.json()
    assert len(zones) == 4
    codes = [z["code"] for z in zones]
    assert "BRP-Z01" in codes
    assert "BRP-Z04" in codes
    # Strictly zero Kamrup Metro zones
    assert "ZONE 01" not in codes
    assert "ZONE 05" not in codes

    # 3. Inventory: Barpeta DDMA Warehouse
    res_inv = client.get("/api/inventory", headers=headers)
    assert res_inv.status_code == 200
    inv = res_inv.json()
    assert inv["depot"]["code"] == "DEPOT-BRP-01"
    assert "Barpeta" in inv["depot"]["name"]
    assert len(inv["items"]) >= 5
    assert inv["metrics"]["total_stock_kg"] > 0
    # Zero Kamrup Metro Sarusajai SKUs
    skus = [i["sku"] for i in inv["items"]]
    assert "FOOD-RICE-001" not in skus
    assert "BRP-FOOD-001" in skus

    # 4. Shelters & Vehicles
    res_shelters = client.get("/api/shelters", headers=headers)
    assert res_shelters.status_code == 200
    shelters = res_shelters.json()
    assert len(shelters) == 3
    assert any("Mandia" in s["name"] or "Barpeta" in s["name"] for s in shelters)

    res_veh = client.get("/api/vehicles", headers=headers)
    assert res_veh.status_code == 200
    vehicles = res_veh.json()
    assert len(vehicles) == 3
    assert any("BRP" in v["code"] for v in vehicles)

    # 5. Allocations: Google OR-Tools CP-SAT solves Barpeta circles
    res_alloc = client.get("/api/allocations", headers=headers)
    assert res_alloc.status_code == 200
    alloc = res_alloc.json()
    assert alloc["status"] == "OPTIMAL"
    assert alloc["location_id"] == "barpeta"
    assert len(alloc["zones"]) == 4

    # 6. Routes: Barpeta convoy paths
    res_routes = client.get("/api/routes", headers=headers)
    assert res_routes.status_code == 200
    routes = res_routes.json()
    assert routes["status"] == "CALCULATED"
    assert routes["district_name"] == "Barpeta"
    assert len(routes["routes"]) == 2

    # 7. GIS GeoJSON: Closed polygons for Barpeta Revenue Circles
    res_gis = client.get("/api/gis/zones.geojson", headers=headers)
    assert res_gis.status_code == 200
    geojson = res_gis.json()
    assert len(geojson["features"]) == 4
    for feat in geojson["features"]:
        assert feat["geometry"]["type"] == "Polygon"
        # First and last coordinate in exterior ring must match (RFC 7946 closed ring)
        ring = feat["geometry"]["coordinates"][0]
        assert ring[0] == ring[-1]

    # 8. Flood Telemetry: Isolates Beki gauge
    res_flood = client.get("/api/flood", headers=headers)
    assert res_flood.status_code == 200
    flood = res_flood.json()
    assert "Barpeta" in flood["region"]
    gauge_ids = [g["station_id"] for g in flood["gauges"]]
    assert "CWC-BEKI-06" in gauge_ids
    assert "CWC-PANDU-01" not in gauge_ids


def test_nalbari_operational_coverage_and_isolation():
    """Verify Nalbari receives Nalbari hydrometric gauges, revenue circles, and zero Kamrup Metro leakage."""
    headers = {"X-Location-ID": "nalbari"}

    # 1. Flood telemetry
    res_flood = client.get("/api/flood", headers=headers)
    assert res_flood.status_code == 200
    flood = res_flood.json()
    assert "Nalbari" in flood["region"]
    gauge_ids = [g["station_id"] for g in flood["gauges"]]
    assert "CWC-PAGLADIYA-07" in gauge_ids
    assert "CWC-PANDU-01" not in gauge_ids
    assert "CWC-BEKI-04" not in gauge_ids

    # 2. Zones
    res_zones = client.get("/api/zones", headers=headers)
    assert res_zones.status_code == 200
    zones = res_zones.json()
    assert len(zones) == 4
    codes = [z["code"] for z in zones]
    assert "NLB-Z01" in codes
    assert "NLB-Z04" in codes

    # 3. Demands
    res_demands = client.get("/api/demands", headers=headers)
    assert res_demands.status_code == 200
    assert len(res_demands.json()) >= 3


def test_cachar_operational_coverage_and_isolation():
    """Verify Cachar receives Barak River hydrology, Silchar depot, and Cachar circles."""
    headers = {"X-Location-ID": "cachar"}

    # 1. Flood telemetry: Barak basin
    res_flood = client.get("/api/flood", headers=headers)
    assert res_flood.status_code == 200
    flood = res_flood.json()
    assert "Cachar" in flood["region"]
    assert "Barak" in flood["river_basin"]
    gauge_ids = [g["station_id"] for g in flood["gauges"]]
    assert "CWC-BARAK-10" in gauge_ids
    assert "CWC-PANDU-01" not in gauge_ids

    # 2. Zones: Cachar revenue circles
    res_zones = client.get("/api/zones", headers=headers)
    assert res_zones.status_code == 200
    zones = res_zones.json()
    assert len(zones) == 4
    codes = [z["code"] for z in zones]
    assert "CCH-Z01" in codes
    assert "CCH-Z04" in codes
    names = [z["name"] for z in zones]
    assert any("Silchar" in n for n in names)
    assert any("Lakhipur" in n for n in names)

    # 3. Depot: Silchar godown
    res_inv = client.get("/api/inventory", headers=headers)
    assert res_inv.status_code == 200
    inv = res_inv.json()
    assert inv["depot"]["code"] == "CCH-DEPOT-01"
    assert "Silchar" in inv["depot"]["name"]


def test_location_switching_roundtrip():
    """Verify sequence: Kamrup Metro -> Barpeta -> Nalbari -> Cachar -> Kamrup Metro returns correct data at each step."""
    # Step 1: Kamrup Metro
    res1 = client.get("/api/zones?location_id=kamrup_metro")
    assert len(res1.json()) == 5
    assert res1.json()[0]["code"] == "ZONE 01"

    # Step 2: Barpeta
    res2 = client.get("/api/zones?location_id=barpeta")
    assert len(res2.json()) == 4
    assert res2.json()[0]["code"] == "BRP-Z01"

    # Step 3: Nalbari
    res3 = client.get("/api/zones?location_id=nalbari")
    assert len(res3.json()) == 4
    assert res3.json()[0]["code"] == "NLB-Z01"

    # Step 4: Cachar
    res4 = client.get("/api/zones?location_id=cachar")
    assert len(res4.json()) == 4
    assert res4.json()[0]["code"] == "CCH-Z01"

    # Step 5: Back to Kamrup Metro
    res5 = client.get("/api/zones?location_id=kamrup_metro")
    assert len(res5.json()) == 5
    assert res5.json()[0]["code"] == "ZONE 01"


def test_zone_scoped_demand_validation():
    """Verify creating a demand validates against the active district's zones."""
    # 1. Invalid zone code for Barpeta (submitting Kamrup Metro's ZONE 01 to Barpeta)
    res_bad = client.post("/api/demands?location_id=barpeta", json={
        "zone_code": "ZONE 01",
        "resource_type": "Food Supplies",
        "requested_qty": 500,
        "unit": "kg",
        "priority": "HIGH"
    })
    assert res_bad.status_code == 400
    assert "Invalid zone_code" in res_bad.json()["detail"]

    # 2. Valid Barpeta zone code
    res_good = client.post("/api/demands?location_id=barpeta", json={
        "zone_code": "BRP-Z01",
        "resource_type": "Food Supplies",
        "requested_qty": 350,
        "unit": "kg",
        "priority": "CRITICAL"
    })
    assert res_good.status_code == 200
    assert res_good.json()["demand"]["zone_code"] == "BRP-Z01"


def test_simulation_does_not_mutate_live_records():
    """Verify executing what-if simulation does not alter operational records."""
    initial_inv = client.get("/api/inventory?location_id=kamrup_metro").json()
    initial_stock = initial_inv["metrics"]["total_stock_kg"]

    # Run simulation scenario
    sim_res = client.post("/api/simulations/run", json={"scenario_id": "A"})
    assert sim_res.status_code == 200

    after_inv = client.get("/api/inventory?location_id=kamrup_metro").json()
    after_stock = after_inv["metrics"]["total_stock_kg"]
    assert initial_stock == after_stock, "Simulation mutated live inventory!"


def test_ai_copilot_context_isolation():
    """Verify AI context aggregation compiles only target district telemetry."""
    # Preview Barpeta context
    res_ctx = client.get("/api/ai/context/preview?location_id=barpeta")
    assert res_ctx.status_code == 200
    preview = res_ctx.json()
    items = {item["domain"]: item for item in preview["context_items"]}

    assert "Barpeta" in items["zones"]["title"]
    assert "Barpeta" in items["inventory"]["title"]
    assert "DEPOT-BRP-01" in items["inventory"]["raw_metrics"]["depot_code"]
    assert "Barpeta" in items["demands"]["title"]
    assert "Barpeta" in items["roads"]["title"]


def test_what_if_scenario_location_scoping():
    """Verify What-If scenario executes on target district operational context."""
    # 1. Barpeta What-If simulation
    res_barpeta = client.post("/api/logistics-advisor/what-if", json={
        "scenario_title": "Barpeta Flash Inundation Test",
        "location_id": "barpeta",
        "demand_multiplier": 1.2
    })
    assert res_barpeta.status_code == 200
    data_brp = res_barpeta.json()
    assert data_brp["database_mutated"] is False
    zone_codes_brp = [z["zone_code"] for z in data_brp["zones"]]
    assert "BRP-Z01" in zone_codes_brp
    assert "ZONE 01" not in zone_codes_brp

    # 2. Cachar What-If simulation
    res_cachar = client.post("/api/logistics-advisor/what-if", json={
        "scenario_title": "Barak Valley Riverfront Surge",
        "location_id": "cachar",
        "demand_multiplier": 1.1
    })
    assert res_cachar.status_code == 200
    data_cch = res_cachar.json()
    assert data_cch["database_mutated"] is False
    zone_codes_cch = [z["zone_code"] for z in data_cch["zones"]]
    assert "CCH-Z01" in zone_codes_cch
    assert "BRP-Z01" not in zone_codes_cch


def test_individual_zone_endpoint_resolution():
    """Verify /api/zones/{zone_code} accurately resolves district circles and prevents cross-district leakage."""
    # Barpeta circle
    res_brp = client.get("/api/zones/BRP-Z01?location_id=barpeta")
    assert res_brp.status_code == 200
    assert "Barpeta Sadar" in res_brp.json()["name"]

    # Nalbari circle
    res_nlb = client.get("/api/zones/NLB-Z01?location_id=nalbari")
    assert res_nlb.status_code == 200
    assert "Nalbari Sadar" in res_nlb.json()["name"]

    # Cachar circle
    res_cch = client.get("/api/zones/CCH-Z01?location_id=cachar")
    assert res_cch.status_code == 200
    assert "Silchar Sadar" in res_cch.json()["name"]

    # Isolation check: Querying Kamrup Metro zone code from Barpeta must return 404
    res_leak = client.get("/api/zones/ZONE 01?location_id=barpeta")
    assert res_leak.status_code == 404

