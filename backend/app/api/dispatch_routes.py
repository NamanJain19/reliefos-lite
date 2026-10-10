"""
RELIEFOS Lite — Dispatch Workflow API Routes
Provides endpoints for AI-assisted, human-approved dispatch manifests,
pre-dispatch safety validation, officer reviews, and state transitions.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import require_role, WRITE_ROLES
from app.models.domain import DispatchOrderModel
from app.schemas.dispatch import (
    DispatchOrderResponse, DispatchReviewRequest,
    DispatchTransitionRequest, GenerateDispatchesFromPlanRequest,
    SafetyValidationReport
)
from app.services.dispatch.dispatch_service import (
    DispatchService, InvalidStateTransitionError,
    DuplicateReviewError, DispatchWorkflowError
)
from app.services.logistics_advisor.advisor_service import LogisticsAdvisorService
from app.schemas.logistics_advisor import LogisticsStrategyEnum
from app.core.location_registry import resolve_location

router = APIRouter(prefix="/dispatch", tags=["Dispatch Management"])


@router.post(
    "/generate-from-plan",
    response_model=List[DispatchOrderResponse],
    summary="Generate reviewable dispatch orders from an OR-Tools allocation plan"
)
async def generate_dispatch_orders_from_plan(
    request: GenerateDispatchesFromPlanRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role(WRITE_ROLES))
):
    """
    Synthesizes the OR-Tools optimization plan into structured dispatch orders.
    Enforces DRY_RUN simulation mode by default and runs automated pre-dispatch safety checks.
    """
    try:
        # Retrieve optimization plan with safe enum conversion
        strategy_raw = request.strategy or "LEXICOGRAPHIC_SEVERITY_OPTIMAL"
        try:
            strategy_enum = LogisticsStrategyEnum(strategy_raw)
        except Exception:
            strategy_enum = LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL

        loc_id = getattr(request, "location_id", "kamrup_metro") or "kamrup_metro"
        plan = LogisticsAdvisorService.generate_logistics_plan(strategy=strategy_enum, location_id=loc_id)

        orders = DispatchService.generate_orders_from_plan(
            plan=plan.model_dump(),
            db=db,
            is_dry_run=request.is_dry_run,
            is_simulation=False,
            operator_name=request.operator_name or current_user.get("username", "Operator")
        )

        return [DispatchService.to_response_model(o) for o in orders]
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate dispatch orders from plan: {str(exc)}"
        )


@router.get(
    "/orders",
    response_model=List[DispatchOrderResponse],
    summary="List all dispatch manifests with optional status filtering"
)
async def list_dispatch_orders(
    status_filter: Optional[str] = Query(None, description="Filter by status (e.g. PENDING, APPROVED, READY, DISPATCHED)"),
    zone_code: Optional[str] = Query(None, description="Filter by zone code (e.g. ZONE 01)"),
    is_dry_run: Optional[bool] = Query(None, description="Filter by dry run mode"),
    loc_id: str = Depends(resolve_location),
    db: Session = Depends(get_db)
):
    """Lists dispatch manifests in descending order of creation."""
    query = db.query(DispatchOrderModel).filter(DispatchOrderModel.location_id == loc_id)

    if status_filter:
        query = query.filter(DispatchOrderModel.status == status_filter.strip().upper())
    if zone_code:
        query = query.filter(DispatchOrderModel.zone_code == zone_code.strip().upper())
    if is_dry_run is not None:
        query = query.filter(DispatchOrderModel.is_dry_run == is_dry_run)

    orders = query.order_by(DispatchOrderModel.id.desc()).all()
    return [DispatchService.to_response_model(o) for o in orders]



@router.get(
    "/orders/{dispatch_id}",
    response_model=DispatchOrderResponse,
    summary="Retrieve full details and safety report of a dispatch order"
)
async def get_dispatch_order(
    dispatch_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves single dispatch order by ID."""
    clean_id = dispatch_id.strip().upper()
    order = db.query(DispatchOrderModel).filter(DispatchOrderModel.dispatch_id == clean_id).first()
    if not order:
        raise HTTPException(status_code=404, detail=f"Dispatch order '{clean_id}' not found.")
    return DispatchService.to_response_model(order)


@router.post(
    "/orders/{dispatch_id}/review",
    response_model=DispatchOrderResponse,
    summary="Record human officer approval or rejection on a proposed dispatch manifest"
)
async def review_dispatch_order_endpoint(
    dispatch_id: str,
    request: DispatchReviewRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role(WRITE_ROLES))
):
    """
    Authorizes or rejects a proposed dispatch plan.
    Requires role COMMANDER or OPERATOR. Rejects ANALYST (403).
    Prevents duplicate reviews and logs to SQLite audit trail.
    """
    try:
        officer = request.officer_name or current_user.get("username", "Officer")
        order = DispatchService.review_order(
            dispatch_id=dispatch_id,
            decision=request.decision,
            officer_name=officer,
            notes=request.notes,
            form_8b_reference=request.form_8b_reference or "ASDMA-F8B-2026-LOG-DISPATCH",
            db=db
        )
        return DispatchService.to_response_model(order)
    except DuplicateReviewError as dup_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(dup_err))
    except DispatchWorkflowError as wf_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(wf_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post(
    "/orders/{dispatch_id}/transition",
    response_model=DispatchOrderResponse,
    summary="Advance dispatch status through the validated lifecycle"
)
async def transition_dispatch_order_endpoint(
    dispatch_id: str,
    request: DispatchTransitionRequest,
    db: Session = Depends(get_db),
    current_user: Dict[str, Any] = Depends(require_role(WRITE_ROLES))
):
    """
    Advances dispatch status (e.g. APPROVED -> READY -> DISPATCHED -> DELIVERED).
    Enforces strict state transitions and verifies human operator role permissions.
    """
    try:
        operator = request.operator_name or current_user.get("username", "Operator")
        order = DispatchService.transition_order(
            dispatch_id=dispatch_id,
            target_status=request.target_status.value,
            operator_name=operator,
            notes=request.notes or "",
            db=db,
            form_8b_reference=request.form_8b_reference
        )
        return DispatchService.to_response_model(order)
    except InvalidStateTransitionError as trans_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid State Transition",
                "message": str(trans_err),
                "current_status": trans_err.current_status,
                "target_status": trans_err.target_status,
                "allowed_transitions": trans_err.allowed
            }
        )
    except DispatchWorkflowError as wf_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(wf_err))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get(
    "/safety-check",
    response_model=SafetyValidationReport,
    summary="Run live pre-dispatch safety verification on specified parameters"
)
async def run_safety_check(
    zone_code: str = Query("ZONE 01"),
    vehicle_code: str = Query("VH-01"),
    food_kg: float = Query(1000.0),
    water_l: float = Query(700.0),
    db: Session = Depends(get_db)
):
    """Runs instant pre-dispatch safety validation against current depot inventory and road closure telemetry."""
    return DispatchService.validate_dispatch_safety(
        zone_code=zone_code,
        vehicle_code=vehicle_code,
        food_kg=food_kg,
        water_l=water_l,
        db=db
    )
