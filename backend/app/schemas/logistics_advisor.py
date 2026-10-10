"""
RELIEFOS Lite — Pydantic Schemas for AI-Assisted Resource Allocation & Logistics Advisor.
Defines data structures for reviewable logistics plans, multi-strategy comparisons,
operational diagnostics, what-if scenario simulations, and human review sign-offs.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum


class LogisticsStrategyEnum(str, Enum):
    LEXICOGRAPHIC_SEVERITY_OPTIMAL = "LEXICOGRAPHIC_SEVERITY_OPTIMAL"
    PROPORTIONAL_EQUAL_SHARE = "PROPORTIONAL_EQUAL_SHARE"
    DISTANCE_MINIMIZING_PROXIMITY = "DISTANCE_MINIMIZING_PROXIMITY"
    WATER_FIRST_SURVIVAL = "WATER_FIRST_SURVIVAL"


class ShelterLinkInfo(BaseModel):
    shelter_code: str
    shelter_name: str
    location_desc: str
    capacity: int
    occupancy: int
    status: str
    allocated_food_kg: float
    allocated_water_l: float


class RouteSummaryInfo(BaseModel):
    vehicle_code: str
    vehicle_name: str
    vehicle_type: str
    assigned_crew: str
    radio_channel: str
    total_distance_km: float
    est_duration: str
    route_profile: str
    detour_enforced: bool
    detour_reason: Optional[str] = None
    waypoints_count: int
    polyline_coordinates: List[List[float]]


class ZoneLogisticsRecommendation(BaseModel):
    zone_code: str
    zone_name: str
    risk_tier: str
    severity_weight: float
    population: int
    food_demand_kg: float
    water_demand_kg: float
    total_demand_kg: float
    alloc_food_kg: float
    alloc_water_kg: float
    total_alloc_kg: float
    deficit_kg: float
    fulfillment_pct: float
    is_accessible: bool
    access_status: str
    assigned_vehicles: List[str]
    shelters: List[ShelterLinkInfo]
    ai_allocation_rationale: str


class BindingConstraintItem(BaseModel):
    constraint: str
    type: str  # "INVENTORY_BOUND", "VEHICLE_CAPACITY", "TOPOLOGY_SEVERED", "GLOBAL_OPTIMUM"
    description: str
    affected_resource: Optional[str] = None


class OperationalDiagnostics(BaseModel):
    binding_constraints: List[BindingConstraintItem]
    missing_data_warnings: List[str]
    unavailable_routes: List[str]
    capacity_bottlenecks: List[str]
    conflicting_inputs: List[str]
    telemetry_freshness: Dict[str, str]
    data_trust_summary: str


class AlternativeStrategyComparisonItem(BaseModel):
    strategy_id: str
    strategy_name: str
    is_recommended: bool
    priority_assumptions: str
    total_allocated_kg: float
    total_unmet_kg: float
    coverage_ratio_pct: float
    critical_zone_coverage_pct: float
    est_transit_distance_km: float
    est_fuel_burn_liters: float
    solver_runtime_ms: float
    solver_status: str  # "OPTIMAL" | "FEASIBLE" | "INFEASIBLE"
    key_tradeoff: str
    allocations_by_zone: Dict[str, Dict[str, float]]


class LogisticsAdvisorPlanResponse(BaseModel):
    plan_id: str
    plan_version: str
    generated_at: str
    active_strategy: str
    solver_engine: str
    solver_runtime_ms: float
    solver_status: str
    total_available_stock_kg: float
    available_food_kg: float
    available_water_kg: float
    total_fleet_capacity_kg: float
    active_vehicles_count: int
    total_demand_kg: float
    total_allocated_kg: float
    total_unmet_kg: float
    coverage_ratio_pct: float
    total_transit_distance_km: float
    est_total_fuel_burn_liters: float
    zones: List[ZoneLogisticsRecommendation]
    routes: List[RouteSummaryInfo]
    diagnostics: OperationalDiagnostics
    ai_executive_briefing: str
    review_status: str  # "PENDING_REVIEW", "APPROVED", "REJECTED"
    review_details: Optional[Dict[str, Any]] = None
    safety_disclaimer: str


class WhatIfScenarioRequest(BaseModel):
    scenario_title: Optional[str] = Field("Custom What-If Scenario", description="Descriptive scenario name")
    location_id: Optional[str] = Field("kamrup_metro", description="Operational location ID (e.g. 'kamrup_metro', 'barpeta')")
    custom_stock_food_kg: Optional[float] = Field(None, ge=0, description="Override depot available food")
    custom_stock_water_kg: Optional[float] = Field(None, ge=0, description="Override depot available water")
    disabled_vehicles: Optional[List[str]] = Field(default_factory=list, description="Vehicles taken out of service")
    severed_zones: Optional[List[str]] = Field(default_factory=list, description="Zones severed by flood inundation")
    demand_multiplier: Optional[float] = Field(1.0, ge=0.1, le=5.0, description="Multiplier applied to all demands")
    custom_zone_demand: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Per-zone demand overrides")
    strategy: Optional[LogisticsStrategyEnum] = Field(LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL)


class WhatIfScenarioResponse(BaseModel):
    simulated_at: str
    scenario_title: str
    strategy_used: str
    solver_status: str
    solver_runtime_ms: float
    baseline_allocated_kg: float
    simulated_allocated_kg: float
    allocated_delta_kg: float
    baseline_unmet_kg: float
    simulated_unmet_kg: float
    unmet_delta_kg: float
    baseline_distance_km: float
    simulated_distance_km: float
    distance_delta_km: float
    feasibility_status: str
    zones: List[Dict[str, Any]]
    bottlenecks: List[str]
    ai_impact_analysis: str
    database_mutated: bool = False
    disclaimer: str


class PlanReviewRequest(BaseModel):
    action: str = Field(..., description="'APPROVE' or 'REJECT'")
    operator_name: str = Field(..., min_length=2, description="Officer name e.g. Insp. S. Sharma")
    review_notes: str = Field(..., min_length=5, description="Operational justification notes")
    form_8b_reference: Optional[str] = Field("ASDMA-F8B-2026-10-04-LOG-01", description="ASDMA statutory form ref")
    disclaimer_acknowledged: bool = Field(True, description="Must acknowledge recommendations are not autonomous dispatches")


class PlanReviewResponse(BaseModel):
    success: bool
    plan_id: str
    review_status: str
    action_recorded: str
    operator_name: str
    timestamp: str
    audit_log_id: int
    form_8b_reference: str
    notes: str
    operational_next_step: str
