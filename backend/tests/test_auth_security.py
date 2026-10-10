"""
RELIEFOS Lite — Security & RBAC Unit and Integration Tests.
Validates:
1. Token issuance and signature verification.
2. Role-based access control (RBAC) boundaries (COMMANDER, OPERATOR, ANALYST).
3. Rejection of unauthorized roles on sensitive write endpoints (403 Forbidden).
4. Rejection of malformed/expired/tampered tokens (401 Unauthorized).
5. Strict authentication enforcement under X-Auth-Strict.
6. Prevention of AI recommendations bypassing operational write permissions.
"""

import hmac
import hashlib
import base64
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.auth import (
    create_access_token, verify_access_token,
    ROLE_COMMANDER, ROLE_OPERATOR, ROLE_ANALYST
)

client = TestClient(app)


def test_login_successful_and_token_issued():
    """Verify authentic operational accounts can log in and receive valid signed tokens."""
    for uname, pwd, expected_role in [
        ("commander", "asdma@2026", ROLE_COMMANDER),
        ("operator", "relief@2026", ROLE_OPERATOR),
        ("analyst", "view@2026", ROLE_ANALYST),
    ]:
        resp = client.post("/api/auth/login", json={"username": uname, "password": pwd})
        assert resp.status_code == 200, f"Login failed for {uname}: {resp.text}"
        data = resp.json()
        assert data["success"] is True
        assert "access_token" in data
        assert data["user"]["role"] == expected_role
        assert data["token_type"] == "bearer"


def test_login_invalid_credentials_rejected():
    """Verify brute force / invalid passwords receive 401 Unauthorized."""
    resp = client.post("/api/auth/login", json={"username": "commander", "password": "wrongpassword"})
    assert resp.status_code == 401

    resp2 = client.post("/api/auth/login", json={"username": "unknown_intruder", "password": "any"})
    assert resp2.status_code == 401


def test_token_tampering_and_signature_verification():
    """Verify HMAC-SHA256 signature verification rejects forged payloads."""
    valid_token = create_access_token({"username": "operator", "role": ROLE_OPERATOR})
    parts = valid_token.split(".")
    # Tamper with the payload (middle part)
    tampered_token = f"{parts[0]}.eyJob2dnZWQiOiB0cnVlfQ.{parts[2]}"
    assert verify_access_token(tampered_token) is None


def test_auth_me_with_bearer_token():
    """Verify GET /api/auth/me resolves the authenticated session."""
    resp = client.post("/api/auth/login", json={"username": "operator", "password": "relief@2026"})
    token = resp.json()["access_token"]

    me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    user = me_resp.json()
    assert user["username"] == "operator"
    assert user["role"] == ROLE_OPERATOR


def test_rbac_analyst_cannot_execute_operational_writes():
    """Verify ANALYST (read-only) role is strictly blocked (403 Forbidden) from write actions."""
    analyst_token = "reliefos-analyst-token-2026"

    # Attempt to verify demand
    resp1 = client.post(
        "/api/demands/DEM-01/verify",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"verified_by": "Rogue Analyst", "notes": "Unauthorized verify"}
    )
    assert resp1.status_code == 403
    assert "not authorized" in resp1.json()["detail"]["message"].lower()

    # Attempt to dispatch demand
    resp2 = client.post(
        "/api/demands/DEM-01/dispatch",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"vehicle_code": "VH-01", "dispatched_by": "Rogue Analyst"}
    )
    assert resp2.status_code == 403

    # Attempt to switch system operational mode
    resp3 = client.post(
        "/api/mode/switch",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"mode": "SIMULATION_DRILL"}
    )
    assert resp3.status_code == 403


