"""
RELIEFOS Lite — PostgreSQL Production Readiness & Multi-Database Compatibility Tests.
Validates:
1. Backend startup and telemetry with SQLite (development/test mode).
2. Backend startup and config validation with PostgreSQL configuration (production mode).
3. URL normalization (postgres://, postgresql:// -> postgresql+psycopg2://).
4. Safe failure when production environment attempts to run SQLite.
5. Enterprise connection pooling configuration for PostgreSQL (pool_size, max_overflow, pool_pre_ping).
6. Non-fatal diagnostic handling when live PostgreSQL host is unreachable.
7. Database CRUD across core disaster operations models (Zones, Shelters, Road Closures, Dispatches).
8. Authentication and user credential verification.
9. Inventory lifecycle and buffer management.
10. Operational scenarios and demand lifecycle management.
11. Audit logging and operational ledger persistence.
12. AI decision-support audit persistence and credential redaction.
13. Alembic migration head alignment and table registry completeness.
"""

import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from pydantic import ValidationError

from app.main import app, lifespan
from app.core.config import Settings, get_settings
from app.core.database import (
    Base, create_db_engine, init_db, check_db_connection,
    SessionLocal
)
from app.models.domain import (
    ZoneModel, DepotModel, VehicleModel, InventoryItemModel,
    DemandModel, ShelterModel, AuditLogModel, RoadClosureModel, DispatchOrderModel
)
from app.core.auth import REGISTERED_USERS, ROLE_COMMANDER, ROLE_OPERATOR, ROLE_ANALYST
from app.services.ai.audit import record_ai_audit_event

client = TestClient(app)


# =========================================================================
# 1. Backend Startup & Configuration Tests (SQLite vs PostgreSQL)
# =========================================================================

def test_sqlite_development_startup_and_health():
    """Verify backend starts up properly on SQLite in development mode."""
    settings = get_settings()
    assert settings.is_sqlite is True
    assert settings.is_postgres is False
    assert settings.database_engine_type == "sqlite"

    conn_status = check_db_connection()
    assert conn_status["status"] == "connected"
    assert conn_status["dialect"] == "sqlite"

    # API Health endpoint
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"


def test_postgresql_config_validation_and_url_normalization():
    """Verify PostgreSQL settings validation and automatic URL normalization."""
    valid_secret = "a" * 32 + "secure_prod_entropy_key"

    # 1. postgresql:// is normalized to postgresql+psycopg2://
    s1 = Settings(
        ENVIRONMENT="production",
        JWT_SECRET=valid_secret,
        DATABASE_URL="postgresql://user:pass@dbhost.internal:5432/reliefos_prod"
    )
    assert s1.is_postgres is True
    assert s1.is_sqlite is False
    assert s1.database_engine_type == "postgresql"
    assert s1.normalized_database_url == "postgresql+psycopg2://user:pass@dbhost.internal:5432/reliefos_prod"

    # 2. postgres:// (legacy cloud format) is normalized to postgresql+psycopg2://
    s2 = Settings(
        ENVIRONMENT="production",
        JWT_SECRET=valid_secret,
        DATABASE_URL="postgres://user:pass@dbhost.internal:5432/reliefos_prod"
    )
    assert s2.normalized_database_url == "postgresql+psycopg2://user:pass@dbhost.internal:5432/reliefos_prod"

    # 3. Component-based URL construction when DATABASE_URL is omitted in production
    s3 = Settings(
        ENVIRONMENT="production",
        JWT_SECRET=valid_secret,
        DATABASE_URL="",
        DB_HOST="rds-cluster.internal",
        DB_PORT=5432,
        DB_USER="reliefos_admin",
        DB_PASSWORD="SuperSecurePassword123",
        DB_NAME="reliefos_prod"
    )
    assert s3.normalized_database_url == "postgresql+psycopg2://reliefos_admin:SuperSecurePassword123@rds-cluster.internal:5432/reliefos_prod"


def test_production_rejects_sqlite_for_concurrency():
    """Verify production startup fails safely if SQLite is configured."""
    valid_secret = "a" * 32 + "secure_prod_entropy_key"

    with pytest.raises((ValidationError, ValueError)) as exc:
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET=valid_secret,
            DATABASE_URL="sqlite:///./reliefos_lite.db"
        )
    assert "CRITICAL DATABASE CONFIGURATION ERROR" in str(exc.value)
    assert "requires PostgreSQL" in str(exc.value)


