"""
RELIEFOS Lite — AI-Assisted Resource Allocation & Logistics Advisor API Endpoints.
Provides decision-support endpoints for reviewable logistics plans, multi-strategy comparisons,
operator what-if simulations, and Form 8B human review sign-offs.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Query, HTTPException, status, Depends

from app.core.auth import require_role, WRITE_ROLES
from app.core.location_registry import resolve_location

from app.schemas.logistics_advisor import (
    LogisticsStrategyEnum, LogisticsAdvisorPlanResponse,
    AlternativeStrategyComparisonItem, WhatIfScenarioRequest,
    WhatIfScenarioResponse, PlanReviewRequest, PlanReviewResponse
)
from app.services.logistics_advisor.advisor_service import LogisticsAdvisorService
from app.services.logistics_advisor.strategies import compare_all_four_strategies

router = APIRouter(prefix="/logistics-advisor", tags=["AI Logistics Advisor"])


@router.get("/plan", response_model=LogisticsAdvisorPlanResponse)
async def get_logistics_plan(
    strategy: Optional[LogisticsStrategyEnum] = Query(
        LogisticsStrategyEnum.LEXICOGRAPHIC_SEVERITY_OPTIMAL,
        description="Select mathematical allocation strategy"
    ),
    loc_id: str = Depends(resolve_location)
):
    """
    Retrieves the reviewable AI-assisted logistics plan calculated using Google OR-Tools CP-SAT
    and NetworkX/OSRM routing. Includes zone allocations, vehicle routes, shelter mappings,
    operational diagnostics, and AI Copilot explanations.
    """
    try:
        return LogisticsAdvisorService.generate_logistics_plan(strategy=strategy, location_id=loc_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate logistics plan: {str(e)}"
        )


@router.get("/strategies", response_model=List[AlternativeStrategyComparisonItem])
async def get_strategy_comparisons(
    loc_id: str = Depends(resolve_location)
):
    """
    Executes and compares all 4 mathematical allocation strategies side-by-side using OR-Tools CP-SAT:
    1. Lexicographic Severity Optimal (ASDMA Recommended)
    2. Proportional Equal Share (Uniform Equity)
    3. Distance Minimizing Proximity (Rapid Turnaround)
    4. Water-First Survival (Hydration Priority)
    """
    try:
        ctx = LogisticsAdvisorService.get_verified_operational_context(location_id=loc_id)
        return compare_all_four_strategies(
            zones=ctx["zones"],
            depot=ctx["depot"],
            vehicles=ctx["vehicles"],
            unreachable_zones=ctx["unreachable_zones"]
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Strategy comparison computation failed: {str(e)}"
        )


@router.post("/what-if", response_model=WhatIfScenarioResponse)
async def simulate_what_if_scenario(
    req: WhatIfScenarioRequest,
    loc_id: str = Depends(resolve_location)
):
    """
    Executes an operator-defined what-if simulation in an isolated in-memory sandbox.
    Supports custom stock levels, disabled vehicles, severed zones, and demand surges.
    Strictly guarantees ZERO changes to live database records.
    """
    try:
        if not req.location_id or req.location_id == "kamrup_metro":
            req.location_id = loc_id
        return LogisticsAdvisorService.execute_what_if_scenario(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"What-if simulation failed: {str(e)}"
        )


@router.post("/review", response_model=PlanReviewResponse)
async def review_and_sign_off_plan(
    req: PlanReviewRequest,
    current_user: Dict[str, Any] = Depends(require_role(WRITE_ROLES))
):
    """
    Records an operational human review and sign-off (APPROVE / REJECT) for the logistics plan.
    Logs an immutable audit record to the SQLite database.
    Does NOT autonomously dispatch vehicles or decrement warehouse inventory.
    """
    try:
        return LogisticsAdvisorService.record_plan_review(req)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record plan review: {str(e)}"
        )