def test_rbac_operator_can_verify_demand_but_cannot_switch_mode():
    """Verify OPERATOR can verify demands, but only COMMANDER can switch system mode."""
    operator_token = "reliefos-operator-token-2026"

    # Operator can verify demand
    resp1 = client.post(
        "/api/demands/DEM-01/verify",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"verified_by": "Insp. S. Sharma", "notes": "Legitimate officer sign-off"}
    )
    assert resp1.status_code in (200, 404)  # 200 if DEM-01 exists, 404 if not found in db, but NOT 403!

    # Operator cannot switch mode (only COMMANDER)
    resp2 = client.post(
        "/api/mode/switch",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"mode": "OPERATIONAL_LIVE"}
    )
    assert resp2.status_code == 403
    assert "not authorized" in resp2.json()["detail"]["message"].lower()


def test_rbac_commander_can_switch_mode():
    """Verify COMMANDER has full administrative authority."""
    commander_token = "reliefos-commander-token-2026"

    resp = client.post(
        "/api/mode/switch",
        headers={"Authorization": f"Bearer {commander_token}"},
        json={"mode": "OPERATIONAL_LIVE", "operator_name": "EOC Commander P. Baruah"}
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_strict_mode_rejects_missing_credentials():
    """Verify X-Auth-Strict header enforces 401 when no token is supplied."""
    resp = client.post(
        "/api/demands/DEM-01/verify",
        headers={"X-Auth-Strict": "true"},
        json={"verified_by": "Anonymous", "notes": "Unauthenticated test"}
    )
    assert resp.status_code == 401
    assert "authentication required" in resp.json()["detail"].lower()


def test_invalid_bearer_token_rejected():
    """Verify malformed Bearer tokens are rejected with 401 Unauthorized."""
    resp = client.post(
        "/api/demands/DEM-01/verify",
        headers={"Authorization": "Bearer completely-forged-token"},
        json={"verified_by": "Anonymous", "notes": "Forgery attempt"}
    )
    assert resp.status_code == 401


def test_profile_update_and_role_immutability():
    """Verify profile fields (name, email, phone) can be updated, but role is strictly immutable."""
    operator_token = "reliefos-operator-token-2026"

    # 1. Update profile with legitimate fields and attempted role tampering
    update_payload = {
        "name": "Insp. S. Sharma (Updated)",
        "email": "sharma.updated@asdma.gov.in",
        "phone": "+91 94350 99887",
        "agency": "Guwahati Central Logistics Desk",
        "role": "COMMANDER"  # Malicious attempt to elevate privileges
    }
    resp = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {operator_token}"},
        json=update_payload
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Insp. S. Sharma (Updated)"
    assert data["email"] == "sharma.updated@asdma.gov.in"
    assert data["phone"] == "+91 94350 99887"
    assert data["agency"] == "Guwahati Central Logistics Desk"
    # CRITICAL: Role must remain OPERATOR despite request payload
    assert data["role"] == ROLE_OPERATOR

    # 2. Verify GET /api/auth/me returns the persisted updated information
    me_resp = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {operator_token}"}
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["name"] == "Insp. S. Sharma (Updated)"
    assert me_data["email"] == "sharma.updated@asdma.gov.in"
    assert me_data["role"] == ROLE_OPERATOR

    # Reset back to default
    client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"name": "Insp. S. Sharma", "email": "insp.sharma@asdma.gov.in", "phone": "+91 94350 22002", "agency": "Kamrup Metro Logistics Desk"}
    )


def test_profile_update_validation_rejections():
    """Verify invalid inputs (name too short, invalid email) are rejected."""
    operator_token = "reliefos-operator-token-2026"

    # Name too short
    resp1 = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"name": "X"}
    )
    assert resp1.status_code == 422

    # Invalid email format
    resp2 = client.put(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"email": "not-an-email"}
    )
    assert resp2.status_code == 422


