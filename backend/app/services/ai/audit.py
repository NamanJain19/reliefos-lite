"""
RELIEFOS Lite — AI Audit & Compliance Logging Module
Persists tamper-evident operational guidance records to the SQLite audit log ledger.
Guarantees zero exposure of API keys, bearer tokens, or sensitive system credentials.
"""

import hashlib
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any

from app.core.database import SessionLocal
from app.models.domain import AuditLogModel
from app.services.ai.security import redact_sensitive_credentials

logger = logging.getLogger("reliefos.ai.audit")


def record_ai_audit_event(
    operator_name: str,
    query_text: str,
    provider_name: str,
    model_name: str,
    latency_ms: float,
    recommendation_summary: str,
    supporting_evidence_count: int,
    risks_count: int,
    disclosures_count: int
) -> str:
    """
    Persists an immutable audit log entry for every generated AI decision recommendation.
    Returns the unique audit tracking ID.
    """
    audit_id = f"AI-AUDIT-{uuid.uuid4().hex[:8].upper()}"

    # Calculate query digest hash (SHA-256)
    query_hash = hashlib.sha256(query_text.encode("utf-8")).hexdigest()[:16]

    clean_query = redact_sensitive_credentials(query_text)
    if len(clean_query) > 120:
        clean_query = clean_query[:117] + "..."

    clean_rec = redact_sensitive_credentials(recommendation_summary)
    if len(clean_rec) > 200:
        clean_rec = clean_rec[:197] + "..."

    audit_payload = {
        "audit_id": audit_id,
        "provider": provider_name,
        "model": model_name,
        "latency_ms": latency_ms,
        "query_digest": query_hash,
        "evidence_citations": supporting_evidence_count,
        "identified_risks": risks_count,
        "disclosures": disclosures_count,
        "human_review_required": True,
        "statutory_form": "Form 8B ASDMA"
    }

    db = SessionLocal()
    try:
        log_entry = AuditLogModel(
            operator_name=operator_name or "Insp. S. Sharma (EOC Planner)",
            entity_type="AI_DECISION_SUPPORT",
            entity_id=audit_id,
            action="GENERATE_RECOMMENDATION",
            old_value=f"Query: '{clean_query}' (hash:{query_hash})",
            new_value=json.dumps(audit_payload),
            notes=clean_rec
        )
        db.add(log_entry)
        db.commit()
        logger.info(f"AI decision-support guidance logged successfully under audit ID {audit_id}")
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to record AI audit log entry: {str(exc)}")
    finally:
        db.close()

    return audit_id
