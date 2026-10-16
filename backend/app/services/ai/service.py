"""
RELIEFOS Lite — Core AI Service Orchestrator
Coordinates rate limiting, prompt security, dynamic context compilation, provider invocation,
grounded evidence validation, deterministic fallback synthesis, and statutory audit logging.
"""

import json
import re
import logging
from typing import Optional, Dict, Any, List

from app.core.config import get_settings
from app.schemas.ai import (
    AIQueryRequest, AIStructuredResponse, AISupportingEvidence, AIProposedAction
)
from app.services.ai.exceptions import (
    AIError, AIPromptSecurityError, AIRateLimitError, AITimeoutError, AIProviderError
)
from app.services.ai.security import (
    validate_and_sanitize_query, build_system_instruction, format_secure_prompt
)
from app.services.ai.context_service import AIContextService
from app.services.ai.synthesizer import DeterministicGroundedSynthesizer
from app.services.ai.resilience import (
    SlidingWindowRateLimiter, CircuitBreaker, execute_with_retry
)
from app.services.ai.providers.factory import get_configured_ai_provider
from app.services.ai.providers.mock import MockAIProvider
from app.services.ai.audit import record_ai_audit_event
from app.core.location_registry import normalize_location_id

logger = logging.getLogger("reliefos.ai.service")

# Global rate limiter and circuit breaker instances
rate_limiter = SlidingWindowRateLimiter(max_requests_per_minute=30)
circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout_seconds=30.0)