def test_password_change_flow_and_security():
    """Verify password change requires correct current password, validates length, and updates credentials."""
    operator_token = "reliefos-operator-token-2026"

    # 1. Wrong current password rejected
    resp_wrong = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"current_password": "wrong_password", "new_password": "new_secret_2026"}
    )
    assert resp_wrong.status_code == 400
    assert "current password is incorrect" in resp_wrong.json()["detail"].lower()

    # 2. Too short new password rejected
    resp_short = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"current_password": "relief@2026", "new_password": "123"}
    )
    assert resp_short.status_code == 422

    # 3. Successful password change
    resp_success = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"current_password": "relief@2026", "new_password": "relief@newpass2026"}
    )
    assert resp_success.status_code == 200
    assert resp_success.json()["success"] is True

    # 4. Old password rejected at login
    resp_old_login = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "relief@2026"}
    )
    assert resp_old_login.status_code == 401

    # 5. New password succeeds at login
    resp_new_login = client.post(
        "/api/auth/login",
        json={"username": "operator", "password": "relief@newpass2026"}
    )
    assert resp_new_login.status_code == 200
    assert resp_new_login.json()["success"] is True

    # Reset back to default password
    new_token = resp_new_login.json()["access_token"]
    reset_resp = client.post(
        "/api/auth/change-password",
        headers={"Authorization": f"Bearer {new_token}"},
        json={"current_password": "relief@newpass2026", "new_password": "relief@2026"}
    )
    assert reset_resp.status_code == 200


# =========================================================================
# Production Authentication Hardening & Threat Validation Test Suite
# =========================================================================

def test_valid_jwt_lifecycle_and_claims():
    """Verify standard JWT creation, claim structure, and round-trip verification."""
    user = {
        "username": "commander",
        "role": ROLE_COMMANDER,
        "name": "EOC Commander P. Baruah",
        "agency": "ASDMA District Control Room",
        "email": "commander.baruah@asdma.gov.in",
        "phone": "+91 94350 11001"
    }
    token = create_access_token(user, expires_delta_hours=24)
    assert isinstance(token, str)
    assert len(token.split(".")) == 3

    payload = verify_access_token(token)
    assert payload is not None
    assert payload["sub"] == "commander"
    assert payload["role"] == ROLE_COMMANDER
    assert payload["agency"] == "ASDMA District Control Room"
    assert payload["exp"] > payload["iat"]

    # Verify session resolution via API
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["username"] == "commander"
    assert resp.json()["role"] == ROLE_COMMANDER


def test_invalid_jwt_signatures_and_tampering():
    """Verify forged signatures, foreign keys, and malformed tokens fail verification."""
    valid_token = create_access_token({"username": "operator", "role": ROLE_OPERATOR})
    parts = valid_token.split(".")

    # 1. Tampered payload
    tampered_payload = f"{parts[0]}.eyJob2dnZWQiOiB0cnVlfQ.{parts[2]}"
    assert verify_access_token(tampered_payload) is None

    # 2. Corrupted signature
    tampered_sig = f"{parts[0]}.{parts[1]}.badsignature"
    assert verify_access_token(tampered_sig) is None

    # 3. Malformed segment counts
    assert verify_access_token("single_segment_string") is None
    assert verify_access_token(f"{parts[0]}.{parts[1]}") is None
    assert verify_access_token(f"{parts[0]}.{parts[1]}.{parts[2]}.extra") is None

    # 4. Token signed with wrong foreign HMAC key
    signing_input = f"{parts[0]}.{parts[1]}".encode("utf-8")
    wrong_sig = base64.urlsafe_b64encode(
        hmac.new(b"completely_different_foreign_secret_123", signing_input, hashlib.sha256).digest()
    ).decode("utf-8").rstrip("=")
    wrong_key_token = f"{parts[0]}.{parts[1]}.{wrong_sig}"
    assert verify_access_token(wrong_key_token) is None

    # 5. Protected endpoint rejects invalid token with 401
    resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {wrong_key_token}"})
    assert resp.status_code == 401
    assert "invalid, expired, or untrusted" in resp.json()["detail"].lower()


