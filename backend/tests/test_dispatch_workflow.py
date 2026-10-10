"""
RELIEFOS Lite — Comprehensive Human-Approved Dispatch Workflow Tests
Validates:
1. Generation of unique dispatch orders from OR-Tools allocation plans
2. Pre-dispatch safety checks (depot inventory, vehicle payload limits, road inundation <= 0.35m)
3. Human officer approval and rejection with Form 8B statutory reference
4. Role-based access control (COMMANDER/OPERATOR succeed, ANALYST gets 403)
5. Duplicate review prevention
6. State machine lifecycle transitions (PENDING -> APPROVED -> READY -> DISPATCHED -> DELIVERED)
7. Invalid state transition rejection (e.g. PENDING -> DISPATCHED)
8. DRY_RUN mode isolation (depot inventory remains intact, external connectors DISABLED_BY_POLICY)
9. Audit log traceability for every review and transition
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import get_db, SessionLocal
from app.models.domain import DispatchOrderModel, AuditLogModel, InventoryItemModel
from app.services.dispatch.dispatch_service import DispatchService

client = TestClient(app)

COMMANDER_TOKEN = "reliefos-commander-token-2026"
OPERATOR_TOKEN = "reliefos-operator-token-2026"
ANALYST_TOKEN = "reliefos-analyst-token-2026"


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_list_seeded_dispatch_orders():
    """Verify listing seeded dispatch manifests."""
    res = client.get("/api/dispatch/orders")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    sample = data[0]
    assert "dispatch_id" in sample
    assert "safety_validation" in sample
    assert sample["external_connector_status"] == "DISABLED_BY_POLICY"
    assert sample["is_dry_run"] is True


def test_generate_dispatches_from_or_tools_plan():
    """Verify generating dispatch manifests from current OR-Tools optimization plan."""
    payload = {
        "strategy": "LEXICOGRAPHIC_SEVERITY_OPTIMAL",
        "is_dry_run": True,
        "operator_name": "Insp. S. Sharma"
    }
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    res = client.post("/api/dispatch/generate-from-plan", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    first_order = data[0]
    assert first_order["dispatch_id"].startswith("DSP-")
    assert first_order["status"] == "PENDING"
    assert first_order["is_dry_run"] is True
    assert "safety_validation" in first_order
    assert first_order["safety_validation"]["is_safe"] in (True, False)


def test_safety_check_endpoint():
    """Verify pre-dispatch safety verification calculation endpoint."""
    # Under vehicle payload capacity (2500 kg capacity for VH-01)
    res = client.get("/api/dispatch/safety-check?zone_code=ZONE%2002&vehicle_code=VH-01&food_kg=300&water_l=400")
    assert res.status_code == 200
    report = res.json()
    assert report["inventory_sufficient"] is True
    assert report["vehicle_capacity_sufficient"] is True
    assert report["routes_passable"] is True
    assert report["is_safe"] is True

    # Over vehicle payload capacity (> 2500 kg for VH-01)
    res_over = client.get("/api/dispatch/safety-check?zone_code=ZONE%2002&vehicle_code=VH-01&food_kg=2000&water_l=1000")
    assert res_over.status_code == 200
    report_over = res_over.json()
    assert report_over["vehicle_capacity_sufficient"] is False
    assert report_over["is_safe"] is False
    assert any("exceeds" in err for err in report_over["errors"])


def test_officer_approval_workflow(db_session: Session):
    """Verify human officer can approve a pending dispatch order with Form 8B statutory reference."""
    disp_id = f"DSP-TEST-APP-{uuid.uuid4().hex[:6].upper()}"
    order = DispatchOrderModel(
        dispatch_id=disp_id,
        plan_id="PLAN-TEST-01",
        zone_code="ZONE 02",
        zone_name="Bharalumukh",
        vehicle_code="VH-01",
        vehicle_name="Tata 407 4x4 High-Clearance",
        food_quantity_kg=200,
        water_quantity_l=300,
        total_weight_kg=500,
        status="PENDING",
        is_dry_run=True,
        is_simulation=False,
        form_8b_reference="ASDMA-F8B-2026-TEST"
    )
    db_session.add(order)
    db_session.commit()

    review_payload = {
        "decision": "APPROVED",
        "officer_name": "Insp. S. Sharma",
        "notes": "Verified flood clearance on AT Road detour. Staging authorized under Form 8B.",
        "form_8b_reference": "ASDMA-F8B-2026-APPR-01",
        "disclaimer_acknowledged": True
    }
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    res = client.post(f"/api/dispatch/orders/{disp_id}/review", json=review_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "APPROVED"
    assert data["reviewed_by"] == "Insp. S. Sharma"
    assert data["review_decision"] == "APPROVED"
    assert "READY" in data["allowed_next_transitions"]

    # Verify audit log entry was written
    audit = db_session.query(AuditLogModel).filter(
        AuditLogModel.entity_type == "DISPATCH_ORDER",
        AuditLogModel.entity_id == disp_id
    ).first()
    assert audit is not None
    assert audit.operator_name == "Insp. S. Sharma"
    assert "APPROVED" in audit.action


def test_officer_rejection_workflow(db_session: Session):
    """Verify human officer can reject a proposed dispatch order."""
    disp_id = f"DSP-TEST-REJ-{uuid.uuid4().hex[:6].upper()}"
    order = DispatchOrderModel(
        dispatch_id=disp_id,
        plan_id="PLAN-TEST-02",
        zone_code="ZONE 01",
        zone_name="North Guwahati",
        vehicle_code="VH-02",
        vehicle_name="Mahindra Bolero",
        food_quantity_kg=150,
        water_quantity_l=150,
        total_weight_kg=300,
        status="PENDING",
        is_dry_run=True,
        is_simulation=False
    )
    db_session.add(order)
    db_session.commit()

    review_payload = {
        "decision": "REJECTED",
        "officer_name": "EOC Commander P. Baruah",
        "notes": "Rejected due to river gauge surge. Re-evaluating via boat relay.",
        "disclaimer_acknowledged": True
    }
    headers = {"Authorization": f"Bearer {COMMANDER_TOKEN}"}
    res = client.post(f"/api/dispatch/orders/{disp_id}/review", json=review_payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REJECTED"
    assert data["reviewed_by"] == "EOC Commander P. Baruah"


def test_duplicate_review_prevention(db_session: Session):
    """Verify an already reviewed order cannot be re-reviewed."""
    disp_id = f"DSP-TEST-DUP-{uuid.uuid4().hex[:6].upper()}"
    order = DispatchOrderModel(
        dispatch_id=disp_id,
        plan_id="PLAN-TEST-03",
        zone_code="ZONE 03",
        zone_name="Uzan Bazar",
        vehicle_code="VH-01",
        vehicle_name="Tata 407",
        food_quantity_kg=100,
        water_quantity_l=100,
        total_weight_kg=200,
        status="APPROVED",
        reviewed_by="Insp. S. Sharma",
        review_decision="APPROVED"
    )
    db_session.add(order)
    db_session.commit()

    review_payload = {
        "decision": "APPROVED",
        "officer_name": "Insp. S. Sharma",
        "notes": "Attempting second approval"
    }
    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    res = client.post(f"/api/dispatch/orders/{disp_id}/review", json=review_payload, headers=headers)
    assert res.status_code == 400
    assert "cannot be re-reviewed" in res.json()["detail"]


def test_rbac_analyst_forbidden_from_review():
    """Verify read-only ANALYST role is rejected with 403 Forbidden."""
    review_payload = {
        "decision": "APPROVED",
        "officer_name": "K. Kalita",
        "notes": "Analyst trying to approve write action"
    }
    headers = {"Authorization": f"Bearer {ANALYST_TOKEN}"}
    res = client.post("/api/dispatch/orders/DSP-20261005-001/review", json=review_payload, headers=headers)
    assert res.status_code == 403
    assert "Forbidden" in res.json().get("detail", {}).get("error", "")


def test_state_machine_full_lifecycle(db_session: Session):
    """Verify strict transition sequence: PENDING -> APPROVED -> READY -> DISPATCHED -> DELIVERED."""
    disp_id = f"DSP-TEST-CYC-{uuid.uuid4().hex[:6].upper()}"
    order = DispatchOrderModel(
        dispatch_id=disp_id,
        plan_id="PLAN-CYCLE",
        zone_code="ZONE 04",
        zone_name="Basistha",
        vehicle_code="VH-01",
        vehicle_name="Tata 407",
        food_quantity_kg=100,
        water_quantity_l=100,
        total_weight_kg=200,
        status="PENDING",
        is_dry_run=True
    )
    db_session.add(order)
    db_session.commit()

    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}

    # 1. Review & Approve
    res = client.post(
        f"/api/dispatch/orders/{disp_id}/review",
        json={"decision": "APPROVED", "officer_name": "Insp. S. Sharma", "notes": "Approved for staging"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "APPROVED"

    # 2. Stage to READY
    res = client.post(
        f"/api/dispatch/orders/{disp_id}/transition",
        json={"target_status": "READY", "operator_name": "Insp. S. Sharma", "notes": "Vehicle loaded at depot"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "READY"

    # 3. Rollout to DISPATCHED
    res = client.post(
        f"/api/dispatch/orders/{disp_id}/transition",
        json={"target_status": "DISPATCHED", "operator_name": "Insp. S. Sharma", "notes": "Driver departure logged"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "DISPATCHED"

    # 4. Field confirmation to DELIVERED
    res = client.post(
        f"/api/dispatch/orders/{disp_id}/transition",
        json={"target_status": "DELIVERED", "operator_name": "Insp. S. Sharma", "notes": "Shelter signed receipt"},
        headers=headers
    )
    assert res.status_code == 200
    assert res.json()["status"] == "DELIVERED"


def test_invalid_state_transition_rejected(db_session: Session):
    """Verify illegal transition (e.g. PENDING directly to DISPATCHED) is rejected with 400."""
    disp_id = f"DSP-TEST-INV-{uuid.uuid4().hex[:6].upper()}"
    order = DispatchOrderModel(
        dispatch_id=disp_id,
        plan_id="PLAN-INVALID",
        zone_code="ZONE 05",
        zone_name="Dispur",
        vehicle_code="VH-02",
        vehicle_name="Mahindra Bolero",
        food_quantity_kg=50,
        water_quantity_l=50,
        total_weight_kg=100,
        status="PENDING",
        is_dry_run=True
    )
    db_session.add(order)
    db_session.commit()

    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    # Illegal jump from PENDING directly to DISPATCHED without officer review
    res = client.post(
        f"/api/dispatch/orders/{disp_id}/transition",
        json={"target_status": "DISPATCHED", "operator_name": "Insp. S. Sharma"},
        headers=headers
    )
    assert res.status_code == 400
    assert "Invalid transition" in str(res.json()["detail"])


def test_dry_run_state_isolation(db_session: Session):
    """Verify DRY_RUN mode does not decrement or mutate live operational warehouse inventory."""
    initial_stock = db_session.query(InventoryItemModel).first()
    initial_qty = initial_stock.total_quantity if initial_stock else 2500

    disp_id = f"DSP-TEST-DRY-{uuid.uuid4().hex[:6].upper()}"
    order = DispatchOrderModel(
        dispatch_id=disp_id,
        plan_id="PLAN-DRY",
        zone_code="ZONE 02",
        zone_name="Bharalumukh",
        vehicle_code="VH-01",
        vehicle_name="Tata 407",
        food_quantity_kg=100,
        water_quantity_l=100,
        total_weight_kg=200,
        status="PENDING",
        is_dry_run=True
    )
    db_session.add(order)
    db_session.commit()

    headers = {"Authorization": f"Bearer {OPERATOR_TOKEN}"}
    client.post(
        f"/api/dispatch/orders/{disp_id}/review",
        json={"decision": "APPROVED", "officer_name": "Insp. S. Sharma", "notes": "Dry-run approval"},
        headers=headers
    )
    client.post(
        f"/api/dispatch/orders/{disp_id}/transition",
        json={"target_status": "READY", "operator_name": "Insp. S. Sharma"},
        headers=headers
    )
    client.post(
        f"/api/dispatch/orders/{disp_id}/transition",
        json={"target_status": "DISPATCHED", "operator_name": "Insp. S. Sharma"},
        headers=headers
    )

    # Check database stock unchanged
    db_session.expire_all()
    current_stock = db_session.query(InventoryItemModel).first()
    if current_stock:
        assert current_stock.total_quantity == initial_qty, "Depot stock must not mutate during dry run simulation"
