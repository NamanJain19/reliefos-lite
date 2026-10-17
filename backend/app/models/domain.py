from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text
from datetime import datetime, timezone
from app.core.database import Base


class ZoneModel(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    risk_level = Column(String(50), nullable=False)
    risk_score = Column(Float, default=0.0)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_population = Column(Integer, default=0)
    inundation_area_ha = Column(Float, default=0.0)
    water_depth_m = Column(Float, default=0.0)
    status = Column(String(50), default="MONITORING")
    road_status = Column(String(50), default="OPEN")
    location_id = Column(String(50), default="kamrup_metro", index=True)


class DepotModel(Base):
    __tablename__ = "depots"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity_kg = Column(Float, default=20000.0)
    available_stock_kg = Column(Float, default=5500.0)
    location_id = Column(String(50), default="kamrup_metro", index=True)


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    plate = Column(String(50), nullable=False)
    type = Column(String(100), nullable=False)
    capacity_kg = Column(Float, default=2500.0)
    status = Column(String(50), default="READY")
    fuel_pct = Column(Integer, default=100)
    location_id = Column(String(50), default="kamrup_metro", index=True)


class InventoryItemModel(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    total_quantity = Column(Float, default=0.0)
    available_quantity = Column(Float, default=0.0)
    reserved_quantity = Column(Float, default=0.0)
    unit = Column(String(50), default="kg")
    status = Column(String(50), default="In Stock")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_verified_by = Column(String(100), default="ASDMA Central Logistics Desk")
    location_id = Column(String(50), default="kamrup_metro", index=True)


class DemandModel(Base):
    __tablename__ = "demands"

    id = Column(Integer, primary_key=True, index=True)
    req_id = Column(String(50), unique=True, index=True, nullable=False)
    zone_code = Column(String(50), nullable=False)
    resource_type = Column(String(100), nullable=False)
    requested_qty = Column(Float, nullable=False)
    unit = Column(String(50), default="kg")
    priority = Column(String(50), default="HIGH")
    status = Column(String(50), default="PENDING")
    lifecycle_status = Column(String(50), default="REQUESTED")  # REQUESTED, VERIFIED, ALLOCATED, DISPATCHED, DELIVERED
    verification_status = Column(String(50), default="UNVERIFIED")  # VERIFIED, UNVERIFIED
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    request_source = Column(String(100), default="Field Shelter Coordinator")
    notes = Column(String(255), default="")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    location_id = Column(String(50), default="kamrup_metro", index=True)


class ShelterModel(Base):
    __tablename__ = "shelters"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    zone_code = Column(String(50), nullable=False)
    location_desc = Column(String(255), default="")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, default=500)
    occupancy = Column(Integer, default=0)
    status = Column(String(50), default="ACTIVE")
    verification_status = Column(String(50), default="VERIFIED")  # VERIFIED, ILLUSTRATIVE_PLANNING
    verification_source = Column(String(255), default="DDMA Kamrup Metro Evacuation Registry 2024")
    verified_date = Column(String(50), default="2024-06-15")
    location_id = Column(String(50), default="kamrup_metro", index=True)


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    operator_name = Column(String(100), default="Insp. S. Sharma (EOC Planner)")
    entity_type = Column(String(50), nullable=False, index=True)  # INVENTORY, DEMAND, ROAD_CLOSURE, GAUGE_READING, DISPATCH_MANIFEST, SYSTEM_MODE
    entity_id = Column(String(100), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, VERIFY, DISPATCH, OVERRIDE, SWITCH_MODE
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    notes = Column(String(255), default="")
    location_id = Column(String(50), default="kamrup_metro", index=True)


class RoadClosureModel(Base):
    __tablename__ = "road_closures"

    id = Column(Integer, primary_key=True, index=True)
    corridor_name = Column(String(255), nullable=False)
    location_desc = Column(String(255), default="")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    water_depth_m = Column(Float, default=0.0)
    clearance_threshold_m = Column(Float, default=0.35)
    status = Column(String(50), default="IMPASSABLE_FLOOD")  # IMPASSABLE_FLOOD, RESTRICTED, CLEARED_OPEN
    detour_corridor = Column(String(255), default="")
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    verified_by = Column(String(100), default="PWD Roads / Traffic Police Guwahati")
    is_active = Column(Boolean, default=True)
    location_id = Column(String(50), default="kamrup_metro", index=True)


class DispatchOrderModel(Base):
    __tablename__ = "dispatch_orders"

    id = Column(Integer, primary_key=True, index=True)
    dispatch_id = Column(String(50), unique=True, index=True, nullable=False)
    plan_id = Column(String(50), index=True, nullable=False)
    zone_code = Column(String(50), nullable=False)
    zone_name = Column(String(255), nullable=False)
    vehicle_code = Column(String(50), nullable=False)
    vehicle_name = Column(String(255), default="")
    resource_type = Column(String(100), default="Food Rations & Potable Water")
    food_quantity_kg = Column(Float, default=0.0)
    water_quantity_l = Column(Float, default=0.0)
    total_weight_kg = Column(Float, default=0.0)
    destination_desc = Column(String(255), default="")
    route_summary = Column(String(255), default="")
    transit_distance_km = Column(Float, default=0.0)
    detour_required = Column(Boolean, default=False)
    detour_reason = Column(String(255), default="")
    status = Column(String(50), default="PENDING", index=True)  # PENDING, APPROVED, READY, DISPATCHED, DELIVERED, CANCELLED, REJECTED
    is_dry_run = Column(Boolean, default=True)
    is_simulation = Column(Boolean, default=False)
    safety_validation_passed = Column(Boolean, default=True)
    safety_warnings = Column(Text, default="[]")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_decision = Column(String(50), nullable=True)  # APPROVED, REJECTED
    review_notes = Column(Text, nullable=True)
    form_8b_reference = Column(String(100), default="ASDMA-F8B-2026-LOG-DISPATCH")
    external_connector_attempted = Column(Boolean, default=False)
    external_connector_status = Column(String(50), default="DISABLED_BY_POLICY")
    location_id = Column(String(50), default="kamrup_metro", index=True)


class StockMovementModel(Base):
    """
    Persistent warehouse ledger tracking every physical stock movement:
    receipts, issues, reservations, adjustments, and expiry write-offs.
    """
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(String(50), unique=True, index=True, nullable=False)
    item_sku = Column(String(50), index=True, nullable=False)
    item_name = Column(String(255), nullable=False)
    depot_code = Column(String(50), index=True, nullable=False)
    movement_type = Column(String(50), nullable=False, index=True)  # RECEIPT, DISPATCH_DEDUCTION, RESERVATION, RELEASE_RESERVATION, DAMAGE_EXPIRY_WRITE_OFF, AUDIT_ADJUSTMENT
    quantity = Column(Float, nullable=False)
    unit = Column(String(50), default="kg")
    batch_lot_number = Column(String(100), default="LOT-DEFAULT")
    expiry_date = Column(String(50), nullable=True)
    balance_before = Column(Float, default=0.0)
    balance_after = Column(Float, default=0.0)
    reference_doc = Column(String(100), default="DIRECT_ADJUSTMENT")
    operator_name = Column(String(100), default="ASDMA Logistics Officer")
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    notes = Column(Text, default="")
    location_id = Column(String(50), default="kamrup_metro", index=True)


class IncidentModel(Base):
    """
    Operational field incident tracking for emergency operations center (EOC):
    Embankment breaches, stranded civilians, bridge closures, and rescue calls.
    """
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(50), unique=True, index=True, nullable=False)
    incident_type = Column(String(50), nullable=False, index=True)  # EMBANKMENT_BREACH, FLASH_FLOOD, ROAD_SEVERANCE, STRANDED_CLUSTER, SHELTER_OVERFLOW, LANDSLIDE
    severity = Column(String(50), default="HIGH", index=True)  # CRITICAL, HIGH, MEDIUM, LOW
    status = Column(String(50), default="REPORTED", index=True)  # REPORTED, VERIFIED, IN_RESPONSE, RESOLVED, CLOSED
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    location_desc = Column(String(255), default="")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_code = Column(String(50), nullable=False)
    location_id = Column(String(50), default="kamrup_metro", index=True)
    reported_by = Column(String(100), default="DDMA Field Observer")
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    verified_by = Column(String(100), nullable=True)
    verified_at = Column(DateTime, nullable=True)
    casualties_reported = Column(Integer, default=0)
    persons_stranded = Column(Integer, default=0)
    livestock_affected = Column(Integer, default=0)
    infrastructure_damaged = Column(Text, default="")
    response_action_taken = Column(Text, default="")
    assigned_team = Column(String(100), default="SDRF 1st Battalion Guwahati")
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SituationReportModel(Base):
    """
    Official Disaster Situation Report (SitRep) conforming to ASDMA/NDMA Formats:
    Daily official summaries of displaced persons, damage, logistics distribution, and river stages.
    """
    __tablename__ = "situation_reports"

    id = Column(Integer, primary_key=True, index=True)
    sitrep_id = Column(String(50), unique=True, index=True, nullable=False)
    report_date = Column(String(50), nullable=False, index=True)  # YYYY-MM-DD
    time_window = Column(String(50), default="06:00 - 18:00 IST")
    district_name = Column(String(100), nullable=False)
    location_id = Column(String(50), default="kamrup_metro", index=True)
    active_human_lives_affected = Column(Integer, default=0)
    displaced_in_shelters = Column(Integer, default=0)
    inundated_villages_count = Column(Integer, default=0)
    active_shelters_count = Column(Integer, default=0)
    roads_closed_count = Column(Integer, default=0)
    critical_river_stages = Column(Text, default="[]")  # JSON string of CWC stations & stages
    weather_synopsis = Column(Text, default="")
    relief_distributed_summary = Column(Text, default="{}")  # JSON string of distributed food/water/medical
    active_incidents_count = Column(Integer, default=0)
    compiling_officer = Column(String(100), default="Insp. S. Sharma (Logistics Officer)")
    approving_commander = Column(String(100), nullable=True)
    approval_status = Column(String(50), default="DRAFT", index=True)  # DRAFT, APPROVED, TRANSMITTED_STATE_EOC
    form_reference = Column(String(100), default="ASDMA-SITREP-DAILY-01")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime, nullable=True)


class UserProfileModel(Base):
    """
    Authenticated operational officer profile and duty dossier record.
    Persists official name, duty desk assignment, contact information,
    cryptographic password hash, and avatar photo across sessions.
    """
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    role = Column(String(50), nullable=False, default="OPERATOR")
    name = Column(String(100), nullable=False)
    agency = Column(String(150), default="Kamrup Metro Logistics Desk")
    email = Column(String(150), nullable=True)
    phone = Column(String(50), nullable=True)
    avatar_url = Column(Text, nullable=True)
    password_hash = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