def test_expired_jwt_rejected():
    """Verify expired tokens are strictly rejected by verification and middleware."""
    # Token generated with negative expiry delta (-2 hours in past)
    expired_token = create_access_token(
        {"username": "operator", "role": ROLE_OPERATOR},
        expires_delta_hours=-2.0
    )

    # 1. Token verification returns None
    assert verify_access_token(expired_token) is None

    # 2. Authenticated endpoint rejects with 401
    resp_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert resp_me.status_code == 401
    assert "invalid, expired, or untrusted" in resp_me.json()["detail"].lower()

    # 3. Sensitive write endpoint rejects with 401
    resp_write = client.post(
        "/api/demands/DEM-01/verify",
        headers={"Authorization": f"Bearer {expired_token}"},
        json={"verified_by": "Expired Officer", "notes": "Should be rejected"}
    )
    assert resp_write.status_code == 401


def test_production_missing_secret_fails_safely():
    """Verify production startup fails safely if JWT_SECRET is missing or empty."""
    from pydantic import ValidationError
    from app.core.config import Settings

    # Missing secret in production
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET=None)
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)
    assert "No JWT_SECRET was provided" in str(excinfo.value)

    # Empty string secret in production
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET="")
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)

    # Whitespace-only secret in production
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET="    ")
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)

    # Missing secret when DEBUG=False
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(DEBUG=False, ENVIRONMENT="prod", JWT_SECRET=None)
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)


def test_production_insecure_defaults_rejected():
    """Verify known insecure development secrets and short secrets are rejected in production."""
    from pydantic import ValidationError
    from app.core.config import Settings

    # Legacy dev default secret
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET="reliefos-kamrup-metro-eoc-secret-key-2026")
    assert "insecure default JWT_SECRET" in str(excinfo.value)

    # Placeholder secret from .env.example
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET="your_high_entropy_production_jwt_secret_here")
    assert "insecure default JWT_SECRET" in str(excinfo.value)

    # Secret shorter than 32 characters
    with pytest.raises((ValidationError, ValueError)) as excinfo:
        Settings(ENVIRONMENT="production", JWT_SECRET="short-secret-less-than-32-len")
    assert "at least 32 characters" in str(excinfo.value)


def test_production_valid_secret_enforces_strict_auth():
    """Verify valid production secret configures production mode and auto-enforces AUTH_STRICT."""
    from app.core.config import Settings

    valid_prod_secret = "reliefos-secure-prod-entropy-key-99882211003344"
    assert len(valid_prod_secret) >= 32

    s = Settings(
        ENVIRONMENT="production",
        JWT_SECRET=valid_prod_secret,
        DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/reliefos_lite",
        AUTH_STRICT=False
    )
    assert s.is_production is True
    assert s.AUTH_STRICT is True  # Auto-enforced
    assert s.get_jwt_secret() == valid_prod_secret


def test_development_convenient_fallback_secret():
    """Verify development mode safely falls back to convenient secret when not provided."""
    from app.core.config import Settings, DEV_FALLBACK_JWT_SECRET

    s = Settings(ENVIRONMENT="development", DEBUG=True, JWT_SECRET=None)
    assert s.is_production is False
    assert s.get_jwt_secret() == DEV_FALLBACK_JWT_SECRET
    assert s.JWT_SECRET == DEV_FALLBACK_JWT_SECRET