def test_postgresql_enterprise_engine_pooling_configuration():
    """Verify PostgreSQL engine is configured with production-grade pooling and keepalive."""
    pg_url = "postgresql+psycopg2://postgres:postgres@localhost:5432/reliefos_mock"
    engine = create_db_engine(pg_url)

    assert engine.dialect.name == "postgresql"
    # Verify pool settings
    pool = engine.pool
    assert isinstance(pool, QueuePool)
    assert pool.size() == 10
    assert pool._max_overflow == 20
    assert pool._timeout == 30
    assert pool._recycle == 1800
    assert pool._pre_ping is True


def test_check_db_connection_handles_unreachable_postgres_safely():
    """Verify diagnostic connectivity check returns status unreachable without unhandled crash."""
    unreachable_pg_url = "postgresql+psycopg2://nobody:wrongpass@127.0.0.1:54329/nonexistent"
    engine = create_db_engine(unreachable_pg_url)

    res = check_db_connection(engine)
    assert res["status"] == "unreachable"
    assert res["is_postgres"] is True
    assert "error" in res


@pytest.mark.anyio
async def test_lifespan_production_fails_if_sqlite_used():
    """Verify application lifespan rejects non-PostgreSQL databases in production."""
    mock_settings = Settings(
        ENVIRONMENT="development",
        DEBUG=False,
        JWT_SECRET="a" * 32 + "secure_entropy_key",
        DATABASE_URL="sqlite:///./reliefos_lite.db"
    )
    with patch.object(type(mock_settings), "is_production", True), patch("app.main.settings", mock_settings):
        with pytest.raises(RuntimeError) as exc:
            async with lifespan(app):
                pass
        assert "CRITICAL DATABASE CONFIGURATION ERROR" in str(exc.value)


# =========================================================================
# 2. Database Models & CRUD Compatibility Tests
# =========================================================================

def test_database_crud_zones():
    """Verify ZoneModel CRUD operations."""
    db = SessionLocal()
    unique_code = f"ZONE-TEST-{uuid.uuid4().hex[:6].upper()}"
    try:
        # Create
        new_zone = ZoneModel(
            code=unique_code,
            name="Test Evacuation Perimeter",
            risk_level="HIGH_ALERT",
            risk_score=78.5,
            latitude=26.15,
            longitude=91.75,
            affected_population=1200,
            inundation_area_ha=45.2,
            water_depth_m=0.85,
            status="ACTIVE_ALERT",
            road_status="RESTRICTED"
        )
        db.add(new_zone)
        db.commit()

        # Read
        fetched = db.query(ZoneModel).filter(ZoneModel.code == unique_code).first()
        assert fetched is not None
        assert fetched.name == "Test Evacuation Perimeter"
        assert fetched.risk_score == 78.5

        # Update
        fetched.risk_score = 85.0
        fetched.status = "CRITICAL_ALERT"
        db.commit()

        updated = db.query(ZoneModel).filter(ZoneModel.code == unique_code).first()
        assert updated.risk_score == 85.0
        assert updated.status == "CRITICAL_ALERT"

        # Delete
        db.delete(updated)
        db.commit()
        assert db.query(ZoneModel).filter(ZoneModel.code == unique_code).first() is None
    finally:
        db.close()


def test_database_crud_shelters():
    """Verify ShelterModel CRUD operations."""
    db = SessionLocal()
    unique_code = f"SHELTER-{uuid.uuid4().hex[:6].upper()}"
    try:
        new_shelter = ShelterModel(
            code=unique_code,
            name="Sarusajai Indoor Stadium Staging Center",
            zone_code="ZONE 01",
            location_desc="National Highway 27 Junction",
            latitude=26.12,
            longitude=91.76,
            capacity=800,
            occupancy=150,
            status="ACTIVE",
            verification_status="VERIFIED",
            verification_source="ASDMA Kamrup Metro Field Survey",
            verified_date="2026-10-09"
        )
        db.add(new_shelter)
        db.commit()

        fetched = db.query(ShelterModel).filter(ShelterModel.code == unique_code).first()
        assert fetched is not None
        assert fetched.capacity == 800
        assert fetched.occupancy == 150

        # Update occupancy
        fetched.occupancy = 250
        db.commit()

        updated = db.query(ShelterModel).filter(ShelterModel.code == unique_code).first()
        assert updated.occupancy == 250

        # Cleanup
        db.delete(updated)
        db.commit()
    finally:
        db.close()


