from datetime import datetime, timezone
import logging
from typing import Optional, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import get_settings

logger = logging.getLogger("reliefos.database")

Base = declarative_base()


def create_db_engine(database_url: Optional[str] = None) -> Engine:
    """
    Constructs a resilient SQLAlchemy Engine configured for SQLite (development)
    or PostgreSQL (production connection pooling, keepalive, and disconnect recovery).
    """
    settings = get_settings()
    url = database_url or settings.normalized_database_url

    if url.startswith("sqlite"):
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    else:
        # Production PostgreSQL engine with enterprise connection pooling
        return create_engine(
            url,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_pre_ping=True,
            echo=False
        )


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection(engine_to_check: Optional[Engine] = None) -> Dict[str, Any]:
    """Tests connectivity to the active database engine."""
    target_engine = engine_to_check or engine
    dialect = target_engine.dialect.name
    try:
        with target_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "dialect": dialect,
            "is_postgres": dialect == "postgresql",
            "is_sqlite": dialect == "sqlite"
        }
    except Exception as exc:
        return {
            "status": "unreachable",
            "dialect": dialect,
            "error": str(exc),
            "is_postgres": dialect == "postgresql",
            "is_sqlite": dialect == "sqlite"
        }


def init_db(engine_override: Optional[Engine] = None):
    """Initializes tables and seeds default Kamrup Metro operational records if empty."""
    target_engine = engine_override or engine
    from app.models.domain import (
        ZoneModel, DepotModel, VehicleModel, InventoryItemModel,
        DemandModel, ShelterModel, RoadClosureModel, AuditLogModel, DispatchOrderModel,
        StockMovementModel, IncidentModel, SituationReportModel, UserProfileModel
    )
    from app.core.data_store import (
        ZONES_DATA, DEPOT_DATA, VEHICLES_DATA, INVENTORY_ITEMS_DATA,
        DEMAND_RECORDS_DATA, SHELTERS_DATA
    )

    Base.metadata.create_all(bind=target_engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)
    db = session_factory()
    try:
        if db.query(ZoneModel).count() == 0:
            for z in ZONES_DATA:
                db.add(ZoneModel(
                    code=z["code"],
                    name=z["name"],
                    risk_level=z["risk_tier"],
                    risk_score=z["risk_score"],
                    latitude=z["latitude"],
                    longitude=z["longitude"],
                    affected_population=z["population"],
                    inundation_area_ha=z["inundation_area_ha"],
                    water_depth_m=z["avg_flood_depth_m"],
                    status="MONITORING",
                    road_status=z["key_road_status"]
                ))

            db.add(DepotModel(
                code=DEPOT_DATA["code"],
                name=DEPOT_DATA["name"],
                latitude=DEPOT_DATA["latitude"],
                longitude=DEPOT_DATA["longitude"],
                capacity_kg=float(DEPOT_DATA["total_capacity_kg"]),
                available_stock_kg=float(DEPOT_DATA["available_food_kg"] + DEPOT_DATA["available_water_kg"])
            ))

            for v in VEHICLES_DATA:
                db.add(VehicleModel(
                    code=v["code"],
                    name=v["name"],
                    plate=f"AS-01-DD-{v['code'].replace('VH-', '90')}",
                    type=v["vehicle_type"],
                    capacity_kg=float(v["max_capacity_kg"]),
                    status=v["status"],
                    fuel_pct=100
                ))

            for item in INVENTORY_ITEMS_DATA:
                db.add(InventoryItemModel(
                    sku=item["sku"],
                    name=item["name"],
                    category=item["category"],
                    total_quantity=float(item["total_buffer"]),
                    available_quantity=float(item["available_qty"]),
                    reserved_quantity=float(item["reserved_qty"]),
                    unit=item["unit"],
                    status=item["status"]
                ))

            for d in DEMAND_RECORDS_DATA:
                db.add(DemandModel(
                    req_id=d["id"],
                    zone_code=d["zone_code"],
                    resource_type=d["resource_type"],
                    requested_qty=float(d["requested_qty"]),
                    unit=d["unit"],
                    priority=d["priority"],
                    status=d["status"]
                ))

        if db.query(ShelterModel).count() == 0:
            for s in SHELTERS_DATA:
                db.add(ShelterModel(
                    code=s["id"].upper(),
                    name=s["name"],
                    zone_code=s["zone_code"],
                    location_desc=s.get("location_desc", ""),
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                    capacity=s["capacity"],
                    occupancy=s["occupancy"],
                    status=s["status"],
                    verification_status="VERIFIED",
                    verification_source="DDMA Kamrup Metro Evacuation Registry 2024",
                    verified_date="2024-06-15"
                ))

        if db.query(RoadClosureModel).count() == 0:
            db.add(RoadClosureModel(
                corridor_name="MG Road (Santipur Culvert Section)",
                location_desc="Bharalumukh to Santipur Riverfront corridor",
                latitude=26.175,
                longitude=91.738,
                water_depth_m=0.40,
                clearance_threshold_m=0.35,
                status="IMPASSABLE_FLOOD",
                detour_corridor="AT Road Arterial Bypass via Arya Nagar Flyover",
                verified_by="PWD Roads Assam & Traffic Control Guwahati",
                is_active=True
            ))

        if db.query(AuditLogModel).count() == 0:
            db.add(AuditLogModel(
                operator_name="System Initialization Routine",
                entity_type="SYSTEM_MODE",
                entity_id="INIT-BOOT-01",
                action="INITIALIZE_OPERATIONAL_STATE",
                old_value=None,
                new_value="OPERATIONAL_LIVE",
                notes="RELIEFOS Lite operational database initialized with verified Kamrup Metro baseline."
            ))

        if db.query(DispatchOrderModel).count() == 0:
            db.add(DispatchOrderModel(
                dispatch_id="DSP-20261005-001",
                plan_id="PLAN-LEXICOGRAPHIC_SEVERITY_OPTIMAL",
                zone_code="ZONE 01",
                zone_name="ZONE 01 (North Guwahati)",
                vehicle_code="VH-01",
                vehicle_name="Tata 407 High-Clearance 4x4",
                resource_type="Food Rations & Potable Water",
                food_quantity_kg=1200.0,
                water_quantity_l=900.0,
                total_weight_kg=2100.0,
                destination_desc="North Guwahati Embankment Relief Camp",
                route_summary="Sarusajai Hub -> NH-27 -> Saraighat Bridge -> North Guwahati",
                transit_distance_km=14.2,
                detour_required=False,
                status="PENDING",
                is_dry_run=True,
                is_simulation=False,
                safety_validation_passed=True,
                safety_warnings='{"warnings": ["Carrier payload is at 84% capacity threshold."], "errors": []}',
                form_8b_reference="ASDMA-F8B-2026-LOG-DISPATCH",
                external_connector_status="DISABLED_BY_POLICY"
            ))

            db.add(DispatchOrderModel(
                dispatch_id="DSP-20261005-002",
                plan_id="PLAN-LEXICOGRAPHIC_SEVERITY_OPTIMAL",
                zone_code="ZONE 02",
                zone_name="ZONE 02 (Bharalumukh)",
                vehicle_code="VH-02",
                vehicle_name="Ashok Leyland 4WD Heavy Hauler",
                resource_type="Food Rations & Potable Water",
                food_quantity_kg=1000.0,
                water_quantity_l=700.0,
                total_weight_kg=1700.0,
                destination_desc="Bharalumukh Ward Community Shelter",
                route_summary="Sarusajai -> Jalukbari -> AT Road Bypass -> Bharalumukh",
                transit_distance_km=11.8,
                detour_required=True,
                detour_reason="MG Road Santipur culvert submerged (0.40m > 0.35m threshold); forced detour via AT Road",
                status="APPROVED",
                is_dry_run=True,
                is_simulation=False,
                safety_validation_passed=True,
                safety_warnings='{"warnings": ["Active bypass enforced due to MG Road flood inundation."], "errors": []}',
                reviewed_by="Insp. S. Sharma",
                reviewed_at=datetime.now(timezone.utc),
                review_decision="APPROVED",
                review_notes="Approved under ASDMA Form 8B emergency staging protocol. Detour verified via PWD portal.",
                form_8b_reference="ASDMA-F8B-2026-LOG-DISPATCH",
                external_connector_status="DISABLED_BY_POLICY"
            ))

            db.add(DispatchOrderModel(
                dispatch_id="DSP-20261005-003",
                plan_id="PLAN-LEXICOGRAPHIC_SEVERITY_OPTIMAL",
                zone_code="ZONE 03",
                zone_name="ZONE 03 (Uzan Bazar)",
                vehicle_code="VH-03",
                vehicle_name="Mahindra Bolero Camper 4WD",
                resource_type="Potable Water Supply Wave",
                food_quantity_kg=300.0,
                water_quantity_l=500.0,
                total_weight_kg=800.0,
                destination_desc="Uzan Bazar Ghat Relief Camp",
                route_summary="Sarusajai -> GS Road -> Panbazar -> Uzan Bazar",
                transit_distance_km=8.5,
                detour_required=False,
                status="READY",
                is_dry_run=True,
                is_simulation=False,
                safety_validation_passed=True,
                safety_warnings='{"warnings": [], "errors": []}',
                reviewed_by="Insp. S. Sharma",
                reviewed_at=datetime.now(timezone.utc),
                review_decision="APPROVED",
                review_notes="Water surge demand verified; staging at Sarusajai Bay 3.",
                form_8b_reference="ASDMA-F8B-2026-LOG-DISPATCH",
                external_connector_status="DISABLED_BY_POLICY"
            ))

        if db.query(StockMovementModel).count() == 0:
            db.add(StockMovementModel(
                movement_id="MOV-20261012-001",
                item_sku="SKU-FOOD-01",
                item_name="Fortified Rice & Lentil Emergency Rations",
                depot_code="DEPOT-GAU-01",
                movement_type="RECEIPT",
                quantity=3500.0,
                unit="kg",
                batch_lot_number="LOT-ASDMA-2026-F01",
                expiry_date="2027-06-30",
                balance_before=0.0,
                balance_after=3500.0,
                reference_doc="GOV-ASSAM-RELIEF-CONSIGNMENT-88",
                operator_name="Insp. S. Sharma (Logistics Officer)",
                notes="Initial seasonal pre-positioning consignment received at Sarusajai Hub Bay 1."
            ))
            db.add(StockMovementModel(
                movement_id="MOV-20261012-002",
                item_sku="SKU-WATER-02",
                item_name="Packaged Drinking Water (1L Pouches)",
                depot_code="DEPOT-GAU-01",
                movement_type="RECEIPT",
                quantity=2000.0,
                unit="liters",
                batch_lot_number="LOT-PHE-2026-W04",
                expiry_date="2026-12-31",
                balance_before=0.0,
                balance_after=2000.0,
                reference_doc="PHE-GUWAHATI-SUPPLY-CHALLAN-12",
                operator_name="Insp. S. Sharma (Logistics Officer)",
                notes="PHE Department potable drinking water buffer delivered and certified."
            ))

        if db.query(IncidentModel).count() == 0:
            db.add(IncidentModel(
                incident_id="INC-2026-KM-001",
                incident_type="EMBANKMENT_BREACH",
                severity="CRITICAL",
                status="IN_RESPONSE",
                title="Brahmaputra Embankment Seepage & Santipur Culvert Backflow",
                description="Rising river stage at Bharalumukh sluice gate (48.15m MSL) has induced backflow along Santipur riverfront road corridor. Water depth on carriage-way 0.40m overtopping statutory clearance threshold (0.35m).",
                location_desc="Santipur Riverfront Ghat to Bharalumukh Outfall",
                latitude=26.175,
                longitude=91.738,
                zone_code="ZONE 02",
                location_id="kamrup_metro",
                reported_by="SDRF Quick Reaction Patrol Alpha",
                reported_at=datetime.now(timezone.utc),
                verified_by="EOC Commander P. Baruah",
                verified_at=datetime.now(timezone.utc),
                casualties_reported=0,
                persons_stranded=18,
                livestock_affected=6,
                infrastructure_damaged="MG Road Santipur culvert revetment stones dislodged. Traffic closed; detour via AT Road.",
                response_action_taken="SDRF inflatable boats mobilized for stranded shopkeepers. Sandbag reinforcement initiated by Water Resources Dept.",
                assigned_team="SDRF 1st Bn Guwahati Team 2"
            ))
            db.add(IncidentModel(
                incident_id="INC-2026-KM-002",
                incident_type="STRANDED_CLUSTER",
                severity="HIGH",
                status="REPORTED",
                title="Urban Lowland Inundation at Bharalumukh Ward 4 Lower Basin",
                description="Heavy local storm runoff combined with drainage channel choke has inundated 25 households in lower depression. Approximately 45 persons isolated with drinking water shortages.",
                location_desc="Bharalumukh Ward 4, Railway Line Approach",
                latitude=26.168,
                longitude=91.730,
                zone_code="ZONE 02",
                location_id="kamrup_metro",
                reported_by="Ward Member / Civil Defence Warden",
                reported_at=datetime.now(timezone.utc),
                verified_by="Insp. S. Sharma",
                verified_at=datetime.now(timezone.utc),
                casualties_reported=0,
                persons_stranded=45,
                livestock_affected=12,
                infrastructure_damaged="Submerged community tube-well; drinking water contaminated.",
                response_action_taken="Requisition for 500L clean drinking water and 300 kg dry rations logged in RELIEFOS dispatch queue.",
                assigned_team="Civil Defence Team Ward 4 & DDMA Logistics"
            ))

        if db.query(SituationReportModel).count() == 0:
            db.add(SituationReportModel(
                sitrep_id="SITREP-20261013-KM-01",
                report_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                time_window="06:00 - 18:00 IST",
                district_name="Kamrup Metropolitan",
                location_id="kamrup_metro",
                active_human_lives_affected=23000,
                displaced_in_shelters=850,
                inundated_villages_count=14,
                active_shelters_count=2,
                roads_closed_count=1,
                critical_river_stages='[{"station": "CWC Pandu", "river": "Brahmaputra", "stage_m": 49.68, "danger_m": 49.68, "status": "DANGER"}, {"station": "DC Court Ghat", "river": "Brahmaputra", "stage_m": 49.68, "danger_m": 49.50, "status": "ABOVE_DANGER"}]',
                weather_synopsis="Monsoon depression active across Lower Assam. 24-hour rainfall recorded 38.4 mm at Borjhar RMC. Intermittent moderate to heavy precipitation forecast for next 36 hours.",
                relief_distributed_summary='{"total_food_distributed_kg": 4800, "total_water_distributed_l": 3500, "medical_kits_issued": 120, "active_fleet_convoys": 3}',
                active_incidents_count=2,
                compiling_officer="Insp. S. Sharma (Logistics Officer)",
                approving_commander="EOC Commander P. Baruah",
                approval_status="APPROVED",
                form_reference="ASDMA-SITREP-DAILY-01",
                approved_at=datetime.now(timezone.utc)
            ))

        if db.query(UserProfileModel).count() == 0:
            from app.core.auth import REGISTERED_USERS
            for uname, udata in REGISTERED_USERS.items():
                db.add(UserProfileModel(
                    username=udata["username"],
                    role=udata["role"],
                    name=udata["name"],
                    agency=udata.get("agency", "District Operations"),
                    email=udata.get("email"),
                    phone=udata.get("phone"),
                    avatar_url=udata.get("avatar_url", "/officer_sharma.png"),
                    password_hash=udata.get("password_hash")
                ))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

