from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class AIContextModule(str, Enum):
    ZONES = "zones"
    WEATHER = "weather"
    GAUGES = "gauges"
    INVENTORY = "inventory"
    DEMANDS = "demands"
    ROADS = "roads"
    ALLOCATION = "allocation"
    SYSTEM_MODE = "system_mode"


class AIQueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=3,
        max_length=1500,
        description="The operational query, tactical scenario question, or evaluation request."
    )
    context_modules: Optional[List[AIContextModule]] = Field(
        default=None,
        description="Optional list of context domains to aggregate. If empty or None, all domains are aggregated."
    )
    zone_code: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Optional target operational zone code to prioritize in context (e.g. 'ZONE 01')."
    )
    location_id: Optional[str] = Field(
        default="kamrup_metro",
        max_length=50,
        description="Active district location ID (e.g. 'kamrup_metro', 'barpeta', 'cachar')."
    )
    operator_name: Optional[str] = Field(
        default="Insp. S. Sharma (EOC Planner)",
        max_length=100,
        description="Designation of the emergency operations center officer submitting the query."
    )


class AISupportingEvidence(BaseModel):
    source: str = Field(..., description="Authorizing agency or data feed (e.g., Open-Meteo, CWC, PWD Roads).")
    data_point: str = Field(..., description="Specific observation or metric cited as justification.")
    provenance_state: str = Field(..., description="Data provenance (LIVE, LAST_KNOWN, MANUAL, ESTIMATED, SIMULATED).")
    observation_time: str = Field(..., description="Timestamp or freshness label of the cited metric.")
    trust_tier: str = Field("TIER_1_OFFICIAL", description="Data confidence tier: TIER_1_OFFICIAL, TIER_2_TELEMETRY, TIER_3_ESTIMATED.")


class AIProposedAction(BaseModel):
    action_id: str = Field(..., description="Unique action tracking ID (e.g. ACT-ALLOC-01)")
    title: str = Field(..., description="Short action title (e.g. 'Review & Sign Zone 01 Dispatch Manifest')")
    target_entity: str = Field(..., description="Target sector, vehicle, or requisition code (e.g. 'ZONE 01', 'VH-01')")
    action_type: str = Field("REVIEW_ALLOCATION", description="Action type: REVIEW_ALLOCATION, VERIFY_DEMAND, APPROVE_DETOUR, REPLENISH_STOCK")
    priority: str = Field("HIGH", description="Priority tier: CRITICAL, HIGH, MEDIUM")
    rationale: str = Field(..., description="Operational reason why this action is recommended")
    suggested_route: Optional[str] = Field(None, description="Frontend navigation link (e.g. '/allocation', '/demand')")
    status: str = Field("PENDING_OFFICER_REVIEW", description="Status: PENDING_OFFICER_REVIEW, APPROVED, REJECTED")


class ActionReviewRequest(BaseModel):
    action_id: str = Field(..., min_length=2)
    decision: str = Field(..., description="Must be 'APPROVED' or 'REJECTED'")
    officer_name: Optional[str] = Field("Insp. S. Sharma (EOC Planner)")
    notes: Optional[str] = Field("")


class AIStructuredResponse(BaseModel):
    status: str = Field("SUCCESS", description="Execution status: SUCCESS, PARTIAL_CONTEXT, or FALLBACK.")
    provider_used: str = Field(..., description="Identifier of the underlying AI provider (e.g. 'gemini', 'openai', 'mock').")
    model_used: str = Field(..., description="Model descriptor (e.g., 'gemini-1.5-flash', 'gpt-4o-mini', 'deterministic-core-v1').")
    recommendation: str = Field(..., description="Concise, actionable tactical recommendation for EOC commanders.")
    detailed_explanation: str = Field(..., description="Detailed operational rationale, constraints considered, and trade-off analysis.")
    supporting_evidence: List[AISupportingEvidence] = Field(
        default_factory=list,
        description="Explicit empirical facts from verified database records and live sensors supporting this response."
    )
    proposed_actions: List[AIProposedAction] = Field(
        default_factory=list,
        description="Specific operational actions requiring officer sign-off prior to real-world execution."
    )
    identified_risks_and_limitations: List[str] = Field(
        default_factory=list,
        description="Identified operational hazards, logistical bottlenecks, and boundary conditions."
    )
    missing_or_stale_data_disclosures: List[str] = Field(
        default_factory=list,
        description="Disclosures of any data domains that are stale, unverified, or unavailable."
    )
    human_review_required: bool = Field(
        True,
        description="Mandatory statutory declaration that AI guidance requires officer review before real-world dispatch."
    )
    statutory_compliance_notice: str = Field(
        "ASDMA Decision Support System — Advisory Guidance Only. Official Form 8B officer sign-off required prior to vehicle rollout or supply release.",
        description="Statutory legal and governance declaration."
    )
    is_mock_fallback: bool = Field(False, description="Flag indicating whether response was produced by mock fallback")
    execution_mode: str = Field("LIVE_LLM", description="Execution mode: LIVE_LLM or MOCK_FALLBACK")
    fallback_reason: Optional[str] = Field(None, description="Detailed explanation if fallback was triggered")
    audit_id: str = Field(..., description="UUID or reference tracking code logged into the immutable database audit ledger.")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC creation timestamp."
    )


class AIProviderHealthResponse(BaseModel):
    configured_provider: str
    effective_provider: str
    model: str
    is_live_provider: bool
    provider_status: str = "LIVE"  # "LIVE", "MOCK", "UNAVAILABLE", "ERROR"
    status_message: str = "Provider operational"
    rate_limit_requests_per_minute: int
    current_minute_requests: int
    timeout_seconds: float
    circuit_breaker_status: str
    uptime_status: str


class ContextItem(BaseModel):
    domain: str
    title: str
    source_agency: str
    provenance_state: str
    is_live: bool
    observation_time: str
    summary: str
    raw_metrics: Dict[str, Any]


class AIContextPreviewResponse(BaseModel):
    system_mode: str
    compiled_at: str
    total_domains_compiled: int
    provenance_distribution: Dict[str, int]
    context_items: List[ContextItem]
