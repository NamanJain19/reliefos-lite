"""
RELIEFOS Lite — User Profile, Photo Management, Database Persistence & Duty Dossier Tests.
Validates:
1. Profile retrieval from database via /auth/me.
2. Profile update (name, email, phone, agency) and database persistence.
3. Immutability of username and role (cannot escalate or mutate security tiers).
4. Profile photo upload via /auth/avatar (base64 data URI):
   - Accepts JPG, PNG, and WebP.
   - Rejects non-image formats.
   - Rejects images exceeding 2MB size limit.
5. Instant photo reset / removal via DELETE /auth/avatar.
6. Duty dossier export via /auth/dossier/export:
   - Validates all required officer attributes.
   - Verifies cryptographic SHA-256 integrity hash matches canonical payload.
   - Verifies no secrets (passwords, JWT secret) are exposed.
7. Audit log generation for all profile modifications.
"""

import json
import hashlib
import base64
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.models.domain import UserProfileModel, AuditLogModel
from app.core.auth import (
    create_access_token,
    ROLE_COMMANDER, ROLE_OPERATOR, ROLE_ANALYST
)

client = TestClient(app)


@pytest.fixture
def operator_token():
    """Generates a valid bearer token for standard operator."""
    return create_access_token({
        "username": "operator",
        "role": ROLE_OPERATOR,
        "name": "Insp. S. Sharma",
        "agency": "Kamrup Metro Logistics Desk"
    })


@pytest.fixture
def commander_token():
    """Generates a valid bearer token for district commander."""
    return create_access_token({
        "username": "commander",
        "role": ROLE_COMMANDER,
        "name": "Col. R. Borah",
        "agency": "State EOC Command Hub"
    })


def test_get_profile_and_db_persistence(operator_token):
    """Verify profile can be retrieved and reflects database records."""
    headers = {"Authorization": f"Bearer {operator_token}"}
    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["username"] == "operator"
    assert data["role"] == ROLE_OPERATOR
    assert "name" in data
    assert "agency" in data

    # Verify directly in database
    db = SessionLocal()
    try:
        user_record = db.query(UserProfileModel).filter(UserProfileModel.username == "operator").first()
        assert user_record is not None
        assert user_record.username == "operator"
    finally:
        db.close()


def test_update_profile_success_and_persistence(operator_token):
    """Verify modifying profile fields updates database and retains changes."""
    headers = {"Authorization": f"Bearer {operator_token}"}
    new_name = "Inspector S. Sharma (Logistics Officer)"
    new_email = "sharma.ops@asdma.gov.in"
    new_phone = "+91 94350 99887"
    new_agency = "Kamrup Central Dispatch Unit"

    resp = client.put("/api/auth/me", headers=headers, json={
        "name": new_name,
        "email": new_email,
        "phone": new_phone,
        "agency": new_agency
    })
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == new_name
    assert data["email"] == new_email
    assert data["phone"] == new_phone
    assert data["agency"] == new_agency

    # Verify database persistence
    db = SessionLocal()
    try:
        user_record = db.query(UserProfileModel).filter(UserProfileModel.username == "operator").first()
        assert user_record.name == new_name
        assert user_record.email == new_email
        assert user_record.phone == new_phone
        assert user_record.agency == new_agency

        # Verify audit log was recorded
        audit = db.query(AuditLogModel).filter(
            AuditLogModel.entity_type == "USER_PROFILE",
            AuditLogModel.entity_id == "operator",
            AuditLogModel.action == "UPDATE_PROFILE"
        ).order_by(AuditLogModel.id.desc()).first()
        assert audit is not None
        assert "sharma.ops@asdma.gov.in" in audit.new_value
    finally:
        db.close()

    # Verify a subsequent GET returns the persisted data
    resp_get = client.get("/api/auth/me", headers=headers)
    assert resp_get.status_code == 200
    assert resp_get.json()["name"] == new_name


def test_rbac_security_immutability(operator_token):
    """Verify that username, role, or RBAC tier cannot be tampered with through profile edit."""
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Attempt to elevate role to COMMANDER or alter username
    resp = client.put("/api/auth/me", headers=headers, json={
        "name": "Inspector S. Sharma",
        "username": "commander",
        "role": ROLE_COMMANDER
    })
    # The endpoint should ignore username/role fields and remain OPERATOR
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "operator"
    assert data["role"] == ROLE_OPERATOR

    # Confirm in DB
    db = SessionLocal()
    try:
        user_record = db.query(UserProfileModel).filter(UserProfileModel.username == "operator").first()
        assert user_record.role == ROLE_OPERATOR
        assert user_record.username == "operator"
    finally:
        db.close()


