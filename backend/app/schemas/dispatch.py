"""
RELIEFOS Lite — Pydantic Schemas for Human-Approved Dispatch Workflow
Enforces strict human-in-the-loop state transitions under ASDMA Form 8B regulations.
Autonomous physical dispatch is prohibited by statutory safety controls.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class DispatchStatusEnum(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    READY = "READY"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class SafetyValidationReport(BaseModel):
    is_safe: bool = Field(..., description="Whether all pre-dispatch safety constraints passed")
    inventory_sufficient: bool = Field(..., description="Depot stock covers requested quantities")
    vehicle_capacity_sufficient: bool = Field(..., description="Payload within vehicle rated capacity")
    routes_passable: bool = Field(..., description="No severed roads without detours exceeding clearance threshold")
    warnings: List[str] = Field(default_factory=list, description="Non-blocking operational advisories")
    errors: List[str] = Field(default_factory=list, description="Blocking safety violation reasons")
    validated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DispatchOrderResponse(BaseModel):
    dispatch_id: str = Field(..., description="Unique dispatch tracking ID (e.g. DSP-20261005-001)")
    plan_id: str = Field(..., description="Source logistics optimization plan ID")
    zone_code: str
    zone_name: str
    vehicle_code: str
    vehicle_name: str
    resource_type: str = "Food Rations & Potable Water"
    food_quantity_kg: float = 0.0
    water_quantity_l: float = 0.0
    total_weight_kg: float = 0.0
    destination_desc: str = ""
    route_summary: str = ""
    transit_distance_km: float = 0.0
    detour_required: bool = False
    detour_reason: Optional[str] = None
    status: DispatchStatusEnum = DispatchStatusEnum.PENDING
    is_dry_run: bool = True
    is_simulation: bool = False
    safety_validation: SafetyValidationReport
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None
    form_8b_reference: str = "ASDMA-F8B-2026-LOG-DISPATCH"
    external_connector_status: str = "DISABLED_BY_POLICY"
    allowed_next_transitions: List[str] = Field(default_factory=list)
    created_at: str
    updated_at: str


class DispatchReviewRequest(BaseModel):
    decision: str = Field(..., description="Must be 'APPROVED' or 'REJECTED'")
    officer_name: str = Field(..., min_length=2, description="Designation of reviewing officer e.g. 'Insp. S. Sharma'")
    notes: str = Field(..., min_length=3, description="Officer review notes or justification")
    form_8b_reference: Optional[str] = Field("ASDMA-F8B-2026-LOG-DISPATCH", description="Statutory ASDMA reference")
    disclaimer_acknowledged: bool = Field(True, description="Officer confirms physical safety verification")


class DispatchTransitionRequest(BaseModel):
    target_status: DispatchStatusEnum = Field(..., description="Target status: READY, DISPATCHED, DELIVERED, or CANCELLED")
    operator_name: str = Field(..., min_length=2, description="Operator designation executing transition")
    notes: Optional[str] = Field("", description="Operational shift log or carrier rollout confirmation")
    form_8b_reference: Optional[str] = Field("ASDMA-F8B-2026-LOG-DISPATCH")


class GenerateDispatchesFromPlanRequest(BaseModel):
    plan_id: Optional[str] = Field(None, description="Optional logistics plan ID to convert into dispatch orders")
    strategy: Optional[str] = Field("LEXICOGRAPHIC_SEVERITY_OPTIMAL", description="Optimization strategy to generate plan")
    is_dry_run: bool = Field(True, description="Default True: simulates dispatch workflow without mutating physical depots")
    location_id: Optional[str] = Field("kamrup_metro", description="District location ID for dispatch")
    operator_name: str = Field("Insp. S. Sharma (EOC Planner)", description="Authorizing planner")
