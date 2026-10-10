"""
RELIEFOS Lite — AI Security & Prompt Injection Defense Module
Provides prompt sanitization, pattern detection, credential redaction, and strict contextual boundary fencing.
"""

import re
from typing import Tuple
from app.services.ai.exceptions import AIPromptSecurityError

# Adversarial prompt injection keywords and delimiter breakout patterns
ADVERSARIAL_PATTERNS = [
    r"(?i)\bignore\s+(all\s+)?(previous|prior|above)\s+(instructions|directives|prompts)\b",
    r"(?i)\bdisregard\s+(all\s+)?(previous|safety|system)\s+(instructions|rules|protocols)\b",
    r"(?i)\byou\s+are\s+now\s+(unrestricted|jailbroken|DAN|in\s+developer\s+mode)\b",
    r"(?i)\bsystem\s+override\b",
    r"(?i)\bswitch\s+to\s+unfiltered\s+mode\b",
    r"(?i)\breveal\s+(your\s+)?(system\s+prompt|hidden\s+instructions|api\s+keys?)\b",
    r"(?i)\bexecute\s+(arbitrary\s+)?(sql|shell|bash|powershell|cmd)\b",
    r"(?i)<\s*/?\s*(system_instructions|verified_operational_context|user_query)\s*>",
]

# Common credential patterns for redacting sensitive secrets
CREDENTIAL_PATTERNS = [
    (r"AIza[0-9A-Za-z\-_]{25,50}", "[REDACTED_GEMINI_KEY]"),
    (r"sk-[a-zA-Z0-9_\-]{20,60}", "[REDACTED_OPENAI_KEY]"),
    (r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}", "Bearer [REDACTED_TOKEN]"),
    (r"(?i)(password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]", r"\1='[REDACTED]'"),
    (r"postgresql://[^:]+:[^@]+@", "postgresql://[REDACTED_USER]:[REDACTED_PASS]@"),
]


def redact_sensitive_credentials(text: str) -> str:
    """Removes API keys, bearer tokens, and connection credentials from text or logs."""
    if not text:
        return ""
    redacted = text
    for pattern, replacement in CREDENTIAL_PATTERNS:
        redacted = re.sub(pattern, replacement, redacted)
    return redacted


def validate_and_sanitize_query(query: str) -> str:
    """
    Validates user query against adversarial prompt injection attempts.
    Returns cleaned string if acceptable, or raises AIPromptSecurityError on severe breach.
    """
    if not query or not query.strip():
        raise AIPromptSecurityError("Query string cannot be empty.")

    cleaned = query.strip()

    # Check for adversarial injection signatures
    for pat in ADVERSARIAL_PATTERNS:
        if re.search(pat, cleaned):
            raise AIPromptSecurityError(
                "Adversarial prompt injection pattern detected. Operational queries must strictly concern disaster relief coordination."
            )

    # Sanitize XML/HTML tag breakouts to protect context enclosure
    cleaned = cleaned.replace("</", "< /")
    cleaned = cleaned.replace("```", "'''")

    # Hard length clamp (1500 chars)
    if len(cleaned) > 1500:
        cleaned = cleaned[:1500]

    return cleaned


def build_system_instruction() -> str:
    """
    Constructs the immutable statutory system instruction for RELIEFOS decision support.
    """
    return (
        "You are RELIEFOS Copilot, the AI Decision Support Engine for the Assam State Disaster Management "
        "Authority (ASDMA) and Kamrup Metropolitan Emergency Operations Center (Guwahati, Assam).\n"
        "Your role is STRICTLY ADVISORY DECISION SUPPORT under human-in-the-loop oversight.\n\n"
        "CORE OPERATIONAL RULES:\n"
        "1. Never hallucinate inventory stock, vehicle payload capacity, or road accessibility.\n"
        "2. Only cite facts present in the <verified_operational_context> XML block provided.\n"
        "3. Explicitly distinguish between LIVE sensor data, MANUAL certified readings, LAST_KNOWN baselines, "
        "ESTIMATED models, and SIMULATED drill data.\n"
        "4. If a road water depth exceeds 0.35m, it is strictly impassable for relief trucks. Never suggest crossing it.\n"
        "5. If requested data is missing, stale, or unverified, you MUST explicitly disclose this limitation.\n"
        "6. Always format recommendations in structured JSON matching the specified schema with supporting evidence, "
        "identified risks, and statutory Form 8B human-review declaration.\n"
        "7. Propose reviewable operational actions (e.g. reviewing specific allocation runs, verifying demand requisitions, approving detour routes) "
        "that require authorized officer sign-off before execution. Never attempt to autonomously execute actions."
    )


def format_secure_prompt(context_json: str, sanitized_query: str) -> str:
    """
    Encapsulates context and user query inside tamper-evident XML enclosures.
    """
    return (
        "<verified_operational_context>\n"
        f"{context_json}\n"
        "</verified_operational_context>\n\n"
        "<user_query>\n"
        f"{sanitized_query}\n"
        "</user_query>\n\n"
        "Produce your response strictly as a JSON object with the following fields:\n"
        "{\n"
        '  "recommendation": "Concise tactical guidance (1-2 sentences)",\n'
        '  "detailed_explanation": "Operational rationale citing exact numbers and constraints",\n'
        '  "supporting_evidence": [\n'
        '    {"source": "Agency name", "data_point": "Exact observation", "provenance_state": "LIVE|MANUAL|LAST_KNOWN|SIMULATED", "observation_time": "Time string", "trust_tier": "TIER_1_OFFICIAL|TIER_2_TELEMETRY|TIER_3_ESTIMATED"}\n'
        '  ],\n'
        '  "proposed_actions": [\n'
        '    {"action_id": "ACT-01", "title": "Review action title", "target_entity": "Target code", "action_type": "REVIEW_ALLOCATION|VERIFY_DEMAND|APPROVE_DETOUR|REPLENISH_STOCK", "priority": "CRITICAL|HIGH|MEDIUM", "rationale": "Reason for action", "suggested_route": "/allocation|/demand|/routes"}\n'
        '  ],\n'
        '  "identified_risks_and_limitations": ["Risk 1", "Risk 2"],\n'
        '  "missing_or_stale_data_disclosures": ["Disclosure of any unverified or stale parameters"],\n'
        '  "human_review_required": true\n'
        "}\n"
        "Ensure the output is valid, parseable JSON only. Do not wrap in markdown quotes if possible, or use standard json formatting."
    )