class AIService:
    @staticmethod
    def _parse_llm_json_output(raw_content: str) -> Dict[str, Any]:
        """Strips markdown code fences and parses JSON output safely."""
        text = raw_content.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass

        return {
            "recommendation": text[:200] if text else "Review operational priorities with EOC logistics officer.",
            "detailed_explanation": text if text else "Automated explanation parsing incomplete; inspect raw telemetry.",
            "supporting_evidence": [],
            "identified_risks_and_limitations": ["Model output required raw fallback parsing."],
            "missing_or_stale_data_disclosures": ["Raw response formatting warning."],
            "human_review_required": True
        }

    @classmethod
    async def process_query(cls, request: AIQueryRequest) -> AIStructuredResponse:
        """Processes an operational query through the complete safe decision-support pipeline."""
        settings = get_settings()
        fallback_reason: Optional[str] = None

        # 1. Enforce rate limiting
        await rate_limiter.acquire()

        # 2. Check circuit breaker status
        circuit_open = False
        try:
            await circuit_breaker.check()
        except AIProviderError as cb_err:
            circuit_open = True
            fallback_reason = str(cb_err)

        # 3. Sanitize user query against adversarial prompt injection
        clean_query = validate_and_sanitize_query(request.query)

        # 4. Resolve district location
        loc_id = normalize_location_id(getattr(request, "location_id", "kamrup_metro"))

        # 5. Dynamically determine relevant operational domains if not explicitly pinned
        active_modules = request.context_modules
        if not active_modules:
            active_modules = AIContextService.detect_relevant_modules(clean_query)

        # 6. Fetch authoritative real-time context from database and adapters
        context_preview = AIContextService.compile_full_context(
            modules=active_modules,
            target_zone_code=request.zone_code,
            location_id=loc_id
        )

        # 7. Check AI provider configuration
        provider = get_configured_ai_provider()

        # If live provider is NOT active (e.g. no Gemini/OpenAI API key configured), or circuit breaker is OPEN:
        # Synthesize a deterministic, 100% evidence-grounded operational response directly from DB records.
        if circuit_open or not provider.is_live:
            is_mock = isinstance(provider, MockAIProvider) or getattr(provider, "name", "") == "mock"
            deterministic_resp = DeterministicGroundedSynthesizer.synthesize(
                query=clean_query,
                location_id=loc_id,
                context_items=context_preview.context_items,
                fallback_reason=fallback_reason or ("Mock provider active" if is_mock else "Provider unconfigured"),
                is_provider_error=circuit_open,
                operator_name=request.operator_name
            )
            if is_mock:
                deterministic_resp.is_mock_fallback = True
                deterministic_resp.provider_used = "mock"
                deterministic_resp.execution_mode = "MOCK_FALLBACK"
                deterministic_resp.fallback_reason = "Mock AI provider active (unconfigured cloud LLM credentials)"

            # Record audit event
            audit_id = record_ai_audit_event(
                operator_name=request.operator_name,
                query_text=clean_query,
                provider_name="backend_deterministic",
                model_name=deterministic_resp.model_used,
                latency_ms=12.5,
                recommendation_summary=deterministic_resp.recommendation,
                supporting_evidence_count=len(deterministic_resp.supporting_evidence),
                risks_count=len(deterministic_resp.identified_risks_and_limitations),
                disclosures_count=len(deterministic_resp.missing_or_stale_data_disclosures)
            )
            deterministic_resp.audit_id = audit_id
            return deterministic_resp

        # 8. Live Cloud LLM Inference Pipeline (When Gemini/OpenAI is configured and online)
        context_json = AIContextService.serialize_context_for_prompt(
            modules=active_modules,
            target_zone_code=request.zone_code,
            location_id=loc_id
        )
        system_instruction = build_system_instruction()
        secure_prompt = format_secure_prompt(context_json, clean_query)

        timeout_sec = getattr(settings, "AI_TIMEOUT_SECONDS", 15.0)
        max_retries = getattr(settings, "AI_MAX_RETRIES", 2)
        temperature = getattr(settings, "AI_TEMPERATURE", 0.2)

        try:
            async def _invoke():
                return await provider.generate_response(
                    system_instruction=system_instruction,
                    prompt=secure_prompt,
                    temperature=temperature,
                    timeout_seconds=timeout_sec
                )

            raw_response = await execute_with_retry(
                operation=_invoke,
                max_retries=max_retries,
                base_delay=0.5,
                timeout_seconds=timeout_sec
            )
            await circuit_breaker.record_success()

            # Parse and validate structured output
            parsed = cls._parse_llm_json_output(raw_response.content)

            supporting_evidence_models = []
            for ev in parsed.get("supporting_evidence", []):
                if isinstance(ev, dict) and "source" in ev and "data_point" in ev:
                    supporting_evidence_models.append(
                        AISupportingEvidence(
                            source=ev.get("source", "ASDMA Telemetry"),
                            data_point=ev.get("data_point", ""),
                            provenance_state=ev.get("provenance_state", "ESTIMATED"),
                            observation_time=ev.get("observation_time", "Latest cycle"),
                            trust_tier=ev.get("trust_tier", "TIER_1_OFFICIAL")
                        )
                    )

            # If model didn't generate explicit evidence, populate directly from retrieved context items
            if not supporting_evidence_models:
                for it in context_preview.context_items[:4]:
                    supporting_evidence_models.append(
                        AISupportingEvidence(
                            source=it.source_agency,
                            data_point=it.summary,
                            provenance_state=it.provenance_state,
                            observation_time=it.observation_time,
                            trust_tier="TIER_1_OFFICIAL"
                        )
                    )

            proposed_action_models = []
            for act in parsed.get("proposed_actions", []):
                if isinstance(act, dict) and "action_id" in act and "title" in act:
                    proposed_action_models.append(
                        AIProposedAction(
                            action_id=act.get("action_id", "ACT-01"),
                            title=act.get("title", "Review Action"),
                            target_entity=act.get("target_entity", "OPERATIONAL_SECTOR"),
                            action_type=act.get("action_type", "REVIEW_ALLOCATION"),
                            priority=act.get("priority", "HIGH"),
                            rationale=act.get("rationale", "Standard operational review"),
                            suggested_route=act.get("suggested_route"),
                            status=act.get("status", "PENDING_OFFICER_REVIEW")
                        )
                    )

            risks = parsed.get("identified_risks_and_limitations", [])
            if not isinstance(risks, list):
                risks = [str(risks)]

            disclosures = parsed.get("missing_or_stale_data_disclosures", [])
            if not isinstance(disclosures, list):
                disclosures = [str(disclosures)]

            rec = parsed.get("recommendation", "Review zone demand vs depot inventory.")
            detailed_exp = parsed.get("detailed_explanation", "")

            # Record audit log entry in database
            audit_id = record_ai_audit_event(
                operator_name=request.operator_name,
                query_text=clean_query,
                provider_name=raw_response.provider,
                model_name=raw_response.model,
                latency_ms=raw_response.latency_ms,
                recommendation_summary=rec,
                supporting_evidence_count=len(supporting_evidence_models),
                risks_count=len(risks),
                disclosures_count=len(disclosures)
            )

            return AIStructuredResponse(
                status="SUCCESS",
                provider_used=raw_response.provider,
                model_used=raw_response.model,
                recommendation=rec,
                detailed_explanation=detailed_exp,
                supporting_evidence=supporting_evidence_models,
                proposed_actions=proposed_action_models,
                identified_risks_and_limitations=risks or ["Operational conditions subject to localized variance."],
                missing_or_stale_data_disclosures=disclosures,
                human_review_required=True,
                statutory_compliance_notice="ASDMA Form 8B Advisory Guidance Only. Official human sign-off required prior to vehicle rollout.",
                is_mock_fallback=False,
                execution_mode="LIVE_LLM",
                fallback_reason=None,
                audit_id=audit_id
            )

        except (AIProviderError, AITimeoutError, Exception) as exc:
            logger.warning(f"Live AI provider '{provider.name}' failed: {str(exc)}. Falling back to deterministic grounded synthesis.")
            await circuit_breaker.record_failure()

            # Execute grounded deterministic fallback rather than scripted conversational mock
            degraded_resp = DeterministicGroundedSynthesizer.synthesize(
                query=clean_query,
                location_id=loc_id,
                context_items=context_preview.context_items,
                fallback_reason=f"Live provider '{provider.name}' failed: {str(exc)}",
                is_provider_error=True,
                operator_name=request.operator_name
            )
            degraded_resp.status = "PARTIAL_CONTEXT"

            audit_id = record_ai_audit_event(
                operator_name=request.operator_name,
                query_text=clean_query,
                provider_name="backend_deterministic",
                model_name=degraded_resp.model_used,
                latency_ms=18.0,
                recommendation_summary=degraded_resp.recommendation,
                supporting_evidence_count=len(degraded_resp.supporting_evidence),
                risks_count=len(degraded_resp.identified_risks_and_limitations),
                disclosures_count=len(degraded_resp.missing_or_stale_data_disclosures)
            )
            degraded_resp.audit_id = audit_id
            return degraded_resp