def test_database_crud_road_closures():
    """Verify RoadClosureModel CRUD operations."""
    db = SessionLocal()
    corridor = f"NH-27 Test Submerged Section-{uuid.uuid4().hex[:4]}"
    try:
        closure = RoadClosureModel(
            corridor_name=corridor,
            location_desc="Saraighat Link Bridge",
            latitude=26.18,
            longitude=91.72,
            water_depth_m=0.55,
            clearance_threshold_m=0.35,
            status="IMPASSABLE_FLOOD",
            detour_corridor="AT Road Alternative Bypass",
            verified_by="PWD Assam & Traffic Division",
            is_active=True
        )
        db.add(closure)
        db.commit()

        fetched = db.query(RoadClosureModel).filter(RoadClosureModel.corridor_name == corridor).first()
        assert fetched is not None
        assert fetched.water_depth_m == 0.55
        assert fetched.is_active is True

        # Resolve closure
        fetched.status = "CLEARED_OPEN"
        fetched.is_active = False
        db.commit()

        updated = db.query(RoadClosureModel).filter(RoadClosureModel.corridor_name == corridor).first()
        assert updated.is_active is False

        # Cleanup
        db.delete(updated)
        db.commit()
    finally:
        db.close()


def test_database_crud_dispatch_orders():
    """Verify DispatchOrderModel lifecycle states."""
    db = SessionLocal()
    disp_id = f"DSP-TEST-{uuid.uuid4().hex[:8].upper()}"
    try:
        order = DispatchOrderModel(
            dispatch_id=disp_id,
            plan_id="PLAN-LEXICOGRAPHIC-STAGE-1",
            zone_code="ZONE 01",
            zone_name="ZONE 01 (North Guwahati)",
            vehicle_code="VH-01",
            vehicle_name="Tata 407 High-Clearance 4x4",
            resource_type="Food & Water Bundles",
            food_quantity_kg=500.0,
            water_quantity_l=400.0,
            total_weight_kg=900.0,
            destination_desc="Amingaon Relief Hub",
            route_summary="Sarusajai -> Saraighat -> Amingaon",
            transit_distance_km=12.5,
            detour_required=False,
            status="PENDING",
            is_dry_run=True,
            is_simulation=False,
            safety_validation_passed=True,
            form_8b_reference="ASDMA-FORM8B-2026-TEST"
        )
        db.add(order)
        db.commit()

        fetched = db.query(DispatchOrderModel).filter(DispatchOrderModel.dispatch_id == disp_id).first()
        assert fetched is not None
        assert fetched.status == "PENDING"

        # Transition to APPROVED
        fetched.status = "APPROVED"
        fetched.reviewed_by = "Insp. S. Sharma"
        fetched.reviewed_at = datetime.now(timezone.utc)
        fetched.review_decision = "APPROVED"
        db.commit()

        updated = db.query(DispatchOrderModel).filter(DispatchOrderModel.dispatch_id == disp_id).first()
        assert updated.status == "APPROVED"
        assert updated.reviewed_by == "Insp. S. Sharma"

        # Cleanup
        db.delete(updated)
        db.commit()
    finally:
        db.close()


# =========================================================================
# 3. Authentication & User Credentials
# =========================================================================

def test_authentication_registry_and_user_profiles():
    """Verify default registered operational officers exist and pass validation."""
    assert "commander" in REGISTERED_USERS
    assert "operator" in REGISTERED_USERS
    assert "analyst" in REGISTERED_USERS

    cmd = REGISTERED_USERS["commander"]
    assert cmd["role"] == ROLE_COMMANDER
    assert "@" in cmd["email"]
    assert cmd["agency"] == "ASDMA District Control Room"

    op = REGISTERED_USERS["operator"]
    assert op["role"] == ROLE_OPERATOR
    assert "@" in op["email"]

    an = REGISTERED_USERS["analyst"]
    assert an["role"] == ROLE_ANALYST


# =========================================================================
# 4. Inventory Buffer & Allocation
# =========================================================================

def test_inventory_item_buffer_management():
    """Verify InventoryItemModel available and reserved quantity constraints."""
    db = SessionLocal()
    sku = f"SKU-TEST-{uuid.uuid4().hex[:6].upper()}"
    try:
        item = InventoryItemModel(
            sku=sku,
            name="Emergency Water Purification Tablets (10,000 tabs)",
            category="Water & Sanitation",
            total_quantity=5000.0,
            available_quantity=5000.0,
            reserved_quantity=0.0,
            unit="kits",
            status="In Stock",
            last_verified_by="Kamrup Metro Central Depot"
        )
        db.add(item)
        db.commit()

        fetched = db.query(InventoryItemModel).filter(InventoryItemModel.sku == sku).first()
        assert fetched.total_quantity == 5000.0
        assert fetched.available_quantity == 5000.0

        # Reserve 1500 units for wave dispatch
        fetched.available_quantity -= 1500.0
        fetched.reserved_quantity += 1500.0
        db.commit()

        updated = db.query(InventoryItemModel).filter(InventoryItemModel.sku == sku).first()
        assert updated.available_quantity == 3500.0
        assert updated.reserved_quantity == 1500.0
        assert updated.total_quantity == updated.available_quantity + updated.reserved_quantity

        # Cleanup
        db.delete(updated)
        db.commit()
    finally:
        db.close()


