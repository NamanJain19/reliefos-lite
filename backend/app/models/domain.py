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
