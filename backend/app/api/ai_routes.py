"""
RELIEFOS Lite — AI Infrastructure API Routes
Provides endpoints for AI query generation, provider health, and context inspection.
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Header, status, Depends
from fastapi.responses import JSONResponse

from app.core.auth import require_role, WRITE_ROLES

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.models.domain import AuditLogModel
from app.schemas.ai import (
    AIQueryRequest, AIStructuredResponse, AIProviderHealthResponse,
    AIContextPreviewResponse, AIContextModule, ActionReviewRequest
)
from app.services.ai.service import AIService, rate_limiter, circuit_breaker
from app.services.ai.context_service import AIContextService
from app.services.ai.providers.factory import get_configured_ai_provider
from app.services.ai.exceptions import (
    AIPromptSecurityError, AIRateLimitError, AITimeoutError, AIProviderError
)

router = APIRouter(prefix="/ai", tags=["AI Decision Support"])


@router.post(
    "/query",
    response_model=AIStructuredResponse,
    summary="Submit query for AI-assisted disaster decision support"
)
async def generate_ai_decision_guidance(
    request: AIQueryRequest,
    x_location_id: Optional[str] = Header(None, alias="X-Location-ID")
):
    """
    Submits an operational query to the safe AI decision-support engine.
    Aggregates verified database context and sensor telemetry, sanitizes against prompt injection,
    and returns a structured recommendation with empirical evidence citations and statutory Form 8B notice.
    """
    if x_location_id and (not request.location_id or request.location_id == "kamrup_metro"):
        request.location_id = x_location_id

    try:
        response = await AIService.process_query(request)
        return response
    except AIPromptSecurityError as sec_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Prompt Security Violation",
                "message": str(sec_err),
                "remediation": "Rephrase query strictly to focus on disaster logistics, shelter support, or operational flood risk."
            }
        )
    except AIRateLimitError as rl_err:
        retry_after = rl_err.details.get("retry_after_seconds", 5.0)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate Limit Exceeded",
                "message": str(rl_err),
                "retry_after_seconds": retry_after
            },
            headers={"Retry-After": str(int(retry_after))}
        )
    except AITimeoutError as to_err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={"error": "AI Provider Timeout", "message": str(to_err)}
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "AI Processing Failure", "message": str(exc)}
        )


@router.get(
    "/health",
    response_model=AIProviderHealthResponse,
    summary="Inspect AI provider status, model, and resilience telemetry"
)
async def get_ai_provider_health():
    """Returns AI provider operational status, active model, and rate limiting status."""
    settings = get_settings()
    provider = get_configured_ai_provider()

    cfg_provider = getattr(settings, "AI_PROVIDER", "mock").lower().strip()
    if circuit_breaker.state == "OPEN":
        provider_status = "ERROR"
        status_msg = f"Circuit breaker OPEN due to consecutive failures. Recovery timeout {circuit_breaker.recovery_timeout_seconds}s."
    elif provider.is_live:
        provider_status = "LIVE"
        status_msg = f"Live cloud inference active via {provider.name} ({provider.model_name})."
    elif cfg_provider != "mock":
        provider_status = "UNAVAILABLE"
        status_msg = f"Configured provider '{cfg_provider}' key unconfigured; using deterministic mock fallback."
    else:
        provider_status = "MOCK"
        status_msg = "Deterministic grounded mock engine active."

    return AIProviderHealthResponse(
        configured_provider=cfg_provider,
        effective_provider=provider.name,
        model=provider.model_name,
        is_live_provider=provider.is_live,
        provider_status=provider_status,
        status_message=status_msg,
        rate_limit_requests_per_minute=rate_limiter.max_requests,
        current_minute_requests=rate_limiter.current_load(),
        timeout_seconds=getattr(settings, "AI_TIMEOUT_SECONDS", 15.0),
        circuit_breaker_status=circuit_breaker.state,
        uptime_status="OPERATIONAL" if circuit_breaker.state != "OPEN" else "DEGRADED"
    )


@router.get(
    "/context/preview",
    response_model=AIContextPreviewResponse,
    summary="Preview compiled operational context and provenance breakdown"
)
async def preview_ai_operational_context(
    modules: Optional[str] = Query(None, description="Comma-separated module names (e.g. 'weather,gauges,inventory')"),
    zone_code: Optional[str] = Query(None, description="Optional target zone to filter (e.g. 'ZONE 01')"),
    location_id: Optional[str] = Query(None, description="Target district location ID (e.g. 'kamrup_metro', 'barpeta')"),
    x_location_id: Optional[str] = Header(None, alias="X-Location-ID")
):
    """
    Returns the real-time compiled operational context payload that is provided to the AI.
    Exposes explicit provenance labeling (LIVE, LAST_KNOWN, MANUAL, ESTIMATED) for governance audits.
    """
    effective_loc = location_id or x_location_id or "kamrup_metro"
    module_list = None
    if modules:
        parsed_modules = []
        for mod_str in modules.split(","):
            mod_clean = mod_str.strip().lower()
            try:
                parsed_modules.append(AIContextModule(mod_clean))
            except ValueError:
                pass
        if parsed_modules:
            module_list = parsed_modules

    return AIContextService.compile_full_context(
        modules=module_list,
        target_zone_code=zone_code,
        location_id=effective_loc
    )


@router.post(
    "/actions/review",
    summary="Record officer review decision on an AI-proposed operational action"
)
async def review_ai_proposed_action(
    request: ActionReviewRequest,
    current_user: Dict[str, Any] = Depends(require_role(WRITE_ROLES))
):
    """
    Records an authorized human officer sign-off decision (APPROVED or REJECTED) on an AI action.
    Persists an immutable audit log entry in the operational database conforming to ASDMA Form 8B.
    """
    decision = request.decision.strip().upper()
    if decision not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be either 'APPROVED' or 'REJECTED'."
        )

    action_label = "OFFICER_APPROVE_PROPOSED_ACTION" if decision == "APPROVED" else "OFFICER_REJECT_PROPOSED_ACTION"
    db = SessionLocal()
    audit_id = f"AUD-ACT-{request.action_id}"
    try:
        log_entry = AuditLogModel(
            operator_name=request.officer_name or "Insp. S. Sharma (EOC Planner)",
            entity_type="AI_PROPOSED_ACTION",
            entity_id=request.action_id,
            action=action_label,
            old_value="PENDING_OFFICER_REVIEW",
            new_value=decision,
            notes=request.notes or f"Officer {decision.lower()} action proposal {request.action_id}"
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        audit_id = f"AUD-{log_entry.id:04d}"
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record action review in audit log: {str(exc)}"
        )
    finally:
        db.close()

    return {
        "success": True,
        "status": f"ACTION_{decision}",
        "action_id": request.action_id,
        "decision": decision,
        "reviewed_by": request.officer_name,
        "audit_id": audit_id,
        "audit_logged": True,
        "statutory_form": "Form 8B ASDMA"
    }