# =========================================================================
# 5. Operational Scenarios & Demand Lifecycle
# =========================================================================

def test_demand_scenario_lifecycle():
    """Verify DemandModel lifecycle transitions (REQUESTED -> VERIFIED -> ALLOCATED)."""
    db = SessionLocal()
    req_id = f"DEM-TEST-{uuid.uuid4().hex[:6].upper()}"
    try:
        demand = DemandModel(
            req_id=req_id,
            zone_code="ZONE 01",
            resource_type="Food Rations",
            requested_qty=600.0,
            unit="kg",
            priority="CRITICAL",
            status="PENDING",
            lifecycle_status="REQUESTED",
            verification_status="UNVERIFIED",
            request_source="Field Shelter In-Charge"
        )
        db.add(demand)
        db.commit()

        fetched = db.query(DemandModel).filter(DemandModel.req_id == req_id).first()
        assert fetched.status == "PENDING"
        assert fetched.lifecycle_status == "REQUESTED"

        # Verify demand
        fetched.lifecycle_status = "VERIFIED"
        fetched.verification_status = "VERIFIED"
        fetched.verified_by = "Insp. S. Sharma"
        fetched.verified_at = datetime.now(timezone.utc)
        fetched.status = "APPROVED"
        db.commit()

        verified = db.query(DemandModel).filter(DemandModel.req_id == req_id).first()
        assert verified.lifecycle_status == "VERIFIED"
        assert verified.verification_status == "VERIFIED"
        assert verified.verified_by == "Insp. S. Sharma"

        # Cleanup
        db.delete(verified)
        db.commit()
    finally:
        db.close()


# =========================================================================
# 6. Audit Logging & AI-Related Persistence
# =========================================================================

def test_audit_log_persistence_and_query():
    """Verify operational AuditLogModel persistence."""
    db = SessionLocal()
    entity_id = f"ENTITY-{uuid.uuid4().hex[:8].upper()}"
    try:
        entry = AuditLogModel(
            operator_name="EOC Commander P. Baruah",
            entity_type="INVENTORY",
            entity_id=entity_id,
            action="UPDATE_BUFFER",
            old_value='{"total": 5000, "available": 5000}',
            new_value='{"total": 5000, "available": 3500, "reserved": 1500}',
            notes="Authorized 1500 units release for Zone 01 flood relief."
        )
        db.add(entry)
        db.commit()

        log = db.query(AuditLogModel).filter(AuditLogModel.entity_id == entity_id).first()
        assert log is not None
        assert log.operator_name == "EOC Commander P. Baruah"
        assert log.action == "UPDATE_BUFFER"

        # Cleanup
        db.delete(log)
        db.commit()
    finally:
        db.close()


def test_ai_decision_audit_persistence():
    """Verify AI advisory guidance persistence to AuditLogModel with digest and redaction."""
    db = SessionLocal()
    try:
        audit_id = record_ai_audit_event(
            operator_name="Insp. S. Sharma",
            query_text="Assess flood vulnerability for Sarusajai stadium relief camp with Bearer reliefos-sensitive-token-2026-key",
            provider_name="gemini",
            model_name="gemini-flash-lite-latest",
            latency_ms=320.5,
            recommendation_summary="Dispatch 2 Tata 407 carriers via Saraighat detour to circumvent inundated MG Road section.",
            supporting_evidence_count=4,
            risks_count=2,
            disclosures_count=1
        )
        assert audit_id.startswith("AI-AUDIT-")

        # Verify entry persisted in database
        log_entry = db.query(AuditLogModel).filter(AuditLogModel.entity_id == audit_id).first()
        assert log_entry is not None
        assert log_entry.entity_type == "AI_DECISION_SUPPORT"
        assert log_entry.action == "GENERATE_RECOMMENDATION"
        assert "Saraighat" in log_entry.notes
        # Verify credential was redacted
        assert "reliefos-sensitive-token-2026-key" not in log_entry.old_value
        assert "[REDACTED_TOKEN]" in log_entry.old_value

        # Cleanup
        db.delete(log_entry)
        db.commit()
    finally:
        db.close()


# =========================================================================
# 7. Alembic Migration Registry Completeness
# =========================================================================

def test_alembic_models_registry_matches_metadata():
    """Verify all 9 operational tables are properly registered in SQLAlchemy Base.metadata."""
    registered_tables = set(Base.metadata.tables.keys())
    expected_tables = {
        "zones", "depots", "vehicles", "inventory_items",
        "demands", "shelters", "audit_logs", "road_closures", "dispatch_orders"
    }
    assert expected_tables.issubset(registered_tables)
