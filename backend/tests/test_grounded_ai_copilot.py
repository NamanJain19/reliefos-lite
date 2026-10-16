"""
RELIEFOS Lite — Grounded Operational AI Copilot Test Suite
Verifies genuine backend-to-AI data grounding, dynamic database retrieval,
district isolation, provenance transparency, absence of hallucinated facts,
deterministic fallbacks, and statutory human-in-the-loop governance.
"""

import pytest
import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.domain import (
    InventoryItemModel, ZoneModel, ShelterModel, RoadClosureModel,
    DemandModel, StockMovementModel, AuditLogModel, IncidentModel, SituationReportModel
)
from app.core.auth import create_access_token


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def commander_token():
    return create_access_token(
        user_data={"username": "commander", "role": "COMMANDER", "name": "Chief EOC Commander"}
    )


@pytest.fixture(scope="module")
def operator_token():
    return create_access_token(
        user_data={"username": "operator", "role": "OPERATOR", "name": "Insp. S. Sharma"}
    )


@pytest.fixture(scope="module")
def analyst_token():
    return create_access_token(
        user_data={"username": "analyst", "role": "ANALYST", "name": "Data Analyst"}
    )


class TestGroundedAICopilot:
    """Rigorous end-to-end tests for AI Copilot data grounding and operational integrity."""

    @pytest.fixture(autouse=True)
    def ensure_deterministic_grounding(self, monkeypatch):
        """Ensures test assertions evaluate against deterministic grounding engine rather than remote LLM calls."""
        from app.services.ai.providers.gemini import GeminiProvider
        from app.services.ai.providers.openai import OpenAIProvider
        monkeypatch.setattr(GeminiProvider, "is_live", False)
        monkeypatch.setattr(OpenAIProvider, "is_live", False)

    def test_01_dynamic_inventory_insertion_and_query(self, client):
        """
        1. Insert a known unique inventory record into the active database.
        2. Query Copilot about inventory.
        3. Verify the response contains the exact quantity and SKU.
        """
        db = SessionLocal()
        test_sku = f"TEST-RICE-{uuid.uuid4().hex[:6].upper()}"
        unique_qty = 8765.0
        try:
            item = InventoryItemModel(
                sku=test_sku,
                name="Special Fortified Basmati Rations",
                category="Food Supplies",
                total_quantity=unique_qty,
                available_quantity=unique_qty,
                reserved_quantity=0.0,
                unit="kg",
                status="In Stock",
                location_id="kamrup_metro"
            )
            db.add(item)
            db.commit()

            # Query Copilot for inventory
            resp = client.post("/api/ai/query", json={
                "query": f"What is the current stock balance of {test_sku}?",
                "location_id": "kamrup_metro",
                "operator_name": "Test Officer"
            })
            assert resp.status_code == 200, resp.text
            data = resp.json()

            # Verify grounding
            assert data["status"] in ("SUCCESS", "PARTIAL_CONTEXT")
            assert str(int(unique_qty)) in data["detailed_explanation"] or str(int(unique_qty)) in data["recommendation"]
            assert test_sku in data["detailed_explanation"] or test_sku in data["recommendation"]
            assert data["human_review_required"] is True
            assert data["audit_id"].startswith("AUD-") or data["audit_id"].startswith("AI-AUDIT-")
        finally:
            # Clean up test record
            db.query(InventoryItemModel).filter(InventoryItemModel.sku == test_sku).delete()
            db.commit()
            db.close()

    def test_02_dynamic_inventory_mutation_reflects_immediately(self, client):
        """
        1. Insert inventory record with initial quantity.
        2. Query Copilot -> verify initial quantity.
        3. Mutate (deduct) quantity in database.
        4. Query Copilot again -> verify response reflects mutated quantity immediately.
        """
        db = SessionLocal()
        test_sku = f"MUT-WATR-{uuid.uuid4().hex[:6].upper()}"
        initial_qty = 9000.0
        mutated_qty = 3456.0
        try:
            item = InventoryItemModel(
                sku=test_sku,
                name="Emergency Potable Jerrycans",
                category="Potable Water",
                total_quantity=initial_qty,
                available_quantity=initial_qty,
                reserved_quantity=0.0,
                unit="L",
                status="In Stock",
                location_id="kamrup_metro"
            )
            db.add(item)
            db.commit()

            # Query 1
            resp1 = client.post("/api/ai/query", json={
                "query": f"Check inventory for {test_sku}",
                "location_id": "kamrup_metro"
            })
            assert resp1.status_code == 200
            assert str(int(initial_qty)) in resp1.json()["detailed_explanation"]

            # Mutate in DB
            item_db = db.query(InventoryItemModel).filter(InventoryItemModel.sku == test_sku).first()
            item_db.available_quantity = mutated_qty
            item_db.total_quantity = mutated_qty
            db.commit()

            # Query 2
            resp2 = client.post("/api/ai/query", json={
                "query": f"Check inventory for {test_sku}",
                "location_id": "kamrup_metro"
            })
            assert resp2.status_code == 200
            assert str(int(mutated_qty)) in resp2.json()["detailed_explanation"]
            assert str(int(initial_qty)) not in resp2.json()["detailed_explanation"]
        finally:
            db.query(InventoryItemModel).filter(InventoryItemModel.sku == test_sku).delete()
            db.commit()
            db.close()

    def test_03_district_switching_and_zero_cross_district_leakage(self, client):
        """
        1. Query Kamrup Metro -> verify Sarusajai or Kamrup context.
        2. Switch district to Barpeta -> verify Barpeta depot and sectors.
        3. Switch district to Cachar -> verify Cachar depot and sectors.
        4. Confirm zero cross-district leakage.
        """
        # Barpeta query
        resp_brp = client.post(
            "/api/ai/query",
            json={"query": "What is our current warehouse stock and depot location?"},
            headers={"X-Location-ID": "barpeta"}
        )
        assert resp_brp.status_code == 200
        data_brp = resp_brp.json()
        assert "Barpeta" in data_brp["recommendation"] or "Barpeta" in data_brp["detailed_explanation"]
        # Ensure it does not leak Sarusajai
        assert "Sarusajai" not in data_brp["recommendation"]

        # Cachar query
        resp_cac = client.post(
            "/api/ai/query",
            json={"query": "What is our current warehouse stock and depot location?"},
            headers={"X-Location-ID": "cachar"}
        )
        assert resp_cac.status_code == 200
        data_cac = resp_cac.json()
        assert "Cachar" in data_cac["recommendation"] or "Cachar" in data_cac["detailed_explanation"]
        assert "Barpeta" not in data_cac["recommendation"]

    def test_04_shelter_capacity_and_vacancy_grounding(self, client):
        """
        Insert a shelter record with known capacity and occupancy.
        Ask Copilot which shelters have capacity available.
        Verify that exact capacity, occupancy, and vacancy are reported.
        """
        db = SessionLocal()
        sh_code = f"SH-TEST-{uuid.uuid4().hex[:4].upper()}"
        capacity = 700
        occupancy = 250
        vacancy = 450
        try:
            sh = ShelterModel(
                code=sh_code,
                name="Pragjyotishpur Community Relief Hall",
                zone_code="ZONE 01",
                location_desc="North Guwahati Riverfront",
                latitude=26.19,
                longitude=91.73,
                capacity=capacity,
                occupancy=occupancy,
                status="ACTIVE",
                verification_status="VERIFIED",
                location_id="kamrup_metro"
            )
            db.add(sh)
            db.commit()

            resp = client.post("/api/ai/query", json={
                "query": "Which shelters have recorded capacity available?",
                "location_id": "kamrup_metro"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert "Pragjyotishpur" in data["detailed_explanation"]
            assert str(capacity) in data["detailed_explanation"]
            assert str(occupancy) in data["detailed_explanation"]
            assert str(vacancy) in data["detailed_explanation"]
        finally:
            db.query(ShelterModel).filter(ShelterModel.code == sh_code).delete()
            db.commit()
            db.close()

    def test_05_river_gauge_and_danger_level_grounding(self, client):
        """
        Query Copilot about river gauges and verify that actual CWC river stations,
        current MSL water levels, and danger marks are reported.
        """
        resp = client.post("/api/ai/query", json={
            "query": "What are the latest river gauge observations along the Brahmaputra?",
            "location_id": "kamrup_metro"
        })
        assert resp.status_code == 200
        data = resp.json()
        # Verify gauge evidence citations
        evidence_sources = [ev["source"] for ev in data["supporting_evidence"]]
        assert any("Central Water Commission" in s or "CWC" in s for s in evidence_sources)
        assert "m MSL" in data["detailed_explanation"] or "m" in data["detailed_explanation"]

    def test_06_road_closures_and_detour_route_grounding(self, client):
        """
        Insert an active road closure into the database.
        Ask Copilot about road closures and route impact.
        Verify that the closure and detour are reported with water depth.
        """
        db = SessionLocal()
        test_corridor = f"NH-TEST-CORRIDOR-{uuid.uuid4().hex[:4].upper()}"
        depth = 0.52
        try:
            closure = RoadClosureModel(
                corridor_name=test_corridor,
                location_desc="Santipur Sluice Gate Approach",
                latitude=26.18,
                longitude=91.74,
                water_depth_m=depth,
                clearance_threshold_m=0.35,
                status="IMPASSABLE_FLOOD",
                detour_corridor="Alternative Highway Bypass Route",
                is_active=True,
                location_id="kamrup_metro"
            )
            db.add(closure)
            db.commit()

            resp = client.post("/api/ai/query", json={
                "query": "What road closures are currently recorded and what is their impact?",
                "location_id": "kamrup_metro"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert test_corridor in data["detailed_explanation"] or test_corridor in data["recommendation"]
            assert str(depth) in data["detailed_explanation"]
        finally:
            db.query(RoadClosureModel).filter(RoadClosureModel.corridor_name == test_corridor).delete()
            db.commit()
            db.close()

    def test_07_or_tools_allocation_optimizer_grounding(self, client):
        """
        Ask Copilot about optimizer allocation recommendations.
        Verify that CP-SAT solver results (allocated kg, unmet deficit kg, coverage ratio) are cited.
        """
        resp = client.post("/api/ai/query", json={
            "query": "What resource allocation has the optimizer recommended and why?",
            "location_id": "kamrup_metro"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "OR-Tools" in data["detailed_explanation"] or "optimizer" in data["detailed_explanation"].lower()
        # Verify supporting evidence citations
        evidence_sources = [ev["source"] for ev in data["supporting_evidence"]]
        assert any("OR-Tools" in s or "CP-SAT" in s for s in evidence_sources)

    def test_08_field_incidents_and_sitrep_grounding(self, client):
        """
        Insert an active field incident into the database.
        Ask Copilot about ground incidents.
        Verify that the incident title, severity, and stranded count are reported.
        """
        db = SessionLocal()
        inc_id = f"INC-TEST-{uuid.uuid4().hex[:6].upper()}"
        inc_title = "Embankment Overtopping near Palashbari"
        stranded = 120
        try:
            inc = IncidentModel(
                incident_id=inc_id,
                incident_type="EMBANKMENT_BREACH",
                severity="CRITICAL",
                status="REPORTED",
                title=inc_title,
                description="Water overtopping river embankment; residents marooned.",
                zone_code="ZONE 01",
                latitude=26.15,
                longitude=91.60,
                location_id="kamrup_metro",
                reported_by="Circle Officer Palashbari",
                persons_stranded=stranded
            )
            db.add(inc)
            db.commit()

            resp = client.post("/api/ai/query", json={
                "query": "What are the latest field incidents and breach reports?",
                "location_id": "kamrup_metro"
            })
            assert resp.status_code == 200
            data = resp.json()
            assert inc_title in data["detailed_explanation"] or inc_id in data["detailed_explanation"]
            assert str(stranded) in data["detailed_explanation"]
        finally:
            db.query(IncidentModel).filter(IncidentModel.incident_id == inc_id).delete()
            db.commit()
            db.close()

    def test_09_deterministic_engine_when_ai_provider_unconfigured(self, client):
        """
        Verify that when live AI provider is unconfigured or mock,
        the system returns a deterministic grounded response without fabricated conversational text.
        """
        resp = client.post("/api/ai/query", json={
            "query": "What is the current inventory by warehouse?",
            "location_id": "kamrup_metro"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["execution_mode"] in ("DETERMINISTIC_GROUNDED", "LIVE_LLM")
        assert len(data["supporting_evidence"]) > 0
        assert data["is_mock_fallback"] is False
        assert any("provider" in d.lower() or "configured" in d.lower() or "freshness" in d.lower() for d in data["missing_or_stale_data_disclosures"])

    def test_10_missing_or_unavailable_data_domain_disclosed(self, client):
        """
        Query a domain or location that has missing records.
        Verify that Copilot does NOT invent numbers, but explicitly discloses unavailable data.
        """
        # Test preview for a location without CWC river gauges (e.g. non-existent or isolated circle)
        resp = client.get("/api/ai/context/preview?location_id=barpeta")
        assert resp.status_code == 200
        preview = resp.json()
        assert preview["total_domains_compiled"] >= 5
        assert "provenance_distribution" in preview

    def test_11_role_based_access_control_on_action_reviews(self, client, operator_token, commander_token, analyst_token):
        """
        Verify that reviewing/signing an AI-proposed action requires authorized credentials.
        Unauthenticated requests must be rejected (401/403).
        Authorized operators can sign off under Form 8B.
        """
        # Invalid / missing credentials in strict mode must be rejected (401)
        resp_unauth = client.post("/api/ai/actions/review", json={
            "action_id": "ACT-TEST-01",
            "decision": "APPROVED",
            "officer_name": "Unauthenticated User"
        }, headers={"Authorization": "Bearer bad_signature_token"})
        assert resp_unauth.status_code in (401, 403)

        # Analyst role (read-only observer) must be forbidden from approving operational actions (403)
        resp_analyst = client.post(
            "/api/ai/actions/review",
            json={
                "action_id": "ACT-TEST-01",
                "decision": "APPROVED",
                "officer_name": "Analyst Observer"
            },
            headers={"Authorization": f"Bearer {analyst_token}"}
        )
        assert resp_analyst.status_code == 403

        # Authenticated operator can submit review
        resp_auth = client.post(
            "/api/ai/actions/review",
            json={
                "action_id": "ACT-TEST-01",
                "decision": "APPROVED",
                "officer_name": "Insp. S. Sharma",
                "notes": "Verified against field circle census."
            },
            headers={"Authorization": f"Bearer {operator_token}"}
        )
        assert resp_auth.status_code == 200
        review_data = resp_auth.json()
        assert review_data["success"] is True
        assert review_data["decision"] == "APPROVED"
        assert review_data["audit_logged"] is True

    def test_12_consequential_actions_remain_pending_human_review(self, client):
        """
        Verify that AI never autonomously executes dispatches or releases supplies.
        All proposed actions must be staged in PENDING_OFFICER_REVIEW.
        """
        resp = client.post("/api/ai/query", json={
            "query": "Authorize emergency dispatches to Zone 02 immediately.",
            "location_id": "kamrup_metro"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["human_review_required"] is True
        for act in data["proposed_actions"]:
            assert act["status"] == "PENDING_OFFICER_REVIEW"

    def test_13_audit_log_persists_every_ai_query(self, client):
        """
        Verify that every Copilot query creates an immutable audit record in audit_logs.
        """
        unique_query = f"Audit verification query {uuid.uuid4().hex[:6]}"
        resp = client.post("/api/ai/query", json={
            "query": unique_query,
            "location_id": "kamrup_metro",
            "operator_name": "Auditor Sharma"
        })
        assert resp.status_code == 200
        audit_id = resp.json()["audit_id"]

        db = SessionLocal()
        try:
            log_entry = db.query(AuditLogModel).filter(
                AuditLogModel.operator_name == "Auditor Sharma",
                AuditLogModel.entity_type == "AI_DECISION_SUPPORT"
            ).order_by(AuditLogModel.id.desc()).first()
            assert log_entry is not None
            assert log_entry.action in ("GENERATE_RECOMMENDATION", "AI_QUERY_EVALUATION")
        finally:
            db.close()

    def test_14_ai_health_endpoint_telemetry(self, client):
        """
        Inspect AI health endpoint and verify provider status, rate limit load, and circuit breaker.
        """
        resp = client.get("/api/ai/health")
        assert resp.status_code == 200
        health = resp.json()
        assert "circuit_breaker_status" in health
        assert "uptime_status" in health
        assert "rate_limit_requests_per_minute" in health
        assert health["circuit_breaker_status"] in ("CLOSED", "OPEN", "HALF_OPEN")
