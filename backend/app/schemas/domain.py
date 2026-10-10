from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ZoneSchema(BaseModel):
    id: str
    code: str
    name: str
    latitude: float
    longitude: float
    population: int
    risk_tier: str  # CRITICAL, HIGH, MODERATE, LOW
    risk_score: float
    food_demand_kg: int
    water_demand_kg: int
    total_demand_kg: int
    severity_weight: float
    is_accessible: bool = True
    inundation_area_ha: float = 0.0
    avg_flood_depth_m: float = 0.0
    key_road_status: str = "OPEN"
    recommended_interventions: List[str] = []


class DepotSchema(BaseModel):
    id: str
    code: str
    name: str
    latitude: float
    longitude: float
    total_capacity_kg: int
    available_food_kg: int
    available_water_kg: int
    reserved_food_kg: int
    reserved_water_kg: int


class ShelterSchema(BaseModel):
    id: str
    name: str
    zone_code: str
    location_desc: str
    capacity: int
    occupancy: int
    status: str  # ACTIVE, STANDBY, FULL


class VehicleSchema(BaseModel):
    id: str
    code: str
    name: str
    vehicle_type: str
    max_capacity_kg: int
    status: str  # AVAILABLE, ASSIGNED, MAINTENANCE
    assigned_route: Optional[str] = None
    payload_allocated_kg: int = 0
    utilization_pct: float = 0.0


class InventoryItemSchema(BaseModel):
    sku: str
    name: str
    description: str
    category: str  # Food Supplies, Packaged Food, Dry Rations, Drinking Water, Medical
    available_qty: int
    reserved_qty: int
    total_buffer: int
    unit: str  # kg, L, boxes
    status: str  # In Stock, Low Stock, Depleted
    verified_at: str


class DemandRecordSchema(BaseModel):
    id: str
    zone_code: str
    zone_name: str
    resource_type: str  # Food Rations, Potable Water, Medical Packs
    requested_qty: int
    unit: str
    priority: str  # CRITICAL, HIGH, MEDIUM, LOW
    status: str  # PENDING, APPROVED, PARTIALLY_FULFILLED, FULFILLED
    request_source: str  # Observed, Estimated, Field Audit
    created_at: str


class OptimizationRequest(BaseModel):
    scenario_id: Optional[str] = "baseline"
    prioritize_water: bool = True
    max_runtime_seconds: int = 5
    reserve_buffer_pct: float = 15.0


class ZoneAllocationResult(BaseModel):
    zone_code: str
    zone_name: str
    risk_tier: str
    food_demand_kg: int
    water_demand_kg: int
    total_demand_kg: int
    alloc_food_kg: int
    alloc_water_kg: int
    total_alloc_kg: int
    deficit_kg: int
    fulfillment_pct: float


class AllocationSummary(BaseModel):
    status: str
    algorithm: str
    solver_runtime_ms: float
    total_available_stock_kg: int
    total_reviewed_demand_kg: int
    proposed_allocation_kg: int
    coverage_ratio_pct: float
    projected_deficit_kg: int
    weighted_unmet_penalty: float
    est_transit_distance_km: float
    zones: List[ZoneAllocationResult]
    feasibility_checks: Dict[str, str]
    human_in_loop_status: str


class WaypointStop(BaseModel):
    sequence: int
    location_name: str
    distance_from_prev_km: float
    cumulative_km: float
    arrival_time_est: str
    action: str  # Departure, Detour, Offload, Return
    offload_food_kg: int = 0
    offload_water_kg: int = 0


class VehicleRoutePlan(BaseModel):
    vehicle_code: str
    vehicle_name: str
    vehicle_type: str
    assigned_crew: str
    radio_channel: str
    capacity_kg: int
    payload_loaded_kg: int
    utilization_pct: float
    total_distance_km: float
    est_tour_duration: str
    status: str
    route_profile: str
    waypoints: List[WaypointStop]