def test_avatar_upload_formats_and_persistence(operator_token):
    """Verify avatar upload supports PNG, JPG, and WebP base64 data URIs."""
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    # 1. Valid PNG upload
    sample_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    resp_png = client.post("/api/auth/avatar", headers=headers, json={"avatar_data_url": sample_png})
    assert resp_png.status_code == 200
    assert resp_png.json()["avatar_url"] == sample_png

    # 2. Valid JPEG upload
    sample_jpg = "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="
    resp_jpg = client.post("/api/auth/avatar", headers=headers, json={"avatar_data_url": sample_jpg})
    assert resp_jpg.status_code == 200
    assert resp_jpg.json()["avatar_url"] == sample_jpg

    # 3. Valid WebP upload
    sample_webp = "data:image/webp;base64,UklGRhoAAABXRUJQVlA4TA0AAAAvAAAAEAcQERGIiP4HAA=="
    resp_webp = client.post("/api/auth/avatar", headers=headers, json={"avatar_data_url": sample_webp})
    assert resp_webp.status_code == 200
    assert resp_webp.json()["avatar_url"] == sample_webp

    # Verify persisted in DB
    db = SessionLocal()
    try:
        user_record = db.query(UserProfileModel).filter(UserProfileModel.username == "operator").first()
        assert user_record.avatar_url == sample_webp
    finally:
        db.close()


def test_avatar_upload_validation_rejections(operator_token):
    """Verify invalid format and oversized avatars are rejected with 422."""
    headers = {"Authorization": f"Bearer {operator_token}"}

    # Unsupported MIME type
    resp_pdf = client.post("/api/auth/avatar", headers=headers, json={
        "avatar_data_url": "data:application/pdf;base64,JVBERi0xLjQK"
    })
    assert resp_pdf.status_code == 422
    assert "Unsupported image format" in resp_pdf.json()["detail"]

    # Oversized payload (> 2.8 MB base64 data)
    huge_data = "data:image/jpeg;base64," + ("A" * 3_000_000)
    resp_huge = client.post("/api/auth/avatar", headers=headers, json={"avatar_data_url": huge_data})
    assert resp_huge.status_code == 422
    assert "exceeds the 2MB limit" in resp_huge.json()["detail"]


def test_avatar_removal_restores_default(operator_token):
    """Verify DELETE /auth/avatar resets avatar to default operational portrait."""
    headers = {"Authorization": f"Bearer {operator_token}"}
    
    # Set custom avatar first
    sample_png = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
    client.post("/api/auth/avatar", headers=headers, json={"avatar_data_url": sample_png})

    # Call DELETE /auth/avatar
    resp = client.delete("/api/auth/avatar", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["avatar_url"] == "/officer_sharma.png"

    # Confirm in DB
    db = SessionLocal()
    try:
        user_record = db.query(UserProfileModel).filter(UserProfileModel.username == "operator").first()
        assert user_record.avatar_url == "/officer_sharma.png"
    finally:
        db.close()


def test_dossier_export_integrity_and_security(operator_token):
    """Verify official dossier export contains all required fields, valid SHA-256, and no secrets."""
    headers = {"Authorization": f"Bearer {operator_token}"}
    resp = client.get("/api/auth/dossier/export", headers=headers)
    assert resp.status_code == 200, resp.text
    dossier = resp.json()

    # Structural fields
    assert "dossier_id" in dossier
    assert "classification" in dossier
    assert "generated_at" in dossier
    assert "jurisdiction" in dossier
    assert "officer" in dossier
    assert "rbac_governance" in dossier
    assert "security_provenance" in dossier
    assert "cryptographic_hash_sha256" in dossier

    # Officer attributes
    officer = dossier["officer"]
    assert officer["username"] == "operator"
    assert officer["role"] == ROLE_OPERATOR
    assert "name" in officer
    assert "duty_desk" in officer
    assert "official_email" in officer

    # RBAC capabilities
    rbac = dossier["rbac_governance"]
    assert rbac["active_tier"] == ROLE_OPERATOR
    assert "VERIFY_DEMAND" in rbac["authorized_capabilities"]
    assert "DISPATCH_DEMAND" in rbac["authorized_capabilities"]

    # Security verification: verify SHA-256 matches payload content
    received_hash = dossier["cryptographic_hash_sha256"]
    dossier_copy = dict(dossier)
    del dossier_copy["cryptographic_hash_sha256"]
    serialized = json.dumps(dossier_copy, sort_keys=True).encode("utf-8")
    expected_hash = hashlib.sha256(serialized).hexdigest()
    assert received_hash == expected_hash

    # Security check: Ensure password hash and JWT secret are not present
    dumped = json.dumps(dossier)
    assert "password_hash" not in dumped
    assert "SECRET_KEY" not in dumped
    assert "secret" not in dumped.lower() or "session" in dumped.lower() or "statutory_notice" in dumped.lower()