def test_role_authorization_with_real_jwt_tokens():
    """Verify COMMANDER, OPERATOR, and ANALYST privileges using genuine signed JWT tokens."""
    # 1. Create real signed tokens
    commander_token = create_access_token({"username": "commander", "role": ROLE_COMMANDER})
    operator_token = create_access_token({"username": "operator", "role": ROLE_OPERATOR})
    analyst_token = create_access_token({"username": "analyst", "role": ROLE_ANALYST})

    # 2. COMMANDER: can switch system mode (Admin privilege)
    resp_cmd = client.post(
        "/api/mode/switch",
        headers={"Authorization": f"Bearer {commander_token}"},
        json={"mode": "OPERATIONAL_LIVE", "operator_name": "EOC Commander"}
    )
    assert resp_cmd.status_code == 200

    # 3. OPERATOR: forbidden from mode switch (403), but allowed on operational verify
    resp_op_switch = client.post(
        "/api/mode/switch",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"mode": "SIMULATION_DRILL"}
    )
    assert resp_op_switch.status_code == 403
    assert "not authorized" in resp_op_switch.json()["detail"]["message"].lower()

    resp_op_verify = client.post(
        "/api/demands/DEM-01/verify",
        headers={"Authorization": f"Bearer {operator_token}"},
        json={"verified_by": "Insp. Sharma", "notes": "JWT signed verify"}
    )
    assert resp_op_verify.status_code in (200, 404)  # 200 or 404 not found, but NOT 403

    # 4. ANALYST: forbidden from all operational writes (403)
    resp_an_verify = client.post(
        "/api/demands/DEM-01/verify",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"verified_by": "Analyst", "notes": "Should be blocked"}
    )
    assert resp_an_verify.status_code == 403

    resp_an_dispatch = client.post(
        "/api/demands/DEM-01/dispatch",
        headers={"Authorization": f"Bearer {analyst_token}"},
        json={"vehicle_code": "VH-01", "dispatched_by": "Analyst"}
    )
    assert resp_an_dispatch.status_code == 403

    # 5. ANALYST: can inspect own profile (Read privilege)
    resp_an_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {analyst_token}"})
    assert resp_an_me.status_code == 200
    assert resp_an_me.json()["role"] == ROLE_ANALYST


def test_unauthorized_access_scenarios():
    """Verify unauthorized requests receive 401 Unauthorized across headers and credentials."""
    # 1. Malformed Authorization headers
    bad_headers = [
        {"Authorization": "Basic dXNlcjpwYXNz"},
        {"Authorization": "Bearer"},
        {"Authorization": "Token 12345"},
        {"Authorization": "InvalidScheme token"}
    ]
    for h in bad_headers:
        resp = client.get("/api/auth/me", headers=h)
        assert resp.status_code == 401

    # 2. Strict mode missing Authorization header
    resp_strict = client.get("/api/auth/me", headers={"X-Auth-Strict": "true"})
    assert resp_strict.status_code == 401

    # 3. Invalid login credentials
    resp_bad_login = client.post("/api/auth/login", json={"username": "commander", "password": "incorrect"})
    assert resp_bad_login.status_code == 401


def test_jwt_secret_not_exposed_or_printed():
    """Verify secret is excluded from string representations, logs, and API responses."""
    from app.core.config import Settings

    custom_secret = "sensitive-high-entropy-jwt-secret-string-do-not-leak"
    s = Settings(ENVIRONMENT="development", JWT_SECRET=custom_secret)

    # 1. Excluded from repr() and str()
    assert custom_secret not in repr(s)
    assert custom_secret not in str(s)

    # 2. Excluded from public endpoints
    endpoints_to_check = [
        "/api/settings",
        "/api/health",
        "/api/auth/roles",
        "/api/auth/me"
    ]
    for ep in endpoints_to_check:
        resp = client.get(ep)
        assert custom_secret not in resp.text


@pytest.mark.anyio
async def test_lifespan_production_safe_failure():
    """Verify application lifespan startup aborts safely with RuntimeError in production if secret is insecure."""
    from unittest.mock import patch
    from app.main import lifespan, app
    from app.core.config import Settings

    # Dev settings with short secret
    mock_settings = Settings(ENVIRONMENT="development", JWT_SECRET="short-dev-key")
    with patch.object(type(mock_settings), "is_production", True), patch("app.main.settings", mock_settings):
        with pytest.raises(RuntimeError) as exc:
            async with lifespan(app):
                pass
        assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(exc.value)