class RouteOptimizationResponse(BaseModel):
    status: str
    total_transit_distance_km: float
    baseline_distance_km: float
    distance_savings_pct: float
    fleet_tour_duration: str
    payload_utilization_kg: int
    payload_capacity_kg: int
    payload_utilization_pct: float
    inundations_evaded: int
    active_vehicles_count: int
    routes: List[VehicleRoutePlan]
    hazard_audit: List[Dict[str, Any]]


class FloodObservationSchema(BaseModel):
    station_id: str
    station_name: str
    river: str
    current_level_m: float
    warning_level_m: float
    danger_level_m: float
    variance_m: float
    alert_tier: str  # NORMAL, ALERT, DANGER
    discharge_cumecs: Optional[float] = None
    observed_at: str


class DataSourceSchema(BaseModel):
    code: str
    name: str
    authority: str
    class_type: str  # OBSERVED, FORECAST, ESTIMATED, STATIC+SENSOR, MANUAL AUDIT, SIMULATED
    protocol: str
    cadence: str
    last_ingest: str
    health_pct: float
    status: str


class AddStockRequest(BaseModel):
    sku: Optional[str] = Field(None, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(..., min_length=2, max_length=100)
    quantity: int = Field(..., gt=0, description="Quantity must be strictly positive")
    unit: str = Field(..., min_length=1, max_length=20)


class UpdateStockRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = None
    available_qty: Optional[int] = Field(None, ge=0)
    reserved_qty: Optional[int] = Field(None, ge=0)
    unit: Optional[str] = None
    status: Optional[str] = None


class CreateDemandRequest(BaseModel):
    zone_code: str = Field(..., min_length=2, max_length=50)
    resource_type: str = Field(..., min_length=2, max_length=100)
    requested_qty: int = Field(..., gt=0, description="Requested quantity must be strictly positive")
    unit: str = Field(..., min_length=1, max_length=20)
    priority: str = Field("HIGH")


class UpdateDemandStatusRequest(BaseModel):
    status: str = Field(..., description="Must be PENDING, APPROVED, FULFILLED, or REJECTED")


class RunScenarioRequest(BaseModel):
    scenario_id: str = Field("A", description="Scenario ID (A to J)")
    custom_overrides: Optional[Dict[str, Any]] = Field(None, description="Optional parameter overrides")


class SwitchModeRequest(BaseModel):
    mode: str = Field(..., description="OPERATIONAL_LIVE, HISTORICAL_EVENT, or SIMULATION_DRILL")
    operator_name: Optional[str] = Field("Insp. S. Sharma (EOC Planner)")
    historical_event_id: Optional[str] = Field("HIST-2022-GHY-MONSOON")
    notes: Optional[str] = Field("")


class ManualGaugeReadingRequest(BaseModel):
    station_id: str = Field(..., min_length=2)
    water_level_m: float = Field(..., ge=0.0)
    operator_name: Optional[str] = Field("Insp. S. Sharma")
    notes: Optional[str] = Field("Manual gauge verification")


class RoadClosureRequest(BaseModel):
    corridor_name: str = Field(..., min_length=2, max_length=255)
    location_desc: Optional[str] = Field("")
    latitude: float = Field(...)
    longitude: float = Field(...)
    water_depth_m: float = Field(..., ge=0.0)
    status: Optional[str] = Field("IMPASSABLE_FLOOD")
    detour_corridor: Optional[str] = Field("")
    verified_by: Optional[str] = Field("Traffic Control Guwahati")


class RealRouteRequest(BaseModel):
    start_lat: float = Field(...)
    start_lng: float = Field(...)
    end_lat: float = Field(...)
    end_lng: float = Field(...)
    route_name: Optional[str] = Field(None)


class VerifyDemandRequest(BaseModel):
    verified_by: Optional[str] = Field("Insp. S. Sharma")
    notes: Optional[str] = Field("")


class DispatchDemandRequest(BaseModel):
    vehicle_code: str = Field(..., min_length=2)
    dispatched_by: Optional[str] = Field("Insp. S. Sharma")
    notes: Optional[str] = Field("")


