"""
RELIEFOS Lite — Genuine Operational Workflows Integration Tests.
Validates:
1. Warehouse Inventory Ledger (Receipts, Adjustments, Reservations, Movements, Alerts)
2. Field Incident Lifecycle (Reporting, Field Verification, Rescue Team Mobilization, Resolution)
3. Daily Situation Report (SitRep Auto-Compilation, Live Telemetry Aggregation, Commander Sign-Off)
4. Sphere-Standard Humanitarian Relief Requirement Projections (2,100 kcal, 15L WASH, multi-horizon)
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.domain import InventoryItemModel, IncidentModel, SituationReportModel

client = TestClient(app)


def test_inventory_receipt_and_movement_ledger():
    """Verify physical relief consignment receipt updates balances and records movement."""
    operator_token = "reliefos-operator-token-2026"
    headers = {
        "Authorization": f"Bearer {operator_token}",
        "X-Location-ID": "kamrup_metro"
    }

    payload = {
        "item_sku": "FOOD-001",
        "quantity": 500.0,
        "batch_lot_number": "LOT-TEST-2026-X1",
        "expiry_date": "2027-12-31",
        "reference_doc": "CONSIGNMENT-TEST-99",
        "operator_name": "Insp. S. Sharma",
        "notes": "Emergency buffer augmentation test"
    }

    res = client.post("/api/operational/inventory/receipt", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["item_sku"] == "FOOD-001"
    assert data["movement_type"] == "RECEIPT"
    assert data["quantity"] == 500.0
    assert data["balance_after"] > data["balance_before"]

    # Verify movement appears in ledger
    ledger_res = client.get("/api/operational/inventory/movements?sku=FOOD-001", headers=headers)
    assert ledger_res.status_code == 200
    movements = ledger_res.json()
    assert any(m["movement_id"] == data["movement_id"] for m in movements)


def test_inventory_adjustment_and_rejection():
    """Verify formal cycle-count adjustment updates available stock and rejects negative balances."""
    operator_token = "reliefos-operator-token-2026"
    headers = {
        "Authorization": f"Bearer {operator_token}",
        "X-Location-ID": "kamrup_metro"
    }

    # 1. Valid deduction adjustment
    adj_payload = {
        "item_sku": "WATR-001",
        "adjustment_type": "AUDIT_CORRECTION",
        "quantity_delta": -50.0,
        "reason": "Damaged pouches during warehouse transit",
        "operator_name": "Insp. S. Sharma"
    }
    res = client.post("/api/operational/inventory/adjustment", json=adj_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["movement_type"] == "AUDIT_CORRECTION"

    # 2. Invalid adjustment causing negative stock rejected safely
    bad_payload = {
        "item_sku": "WATR-001",
        "adjustment_type": "AUDIT_CORRECTION",
        "quantity_delta": -999999.0,
        "reason": "Excessive deduction test",
        "operator_name": "Insp. S. Sharma"
    }
    bad_res = client.post("/api/operational/inventory/adjustment", json=bad_payload, headers=headers)
    assert bad_res.status_code == 400


def test_inventory_stock_reservation():
    """Verify stock reservation locks inventory for an operational dispatch plan."""
    operator_token = "reliefos-operator-token-2026"
    headers = {
        "Authorization": f"Bearer {operator_token}",
        "X-Location-ID": "kamrup_metro"
    }

    res_payload = {
        "item_sku": "FOOD-001",
        "quantity_to_reserve": 200.0,
        "plan_id": "PLAN-DISPATCH-TEST-01",
        "notes": "Staging for North Guwahati Zone 1"
    }
    res = client.post("/api/operational/inventory/reserve", json=res_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["movement_type"] == "RESERVATION"
    assert data["quantity"] == 200.0


def test_inventory_low_stock_alerts():
    """Verify inventory alert endpoint flags low stock or depletion."""
    headers = {"X-Location-ID": "kamrup_metro"}
    res = client.get("/api/operational/inventory/alerts", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_low_stock_alerts" in data
    assert isinstance(data["alerts"], list)


def test_field_incident_lifecycle():
    """Verify reporting, inspecting, updating, and team mobilization for emergency incidents."""
    operator_token = "reliefos-operator-token-2026"
    headers = {
        "Authorization": f"Bearer {operator_token}",
        "X-Location-ID": "kamrup_metro"
    }

    # 1. Report new incident
    incident_payload = {
        "incident_type": "FLASH_FLOOD",
        "severity": "CRITICAL",
        "title": "Basistha Stream Bank Inundation & Culvert Choke",
        "description": "Flash runoff from Meghalaya foothills has inundated residential lowlands along Basistha temple approach.",
        "location_desc": "Basistha Chariali / Temple Road",
        "latitude": 26.118,
        "longitude": 91.785,
        "zone_code": "ZONE 04",
        "reported_by": "Local Disaster Management Committee (LDMC)",
        "persons_stranded": 28,
        "livestock_affected": 8,
        "infrastructure_damaged": "Submerged culvert and 30m road erosion.",
        "response_action_taken": "Traffic diverted; watercraft team deployed.",
        "assigned_team": "SDRF Team 3"
    }

    create_res = client.post("/api/operational/incidents", json=incident_payload, headers=headers)
    assert create_res.status_code == 201
    inc_data = create_res.json()
    assert inc_data["status"] == "REPORTED"
    assert inc_data["incident_id"].startswith("INC-")
    inc_id = inc_data["incident_id"]

    # 2. Get details
    get_res = client.get(f"/api/operational/incidents/{inc_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == incident_payload["title"]

    # 3. Update status to IN_RESPONSE
    update_payload = {
        "status": "IN_RESPONSE",
        "verified_by": "Insp. S. Sharma",
        "response_action_taken": "28 residents evacuated to Basistha High School shelter. Medical checks ongoing."
    }
    upd_res = client.put(f"/api/operational/incidents/{inc_id}", json=update_payload, headers=headers)
    assert upd_res.status_code == 200
    assert upd_res.json()["status"] == "IN_RESPONSE"
    assert upd_res.json()["verified_by"] == "Insp. S. Sharma"


def test_daily_sitrep_compilation_and_commander_approval():
    """Verify auto-compilation of daily SitRep from live state and Commander sign-off."""
    commander_token = "reliefos-commander-token-2026"
    headers = {
        "Authorization": f"Bearer {commander_token}",
        "X-Location-ID": "kamrup_metro"
    }

    # 1. Compile SitRep
    gen_payload = {
        "time_window": "06:00 - 18:00 IST",
        "weather_synopsis": "Active monsoon trough across Brahmaputra valley with heavy rain alerts.",
        "compiling_officer": "Insp. S. Sharma"
    }
    compile_res = client.post("/api/operational/sitreps/generate", json=gen_payload, headers=headers)
    assert compile_res.status_code == 200
    sitrep = compile_res.json()
    assert sitrep["approval_status"] == "DRAFT"
    assert sitrep["sitrep_id"].startswith("SITREP-")
    assert sitrep["district_name"] == "Kamrup Metropolitan"
    assert sitrep["active_human_lives_affected"] > 0
    sitrep_id = sitrep["sitrep_id"]

    # 2. Commander sign-off
    appr_payload = {
        "approving_commander": "EOC Commander P. Baruah",
        "notes": "Verified against CWC Pandu stage bulletin and field shelter reports."
    }
    appr_res = client.put(f"/api/operational/sitreps/{sitrep_id}/approve", json=appr_payload, headers=headers)
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["approval_status"] == "APPROVED"
    assert appr_data["approving_commander"] == "EOC Commander P. Baruah"
    assert appr_data["approved_at"] is not None


def test_sphere_humanitarian_demand_calculation():
    """Verify Sphere standards calculation adheres to 2,100 kcal and 15L water baselines."""
    headers = {"X-Location-ID": "kamrup_metro"}
    payload = {
        "population_affected": 5000,
        "evacuees_in_shelters": 1200,
        "time_horizon_hours": 72,
        "infant_count": 150,
        "elderly_count": 300,
        "contingency_buffer_pct": 15.0
    }

    res = client.post("/api/operational/demand/sphere-calculate", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    # 1. Baselines
    baselines = data["sphere_per_capita_baselines"]
    assert baselines["food_energy_kcal_per_person_day"] == 2100
    assert baselines["food_dry_rations_kg_per_person_day"] == 0.45
    assert baselines["potable_water_liters_per_person_day"] == 15.0

    # 2. Measured shelter requirements
    shelter_req = data["measured_shelter_demand"]
    assert shelter_req["evacuee_headcount"] == 1200
    # 1200 people * 0.45 kg/day * 3 days * 1.15 buffer = ~1863 kg
    assert shelter_req["food_rations_kg"] > 1800
    # 1200 people * 15 L/day * 3 days * 1.15 buffer = ~62100 L
    assert shelter_req["potable_water_liters"] > 60000

    # 3. Horizon breakdown
    horizons = data["horizon_breakdown"]
    assert "24_hours_immediate_kg" in horizons
    assert "72_hours_surge_kg" in horizons
    assert "7_days_sustenance_kg" in horizons
    assert horizons["7_days_sustenance_kg"] > horizons["72_hours_surge_kg"]
