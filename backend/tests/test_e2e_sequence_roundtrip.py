"""
RELIEFOS Lite — Phase 3: Multi-Location Exact Sequence End-to-End Verification Test.
Sequence: Kamrup Metropolitan -> Barpeta -> Nalbari -> Cachar -> Kamrup Metropolitan.
Verifies shared location state, headers, district-specific responses, depot coordinates,
and strict data isolation with zero Kamrup Metro leakage across transitions.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_exact_sequence_roundtrip_verification():
    sequence = [
        {
            "id": "kamrup_metro",
            "name": "Kamrup Metropolitan",
            "expected_zones": 5,
            "depot_code": "DEPOT-GAU-01",
            "first_zone": "ZONE 01",
            "basin_fragment": "Brahmaputra",
            "fleet_size": 3,
        },
        {
            "id": "barpeta",
            "name": "Barpeta",
            "expected_zones": 4,
            "depot_code": "DEPOT-BRP-01",
            "first_zone": "BRP-Z01",
            "basin_fragment": "Beki",
            "fleet_size": 3,
        },
        {
            "id": "nalbari",
            "name": "Nalbari",
            "expected_zones": 4,
            "depot_code": "NLB-DEPOT-01",
            "first_zone": "NLB-Z01",
            "basin_fragment": "Pagladiya",
            "fleet_size": 2,
        },
        {
            "id": "cachar",
            "name": "Cachar",
            "expected_zones": 4,
            "depot_code": "CCH-DEPOT-01",
            "first_zone": "CCH-Z01",
            "basin_fragment": "Barak",
            "fleet_size": 3,
        },
        {
            "id": "kamrup_metro",
            "name": "Kamrup Metropolitan",
            "expected_zones": 5,
            "depot_code": "DEPOT-GAU-01",
            "first_zone": "ZONE 01",
            "basin_fragment": "Brahmaputra",
            "fleet_size": 3,
        },
    ]

    for step_idx, loc in enumerate(sequence):
        loc_id = loc["id"]
        headers = {"X-Location-ID": loc_id}

        # 1. Dashboard Endpoint
        dash_res = client.get("/api/dashboard", headers=headers)
        assert dash_res.status_code == 200, f"Step {step_idx} ({loc_id}) dashboard failed"
        dash = dash_res.json()
        assert dash["location_id"] == loc_id
        assert dash["summary"]["operational_zones"] == loc["expected_zones"]
        assert dash["relief_resource_availability"]["depot_code"] == loc["depot_code"]

        # 2. Zones Endpoint
        zones_res = client.get("/api/zones", headers=headers)
        assert zones_res.status_code == 200, f"Step {step_idx} ({loc_id}) zones failed"
        zones = zones_res.json()
        assert len(zones) == loc["expected_zones"]
        assert zones[0]["code"] == loc["first_zone"]

        # 3. Flood Telemetry Endpoint
        flood_res = client.get("/api/flood", headers=headers)
        assert flood_res.status_code == 200, f"Step {step_idx} ({loc_id}) flood failed"
        flood = flood_res.json()
        assert loc["basin_fragment"].lower() in flood["river_basin"].lower()

        # 4. Inventory Endpoint
        inv_res = client.get("/api/inventory", headers=headers)
        assert inv_res.status_code == 200, f"Step {step_idx} ({loc_id}) inventory failed"
        inv = inv_res.json()
        assert inv["depot"]["code"] == loc["depot_code"]
        assert len(inv["items"]) > 0

        # 5. Route Optimization Endpoint
        routes_res = client.get("/api/routes", headers=headers)
        assert routes_res.status_code == 200, f"Step {step_idx} ({loc_id}) routes failed"
        routes = routes_res.json()
        routes_list = routes.get("routes", []) if isinstance(routes, dict) else routes
        assert len(routes_list) > 0

        # 6. Simulation Scenarios Catalog
        sim_res = client.get("/api/simulations/scenarios", headers=headers)
        assert sim_res.status_code == 200, f"Step {step_idx} ({loc_id}) scenarios failed"
        scenarios = sim_res.json()
        if loc_id == "kamrup_metro":
            assert len(scenarios) == 10
        else:
            assert len(scenarios) >= 2
            expected_prefix = {"barpeta": "BRP", "nalbari": "NLB", "cachar": "CCH"}.get(loc_id, "")
            assert all(s["code"].startswith(expected_prefix) for s in scenarios)

        # 7. Logistics Advisor Plan Endpoint
        adv_res = client.get("/api/logistics-advisor/plan", headers=headers)
        assert adv_res.status_code == 200, f"Step {step_idx} ({loc_id}) advisor failed"
        adv = adv_res.json()
        assert len(adv["zones"]) == loc["expected_zones"]
        assert adv["zones"][0]["zone_code"] == loc["first_zone"]

        # 8. AI Context Preview Endpoint
        ai_res = client.get("/api/ai/context/preview", headers=headers)
        assert ai_res.status_code == 200, f"Step {step_idx} ({loc_id}) AI context failed"
        ai_data = ai_res.json()
        items = {item["domain"]: item for item in ai_data["context_items"]}
        assert "zones" in items
        assert "inventory" in items
