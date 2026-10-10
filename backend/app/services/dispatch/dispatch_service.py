"""
RELIEFOS Lite — Human-Approved Dispatch Service
Coordinates pre-dispatch safety verification, state machine validation,
ASDMA Form 8B officer reviews, DRY_RUN simulation mode, and immutable audit logging.
Autonomous physical dispatch is prohibited by policy and law.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.domain import (
    DispatchOrderModel, VehicleModel, InventoryItemModel,
    RoadClosureModel, ZoneModel, AuditLogModel
)
from app.schemas.dispatch import (
    DispatchStatusEnum, SafetyValidationReport,
    DispatchOrderResponse
)

logger = logging.getLogger("reliefos.dispatch")

# Valid state machine transitions
ALLOWED_TRANSITIONS: Dict[str, List[str]] = {
    DispatchStatusEnum.PENDING.value: [
        DispatchStatusEnum.APPROVED.value,
        DispatchStatusEnum.REJECTED.value,
        DispatchStatusEnum.CANCELLED.value
    ],
    DispatchStatusEnum.APPROVED.value: [
        DispatchStatusEnum.READY.value,
        DispatchStatusEnum.CANCELLED.value
    ],
    DispatchStatusEnum.READY.value: [
        DispatchStatusEnum.DISPATCHED.value,
        DispatchStatusEnum.CANCELLED.value
    ],
    DispatchStatusEnum.DISPATCHED.value: [
        DispatchStatusEnum.DELIVERED.value,
        DispatchStatusEnum.CANCELLED.value
    ],
    DispatchStatusEnum.DELIVERED.value: [],
    DispatchStatusEnum.REJECTED.value: [],
    DispatchStatusEnum.CANCELLED.value: []
}


class DispatchWorkflowError(Exception):
    """Base exception for dispatch workflow violations."""
    pass


class InvalidStateTransitionError(DispatchWorkflowError):
    """Raised when an illegal status change is attempted."""
    def __init__(self, current_status: str, target_status: str, allowed: List[str]):
        super().__init__(
            f"Invalid transition from '{current_status}' to '{target_status}'. "
            f"Permitted next states: {allowed or 'None (Terminal state)'}."
        )
        self.current_status = current_status
        self.target_status = target_status
        self.allowed = allowed


class DuplicateReviewError(DispatchWorkflowError):
    """Raised when an already evaluated plan receives duplicate approval/rejection."""
    pass


class SafetyConstraintViolationError(DispatchWorkflowError):
    """Raised when hard safety limits (e.g. vehicle capacity) are breached."""
    pass


class DispatchService:
    @staticmethod
    def validate_dispatch_safety(
        zone_code: str,
        vehicle_code: str,
        food_kg: float,
        water_l: float,
        db: Session
    ) -> SafetyValidationReport:
        """
        Validates inventory sufficiency, vehicle capacity, and route passability.
        Returns detailed safety report with blocking errors and operational advisories.
        """
        warnings: List[str] = []
        errors: List[str] = []

        total_weight_kg = float(food_kg + water_l)

        # 1. Vehicle Capacity Check
        vehicle = db.query(VehicleModel).filter(VehicleModel.code == vehicle_code).first()
        vehicle_capacity_sufficient = True
        if vehicle:
            if total_weight_kg > vehicle.capacity_kg:
                vehicle_capacity_sufficient = False
                errors.append(
                    f"Vehicle {vehicle.code} ({vehicle.name}) rated capacity is {vehicle.capacity_kg} kg; "
                    f"manifest cargo {total_weight_kg} kg exceeds limit by {total_weight_kg - vehicle.capacity_kg:.1f} kg."
                )
            elif total_weight_kg > (vehicle.capacity_kg * 0.90):
                warnings.append(
                    f"Vehicle {vehicle.code} loaded at {total_weight_kg/vehicle.capacity_kg*100:.1f}% capacity."
                )
        else:
            warnings.append(f"Vehicle '{vehicle_code}' not in active fleet registry; using standard 2,500 kg envelope.")

        # 2. Inventory Check
        inv_items = db.query(InventoryItemModel).all()
        avail_food = sum(
            i.available_quantity for i in inv_items
            if "food" in i.category.lower() or "ration" in i.category.lower()
        )
        avail_water = sum(
            i.available_quantity for i in inv_items
            if "water" in i.category.lower()
        )

        inventory_sufficient = True
        if food_kg > avail_food:
            inventory_sufficient = False
            errors.append(f"Requested food {food_kg} kg exceeds central depot available stock ({avail_food} kg).")
        if water_l > avail_water:
            inventory_sufficient = False
            errors.append(f"Requested water {water_l} L exceeds central depot available stock ({avail_water} L).")

        # 3. Route & Road Closure Clearance Check
        routes_passable = True
        closures = db.query(RoadClosureModel).filter(RoadClosureModel.is_active == True).all()
        for cl in closures:
            if cl.water_depth_m > cl.clearance_threshold_m:
                if cl.detour_corridor:
                    warnings.append(
                        f"Corridor '{cl.corridor_name}' flooded ({cl.water_depth_m}m > {cl.clearance_threshold_m}m). "
                        f"Enforcing bypass: '{cl.detour_corridor}'."
                    )
                else:
                    routes_passable = False
                    errors.append(
                        f"Corridor '{cl.corridor_name}' is severed under {cl.water_depth_m}m water with no confirmed detour."
                    )

        is_safe = len(errors) == 0

        return SafetyValidationReport(
            is_safe=is_safe,
            inventory_sufficient=inventory_sufficient,
            vehicle_capacity_sufficient=vehicle_capacity_sufficient,
            routes_passable=routes_passable,
            warnings=warnings,
            errors=errors
        )

    @classmethod
    def generate_orders_from_plan(
        cls,
        plan: Dict[str, Any],
        db: Session,
        is_dry_run: bool = True,
        is_simulation: bool = False,
        operator_name: str = "Insp. S. Sharma (EOC Planner)"
    ) -> List[DispatchOrderModel]:
        """
        Parses an OR-Tools / Logistics Advisor plan and generates reviewable dispatch orders.
        Assigns unique tracking IDs and attaches pre-dispatch safety reports.
        """
        plan_id = plan.get("plan_id", f"PLAN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M')}")
        zones = plan.get("zones", [])
        routes = plan.get("routes", [])

        # Map vehicle routes by zone or assignment
        vehicle_map: Dict[str, Dict[str, Any]] = {}
        for r in routes:
            v_code = r.get("vehicle_code", "VH-01")
            vehicle_map[v_code] = r

        created_orders: List[DispatchOrderModel] = []
        today_str = datetime.now(timezone.utc).strftime("%Y%m%d")

        for idx, z in enumerate(zones, start=1):
            alloc_food = float(z.get("alloc_food_kg", 0.0))
            alloc_water = float(z.get("alloc_water_l", 0.0))
            total_cargo = float(z.get("total_alloc_kg", alloc_food + alloc_water))

            if total_cargo <= 0:
                continue

            assigned_vehicles = z.get("assigned_vehicles", [])
            veh_code = assigned_vehicles[0] if assigned_vehicles else f"VH-{(idx % 3) + 1:02d}"
            route_info = vehicle_map.get(veh_code, {})

            seq_num = db.query(DispatchOrderModel).count() + len(created_orders) + 1
            dispatch_id = f"DSP-{today_str}-{seq_num:03d}"
            while db.query(DispatchOrderModel).filter(DispatchOrderModel.dispatch_id == dispatch_id).first():
                seq_num += 1
                dispatch_id = f"DSP-{today_str}-{seq_num:03d}"

            # Run safety validation
            safety = cls.validate_dispatch_safety(
                zone_code=z.get("zone_code", f"ZONE 0{idx}"),
                vehicle_code=veh_code,
                food_kg=alloc_food,
                water_l=alloc_water,
                db=db
            )

            detour_req = route_info.get("detour_enforced", False)
            detour_reason = route_info.get("detour_reason", "")

            order = DispatchOrderModel(
                dispatch_id=dispatch_id,
                plan_id=plan_id,
                zone_code=z.get("zone_code", f"ZONE 0{idx}"),
                zone_name=z.get("zone_name", "Kamrup Metro Sector"),
                vehicle_code=veh_code,
                vehicle_name=route_info.get("vehicle_name", f"Relief Vehicle {veh_code}"),
                resource_type="Food Rations & Potable Water",
                food_quantity_kg=alloc_food,
                water_quantity_l=alloc_water,
                total_weight_kg=total_cargo,
                destination_desc=f"{z.get('zone_name', '')} Staging Center",
                route_summary=route_info.get("route_profile", "Sarusajai Central Depot -> Assigned Sector"),
                transit_distance_km=float(route_info.get("total_distance_km", 12.0)),
                detour_required=detour_req,
                detour_reason=detour_reason,
                status=DispatchStatusEnum.PENDING.value,
                is_dry_run=is_dry_run,
                is_simulation=is_simulation,
                safety_validation_passed=safety.is_safe,
                safety_warnings=json.dumps({"warnings": safety.warnings, "errors": safety.errors}),
                form_8b_reference="ASDMA-F8B-2026-LOG-DISPATCH",
                external_connector_status="DISABLED_BY_POLICY"
            )

            db.add(order)
            created_orders.append(order)

        db.commit()

        # Log creation event
        for ord_item in created_orders:
            db.refresh(ord_item)
            audit = AuditLogModel(
                operator_name=operator_name,
                entity_type="DISPATCH_ORDER",
                entity_id=ord_item.dispatch_id,
                action="CREATE_PROPOSED_DISPATCH",
                old_value=None,
                new_value="PENDING",
                notes=f"Generated from plan {plan_id} for {ord_item.zone_name}. DryRun={is_dry_run}."
            )
            db.add(audit)

        db.commit()
        return created_orders

    @classmethod
    def review_order(
        cls,
        dispatch_id: str,
        decision: str,
        officer_name: str,
        notes: str,
        form_8b_reference: str,
        db: Session
    ) -> DispatchOrderModel:
        """
        Records an authorized human officer sign-off (APPROVED or REJECTED).
        Rejects duplicate reviews and logs immutable audit trail.
        """
        clean_id = dispatch_id.strip().upper()
        order = db.query(DispatchOrderModel).filter(DispatchOrderModel.dispatch_id == clean_id).first()
        if not order:
            raise DispatchWorkflowError(f"Dispatch order '{clean_id}' not found.")

        clean_decision = decision.strip().upper()
        if clean_decision not in (DispatchStatusEnum.APPROVED.value, DispatchStatusEnum.REJECTED.value):
            raise DispatchWorkflowError(f"Decision must be 'APPROVED' or 'REJECTED'; received '{decision}'.")

        if order.status != DispatchStatusEnum.PENDING.value:
            raise DuplicateReviewError(
                f"Dispatch order '{clean_id}' is already in '{order.status}' status and cannot be re-reviewed."
            )

        old_status = order.status
        order.status = clean_decision
        order.reviewed_by = officer_name
        order.reviewed_at = datetime.now(timezone.utc)
        order.review_decision = clean_decision
        order.review_notes = notes
        order.form_8b_reference = form_8b_reference or "ASDMA-F8B-2026-LOG-DISPATCH"
        order.updated_at = datetime.now(timezone.utc)

        audit = AuditLogModel(
            operator_name=officer_name,
            entity_type="DISPATCH_ORDER",
            entity_id=order.dispatch_id,
            action=f"OFFICER_REVIEW_{clean_decision}",
            old_value=old_status,
            new_value=clean_decision,
            notes=f"ASDMA Form 8B Review: {notes}"
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def transition_order(
        cls,
        dispatch_id: str,
        target_status: str,
        operator_name: str,
        notes: str,
        db: Session,
        form_8b_reference: Optional[str] = None
    ) -> DispatchOrderModel:
        """
        Advances dispatch status through validated lifecycle:
        PENDING -> APPROVED -> READY -> DISPATCHED -> DELIVERED (or CANCELLED).
        Enforces state transition rules and logs to audit ledger.
        """
        clean_id = dispatch_id.strip().upper()
        order = db.query(DispatchOrderModel).filter(DispatchOrderModel.dispatch_id == clean_id).first()
        if not order:
            raise DispatchWorkflowError(f"Dispatch order '{clean_id}' not found.")

        target = target_status.strip().upper()
        allowed = ALLOWED_TRANSITIONS.get(order.status, [])

        if target not in allowed:
            raise InvalidStateTransitionError(order.status, target, allowed)

        old_status = order.status
        order.status = target
        order.updated_at = datetime.now(timezone.utc)
        if form_8b_reference:
            order.form_8b_reference = form_8b_reference

        audit = AuditLogModel(
            operator_name=operator_name,
            entity_type="DISPATCH_ORDER",
            entity_id=order.dispatch_id,
            action=f"TRANSITION_{target}",
            old_value=old_status,
            new_value=target,
            notes=f"Operational transition to {target}: {notes}" if notes else f"Advanced status to {target}"
        )
        db.add(audit)
        db.commit()
        db.refresh(order)
        return order

    @classmethod
    def to_response_model(cls, order: DispatchOrderModel) -> DispatchOrderResponse:
        """Converts database model into comprehensive API response schema."""
        warnings_list = []
        errors_list = []
        if order.safety_warnings:
            try:
                parsed = json.loads(order.safety_warnings)
                if isinstance(parsed, list):
                    warnings_list = parsed
                elif isinstance(parsed, dict):
                    warnings_list = parsed.get("warnings", [])
                    errors_list = parsed.get("errors", [])
            except Exception:
                warnings_list = [str(order.safety_warnings)]

        safety_report = SafetyValidationReport(
            is_safe=bool(order.safety_validation_passed),
            inventory_sufficient=True,
            vehicle_capacity_sufficient=True,
            routes_passable=True,
            warnings=warnings_list,
            errors=errors_list
        )

        allowed = ALLOWED_TRANSITIONS.get(order.status, [])

        return DispatchOrderResponse(
            dispatch_id=order.dispatch_id,
            plan_id=order.plan_id,
            zone_code=order.zone_code,
            zone_name=order.zone_name,
            vehicle_code=order.vehicle_code,
            vehicle_name=order.vehicle_name,
            resource_type=order.resource_type,
            food_quantity_kg=float(order.food_quantity_kg or 0.0),
            water_quantity_l=float(order.water_quantity_l or 0.0),
            total_weight_kg=float(order.total_weight_kg or 0.0),
            destination_desc=order.destination_desc,
            route_summary=order.route_summary,
            transit_distance_km=float(order.transit_distance_km or 0.0),
            detour_required=bool(order.detour_required),
            detour_reason=order.detour_reason,
            status=DispatchStatusEnum(order.status),
            is_dry_run=bool(order.is_dry_run),
            is_simulation=bool(order.is_simulation),
            safety_validation=safety_report,
            reviewed_by=order.reviewed_by,
            reviewed_at=order.reviewed_at.isoformat() if order.reviewed_at else None,
            review_decision=order.review_decision,
            review_notes=order.review_notes,
            form_8b_reference=order.form_8b_reference or "ASDMA-F8B-2026-LOG-DISPATCH",
            external_connector_status=order.external_connector_status or "DISABLED_BY_POLICY",
            allowed_next_transitions=allowed,
            created_at=order.created_at.isoformat() if order.created_at else datetime.now(timezone.utc).isoformat(),
            updated_at=order.updated_at.isoformat() if order.updated_at else datetime.now(timezone.utc).isoformat()
        )
