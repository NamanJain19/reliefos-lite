from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# Inventory Schemas
class StockReceiptRequest(BaseModel):
    item_sku: str = Field(..., min_length=2, max_length=50, description="SKU code of the item")
    quantity: float = Field(..., gt=0, description="Quantity received")
    batch_lot_number: str = Field(..., min_length=2, max_length=100, description="Manufacturer batch or lot number")
    expiry_date: Optional[str] = Field(None, description="Expiration date (YYYY-MM-DD)")
    reference_doc: str = Field(..., min_length=2, max_length=100, description="Delivery challan or procurement voucher number")
    operator_name: Optional[str] = Field("Insp. S. Sharma (Logistics Officer)", description="Officer receiving consignment")
    notes: Optional[str] = Field("", description="Delivery inspection remarks")


class StockAdjustmentRequest(BaseModel):
    item_sku: str = Field(..., min_length=2, max_length=50)
    adjustment_type: str = Field(..., description="AUDIT_CORRECTION, DAMAGE_WRITE_OFF, or RETURN")
    quantity_delta: float = Field(..., description="Positive for additions, negative for deductions")
    reason: str = Field(..., min_length=5, description="Justification for cycle count adjustment")
    operator_name: Optional[str] = Field("Insp. S. Sharma (Logistics Officer)")


class StockReservationRequest(BaseModel):
    item_sku: str = Field(..., min_length=2, max_length=50)
    quantity_to_reserve: float = Field(..., gt=0)
    plan_id: str = Field(..., min_length=2, max_length=100)
    notes: Optional[str] = Field("")


class StockMovementResponse(BaseModel):
    movement_id: str
    item_sku: str
    item_name: str
    depot_code: str
    movement_type: str
    quantity: float
    unit: str
    batch_lot_number: str
    expiry_date: Optional[str] = None
    balance_before: float
    balance_after: float
    reference_doc: str
    operator_name: str
    timestamp: datetime
    notes: Optional[str] = None
    location_id: str


class InventoryAlertResponse(BaseModel):
    total_low_stock_alerts: int
    total_near_expiry_alerts: int
    alerts: List[Dict[str, Any]]


# Incident Schemas
class CreateIncidentRequest(BaseModel):
    incident_type: str = Field(..., description="EMBANKMENT_BREACH, FLASH_FLOOD, ROAD_SEVERANCE, STRANDED_CLUSTER, SHELTER_OVERFLOW, LANDSLIDE")
    severity: str = Field("HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    location_desc: str = Field(..., min_length=3, max_length=255)
    latitude: float = Field(...)
    longitude: float = Field(...)
    zone_code: str = Field(..., min_length=2, max_length=50)
    reported_by: Optional[str] = Field("DDMA Field Observer")
    persons_stranded: Optional[int] = Field(0, ge=0)
    casualties_reported: Optional[int] = Field(0, ge=0)
    livestock_affected: Optional[int] = Field(0, ge=0)
    infrastructure_damaged: Optional[str] = Field("")
    response_action_taken: Optional[str] = Field("")
    assigned_team: Optional[str] = Field("SDRF 1st Battalion Guwahati")


class UpdateIncidentRequest(BaseModel):
    status: Optional[str] = Field(None, description="REPORTED, VERIFIED, IN_RESPONSE, RESOLVED, CLOSED")
    severity: Optional[str] = Field(None)
    response_action_taken: Optional[str] = Field(None)
    assigned_team: Optional[str] = Field(None)
    verified_by: Optional[str] = Field(None)
    verified_at: Optional[datetime] = Field(None)
    persons_stranded: Optional[int] = Field(None, ge=0)
    notes: Optional[str] = Field(None)


class IncidentResponse(BaseModel):
    id: int
    incident_id: str
    incident_type: str
    severity: str
    status: str
    title: str
    description: str
    location_desc: str
    latitude: float
    longitude: float
    zone_code: str
    location_id: str
    reported_by: str
    reported_at: datetime
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    casualties_reported: int
    persons_stranded: int
    livestock_affected: int
    infrastructure_damaged: Optional[str] = None
    response_action_taken: Optional[str] = None
    assigned_team: Optional[str] = None
    updated_at: datetime


# Situation Report (SitRep) Schemas
class GenerateSitRepRequest(BaseModel):
    report_date: Optional[str] = Field(None, description="YYYY-MM-DD (defaults to today)")
    time_window: Optional[str] = Field("06:00 - 18:00 IST")
    weather_synopsis: Optional[str] = Field(None)
    compiling_officer: Optional[str] = Field("Insp. S. Sharma (Logistics Officer)")


class ApproveSitRepRequest(BaseModel):
    approving_commander: str = Field(..., min_length=2, description="Commander name approving SitRep")
    notes: Optional[str] = Field("")


class SituationReportResponse(BaseModel):
    id: int
    sitrep_id: str
    report_date: str
    time_window: str
    district_name: str
    location_id: str
    active_human_lives_affected: int
    displaced_in_shelters: int
    inundated_villages_count: int
    active_shelters_count: int
    roads_closed_count: int
    critical_river_stages: List[Dict[str, Any]]
    weather_synopsis: str
    relief_distributed_summary: Dict[str, Any]
    active_incidents_count: int
    compiling_officer: str
    approving_commander: Optional[str] = None
    approval_status: str
    form_reference: str
    created_at: datetime
    approved_at: Optional[datetime] = None


# Sphere Standards Request Schema
class SphereCalculationRequest(BaseModel):
    population_affected: int = Field(..., gt=0, description="Total affected headcount in sector")
    evacuees_in_shelters: int = Field(0, ge=0, description="Registered headcount inside shelters")
    time_horizon_hours: int = Field(72, description="Planning window: 24, 72, or 168 hours")
    infant_count: Optional[int] = Field(0, ge=0)
    elderly_count: Optional[int] = Field(0, ge=0)
    contingency_buffer_pct: Optional[float] = Field(15.0, ge=0.0, le=50.0)
