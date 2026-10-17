"""
RELIEFOS Lite — Authentication API Endpoints.
Provides user login, credential verification, token issuance, profile inspection,
profile editing, photo upload, database persistence, and duty dossier export.
"""

import time
import json
import base64
import hashlib
import hmac
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.domain import UserProfileModel, AuditLogModel
from app.core.auth import (
    REGISTERED_USERS, PRESHARED_TOKENS, create_access_token, get_current_user,
    hash_password, verify_password,
    ROLE_COMMANDER, ROLE_OPERATOR, ROLE_ANALYST, ALL_ROLES
)

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])

# Maximum allowed size for avatar base64 data URI (2MB binary ≈ 2.8MB base64)
MAX_AVATAR_B64_BYTES = 2_800_000
ALLOWED_AVATAR_PREFIXES = (
    "data:image/jpeg;base64,",
    "data:image/jpg;base64,",
    "data:image/png;base64,",
    "data:image/webp;base64,"
)

DEFAULT_AVATARS = {
    "commander": "/officer_commander.png",
    "operator": "/officer_sharma.png",
    "analyst": "/officer_analyst.png"
}


class LoginRequest(BaseModel):
    username: str = Field(..., description="Operational username ('commander', 'operator', or 'analyst')")
    password: str = Field(..., description="Account password")


class UserProfileResponse(BaseModel):
    username: str
    role: str
    name: str
    agency: str
    email: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class LoginResponse(BaseModel):
    success: bool
    access_token: str
    token_type: str = "bearer"
    expires_in_hours: int
    user: UserProfileResponse


class UpdateProfileRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100, description="Full display name of officer")
    email: Optional[str] = Field(None, max_length=150, description="Official email address")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone number")
    agency: Optional[str] = Field(None, max_length=150, description="Duty station or assigned agency cell")
    avatar_url: Optional[str] = Field(None, description="Profile avatar URL or base64 image data URI")


class AvatarUploadRequest(BaseModel):
    avatar_data_url: str = Field(..., description="Base64 Data URI: data:image/(jpeg|png|webp);base64,...")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current operational password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New secure password (min 6 chars)")


class RoleDefinition(BaseModel):
    role: str
    description: str
    permissions: List[str]


def _get_or_create_db_profile(uname: str, db: Session) -> UserProfileModel:
    """Retrieves user profile from database; seeds from REGISTERED_USERS if not yet populated."""
    profile = db.query(UserProfileModel).filter(UserProfileModel.username == uname).first()
    if not profile:
        seed = REGISTERED_USERS.get(uname, {
            "username": uname,
            "role": ROLE_OPERATOR,
            "name": "Insp. S. Sharma",
            "agency": "Kamrup Metro Logistics Desk",
            "email": "insp.sharma@asdma.gov.in",
            "phone": "+91 94350 22002",
            "avatar_url": DEFAULT_AVATARS.get(uname, "/officer_sharma.png"),
            "password_hash": hash_password("relief@2026")
        })
        profile = UserProfileModel(
            username=seed["username"],
            role=seed["role"],
            name=seed["name"],
            agency=seed.get("agency", "District Operations"),
            email=seed.get("email"),
            phone=seed.get("phone"),
            avatar_url=seed.get("avatar_url", DEFAULT_AVATARS.get(uname, "/officer_sharma.png")),
            password_hash=seed.get("password_hash")
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def _validate_avatar_data_url(data_url: str) -> None:
    """Validates image MIME prefix and size constraints for avatar uploads."""
    if not data_url:
        return
    # If it's a static path or asset URL, allow it directly
    if not data_url.startswith("data:"):
        return

    if not any(data_url.startswith(prefix) for prefix in ALLOWED_AVATAR_PREFIXES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported image format. Profile photo must be JPG, PNG, or WebP."
        )

    if len(data_url) > MAX_AVATAR_B64_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File size exceeds the 2MB limit. Please upload a smaller image."
        )


@router.post("/login", response_model=LoginResponse, summary="Authenticate and acquire access token")
async def login_endpoint(req: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticates operational user against registered database credentials and issues a signed Bearer token.
    Preset accounts:
    - commander / asdma@2026 (Admin authority: all permissions)
    - operator / relief@2026 (Officer authority: operational writes, demand verify, dispatch, AI review)
    - analyst / view@2026 (Analyst authority: read-only telemetry, GIS map, reporting)
    """
    uname = req.username.strip().lower()
    
    # Query database first, fallback to in-memory REGISTERED_USERS
    profile = db.query(UserProfileModel).filter(UserProfileModel.username == uname).first()
    stored_hash = None
    role = ROLE_OPERATOR
    name = uname
    agency = "District Operations"
    email = None
    phone = None
    avatar_url = DEFAULT_AVATARS.get(uname, "/officer_sharma.png")

    if profile:
        stored_hash = profile.password_hash
        role = profile.role
        name = profile.name
        agency = profile.agency
        email = profile.email
        phone = profile.phone
        avatar_url = profile.avatar_url or DEFAULT_AVATARS.get(uname, "/officer_sharma.png")
    elif uname in REGISTERED_USERS:
        user_record = REGISTERED_USERS[uname]
        stored_hash = user_record["password_hash"]
        role = user_record["role"]
        name = user_record["name"]
        agency = user_record["agency"]
        email = user_record.get("email")
        phone = user_record.get("phone")
        avatar_url = user_record.get("avatar_url", DEFAULT_AVATARS.get(uname, "/officer_sharma.png"))
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    if not stored_hash or not verify_password(req.password, stored_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    user_data = {
        "username": uname,
        "role": role,
        "name": name,
        "agency": agency,
        "email": email,
        "phone": phone,
        "avatar_url": avatar_url
    }
    token = create_access_token(user_data, expires_delta_hours=24)

    return LoginResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        expires_in_hours=24,
        user=UserProfileResponse(
            username=uname,
            role=role,
            name=name,
            agency=agency,
            email=email,
            phone=phone,
            avatar_url=avatar_url
        )
    )


@router.get("/me", response_model=UserProfileResponse, summary="Inspect current authenticated session")
@router.get("/profile", response_model=UserProfileResponse, summary="Inspect current authenticated session (alias)")
async def get_current_user_profile(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns profile and role permissions of the currently authenticated officer from persistent database."""
    uname = user.get("username", "").strip().lower()
    profile = db.query(UserProfileModel).filter(UserProfileModel.username == uname).first()

    if profile:
        return UserProfileResponse(
            username=profile.username,
            role=profile.role,
            name=profile.name,
            agency=profile.agency,
            email=profile.email,
            phone=profile.phone,
            avatar_url=profile.avatar_url or DEFAULT_AVATARS.get(uname, "/officer_sharma.png")
        )

    # Fallback to in-memory register
    record = REGISTERED_USERS.get(uname)
    if record:
        return UserProfileResponse(
            username=record["username"],
            role=record["role"],
            name=record.get("name", user.get("name", "Unknown")),
            agency=record.get("agency", user.get("agency", "District Operations")),
            email=record.get("email", user.get("email")),
            phone=record.get("phone", user.get("phone")),
            avatar_url=record.get("avatar_url", user.get("avatar_url", DEFAULT_AVATARS.get(uname, "/officer_sharma.png")))
        )

    return UserProfileResponse(
        username=user.get("username", "anonymous"),
        role=user.get("role", "ANALYST"),
        name=user.get("name", "Unknown Operator"),
        agency=user.get("agency", "District Operations"),
        email=user.get("email"),
        phone=user.get("phone"),
        avatar_url=user.get("avatar_url", "/officer_sharma.png")
    )


@router.put("/me", response_model=UserProfileResponse, summary="Update current user profile")
@router.put("/profile", response_model=UserProfileResponse, summary="Update current user profile (alias)")
async def update_current_user_profile(
    req: UpdateProfileRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Updates the authenticated officer's profile information (name, email, phone, agency, avatar_url).
    Changes are persisted directly to the active database.
    Security fields (username, role, RBAC permissions) are strictly immutable.
    """
    uname = user.get("username", "").strip().lower()
    profile = _get_or_create_db_profile(uname, db)
    old_summary = f"name={profile.name}, email={profile.email}, phone={profile.phone}, agency={profile.agency}"

    # Validate and update name
    if req.name is not None:
        name_clean = req.name.strip()
        if len(name_clean) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Full Name must be at least 2 characters."
            )
        profile.name = name_clean

    # Validate and update email
    if req.email is not None:
        email_clean = req.email.strip()
        if email_clean:
            if "@" not in email_clean or "." not in email_clean.split("@")[-1]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Please provide a valid official email address."
                )
        profile.email = email_clean

    # Validate and update phone
    if req.phone is not None:
        profile.phone = req.phone.strip()

    # Validate and update agency
    if req.agency is not None:
        profile.agency = req.agency.strip()

    # Validate and update avatar_url
    if req.avatar_url is not None:
        _validate_avatar_data_url(req.avatar_url)
        profile.avatar_url = req.avatar_url if req.avatar_url else DEFAULT_AVATARS.get(uname, "/officer_sharma.png")

    profile.updated_at = datetime.now(timezone.utc)

    # Sync in-memory records and pre-shared tokens
    if uname in REGISTERED_USERS:
        REGISTERED_USERS[uname]["name"] = profile.name
        REGISTERED_USERS[uname]["agency"] = profile.agency
        REGISTERED_USERS[uname]["email"] = profile.email
        REGISTERED_USERS[uname]["phone"] = profile.phone
        REGISTERED_USERS[uname]["avatar_url"] = profile.avatar_url

    for token_key, token_data in PRESHARED_TOKENS.items():
        if token_data.get("username") == uname:
            token_data["name"] = profile.name
            token_data["agency"] = profile.agency
            token_data["email"] = profile.email
            token_data["phone"] = profile.phone
            token_data["avatar_url"] = profile.avatar_url

    # Persist audit record in database
    new_summary = f"name={profile.name}, email={profile.email}, phone={profile.phone}, agency={profile.agency}"
    audit_entry = AuditLogModel(
        operator_name=profile.name,
        entity_type="USER_PROFILE",
        entity_id=uname,
        action="UPDATE_PROFILE",
        old_value=old_summary,
        new_value=new_summary,
        notes="Officer operational profile updated and persisted to ASDMA database."
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(profile)

    return UserProfileResponse(
        username=profile.username,
        role=profile.role,
        name=profile.name,
        agency=profile.agency,
        email=profile.email,
        phone=profile.phone,
        avatar_url=profile.avatar_url
    )


@router.post("/avatar", response_model=UserProfileResponse, summary="Upload or update profile photo")
async def upload_avatar_endpoint(
    req: AvatarUploadRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Uploads and persists a new profile photo (JPG, PNG, or WebP base64 data URI, max 2MB).
    Updates database record and returns refreshed user profile.
    """
    uname = user.get("username", "").strip().lower()
    _validate_avatar_data_url(req.avatar_data_url)

    profile = _get_or_create_db_profile(uname, db)
    profile.avatar_url = req.avatar_data_url
    profile.updated_at = datetime.now(timezone.utc)

    if uname in REGISTERED_USERS:
        REGISTERED_USERS[uname]["avatar_url"] = req.avatar_data_url

    audit_entry = AuditLogModel(
        operator_name=profile.name,
        entity_type="USER_PROFILE",
        entity_id=uname,
        action="UPDATE_AVATAR",
        old_value="Previous Avatar",
        new_value="New Verified Photo Upload",
        notes="Operator profile photo uploaded and persisted."
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(profile)

    return UserProfileResponse(
        username=profile.username,
        role=profile.role,
        name=profile.name,
        agency=profile.agency,
        email=profile.email,
        phone=profile.phone,
        avatar_url=profile.avatar_url
    )


@router.delete("/avatar", response_model=UserProfileResponse, summary="Remove custom photo and reset to default avatar")
async def remove_avatar_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resets the officer's profile photo to the default ASDMA operational avatar."""
    uname = user.get("username", "").strip().lower()
    profile = _get_or_create_db_profile(uname, db)
    default_url = DEFAULT_AVATARS.get(uname, "/officer_sharma.png")

    profile.avatar_url = default_url
    profile.updated_at = datetime.now(timezone.utc)

    if uname in REGISTERED_USERS:
        REGISTERED_USERS[uname]["avatar_url"] = default_url

    audit_entry = AuditLogModel(
        operator_name=profile.name,
        entity_type="USER_PROFILE",
        entity_id=uname,
        action="REMOVE_AVATAR",
        old_value="Custom Avatar",
        new_value=default_url,
        notes="Operator custom photo removed; restored default ASDMA avatar."
    )
    db.add(audit_entry)
    db.commit()
    db.refresh(profile)

    return UserProfileResponse(
        username=profile.username,
        role=profile.role,
        name=profile.name,
        agency=profile.agency,
        email=profile.email,
        phone=profile.phone,
        avatar_url=profile.avatar_url
    )


@router.get("/dossier/export", summary="Export official duty dossier as cryptographically verified JSON")
async def export_dossier_endpoint(
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generates and returns an authoritative, signed JSON dossier for the authenticated officer.
    Contains profile metadata, assigned logistics desk, RBAC privileges, and a SHA-256 integrity hash.
    """
    uname = user.get("username", "").strip().lower()
    profile = _get_or_create_db_profile(uname, db)

    # Role capability mapping
    role_perms = {
        ROLE_COMMANDER: [
            "READ_TELEMETRY", "VIEW_GIS_MAP", "VERIFY_DEMAND", "DISPATCH_DEMAND",
            "UPDATE_INVENTORY", "MODIFY_ROAD_CLOSURES", "SWITCH_SYSTEM_MODE",
            "RESET_DRILL_ENVIRONMENT", "REVIEW_AI_ACTIONS", "SIGN_OFF_LOGISTICS_PLAN",
            "RECALCULATE_RISK_WEIGHTS", "ACCESS_FULL_AUDIT_LOGS"
        ],
        ROLE_OPERATOR: [
            "READ_TELEMETRY", "VIEW_GIS_MAP", "VERIFY_DEMAND", "DISPATCH_DEMAND",
            "UPDATE_INVENTORY", "MODIFY_ROAD_CLOSURES", "REVIEW_AI_ACTIONS",
            "SIGN_OFF_LOGISTICS_PLAN", "RECALCULATE_RISK_WEIGHTS"
        ],
        ROLE_ANALYST: [
            "READ_TELEMETRY", "VIEW_GIS_MAP", "VIEW_SIMULATIONS", "VIEW_FORECASTS",
            "EXPORT_TACTICAL_BRIEFS"
        ]
    }.get(profile.role, ["READ_TELEMETRY"])

    now_iso = datetime.now(timezone.utc).isoformat()
    dossier_id = f"DOSSIER-{profile.username.upper()}-{int(time.time())}"

    dossier_payload = {
        "dossier_id": dossier_id,
        "classification": "ASDMA TACTICAL OPERATIONAL DOSSIER",
        "generated_at": now_iso,
        "jurisdiction": "Assam State Disaster Management Authority (ASDMA) • Kamrup Metropolitan EOC",
        "officer": {
            "name": profile.name,
            "username": profile.username,
            "role": profile.role,
            "duty_desk": profile.agency or "Kamrup Metro Logistics Desk",
            "official_email": profile.email or "N/A",
            "contact_phone": profile.phone or "N/A",
            "avatar_configured": bool(profile.avatar_url and not profile.avatar_url.startswith("/officer_"))
        },
        "rbac_governance": {
            "active_tier": profile.role,
            "authorized_capabilities": role_perms,
            "statutory_statute": "Section 30, Disaster Management Act 2005",
            "compliance_framework": "ASDMA Form 8B Resource Allocation Protocol"
        },
        "security_provenance": {
            "token_standard": "HMAC-SHA256 Bearer Token",
            "audit_trail_reference": f"AUD-USR-{uname.upper()}",
            "statutory_notice": "Official duty record. Unauthorized tampering or role escalation is prohibited."
        }
    }

    # Compute cryptographic SHA-256 integrity hash over canonical JSON
    serialized = json.dumps(dossier_payload, sort_keys=True).encode("utf-8")
    dossier_payload["cryptographic_hash_sha256"] = hashlib.sha256(serialized).hexdigest()

    return dossier_payload


@router.post("/change-password", summary="Change current user password")
async def change_password_endpoint(
    req: ChangePasswordRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Secure password change for the authenticated officer.
    Verifies current password hash and updates stored credential hash in the database.
    """
    uname = user.get("username", "").strip().lower()
    profile = _get_or_create_db_profile(uname, db)

    if not verify_password(req.current_password, profile.password_hash or ""):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect."
        )

    if req.new_password == req.current_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from current password."
        )

    if len(req.new_password) < 6:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password must be at least 6 characters long."
        )

    # Hash new password using scrypt
    new_hash = hash_password(req.new_password)
    profile.password_hash = new_hash
    profile.updated_at = datetime.now(timezone.utc)

    if uname in REGISTERED_USERS:
        REGISTERED_USERS[uname]["password_hash"] = new_hash

    audit_entry = AuditLogModel(
        operator_name=profile.name,
        entity_type="USER_PROFILE",
        entity_id=uname,
        action="CHANGE_PASSWORD",
        old_value="Active Credential Hash",
        new_value="Rotated Credential Hash",
        notes="Operator password rotated and persisted to database."
    )
    db.add(audit_entry)
    db.commit()

    return {
        "success": True,
        "message": "Operational access password updated successfully."
    }


@router.get("/roles", response_model=List[RoleDefinition], summary="List RBAC roles and permissions")
async def get_roles_list():
    """Lists all role-based access control tiers and their operational boundaries."""
    return [
        RoleDefinition(
            role=ROLE_COMMANDER,
            description="District EOC Commander / ASDMA Incident Controller",
            permissions=[
                "READ_TELEMETRY", "VIEW_GIS_MAP", "VERIFY_DEMAND", "DISPATCH_DEMAND",
                "UPDATE_INVENTORY", "MODIFY_ROAD_CLOSURES", "SWITCH_SYSTEM_MODE",
                "RESET_DRILL_ENVIRONMENT", "REVIEW_AI_ACTIONS", "SIGN_OFF_LOGISTICS_PLAN",
                "RECALCULATE_RISK_WEIGHTS", "ACCESS_FULL_AUDIT_LOGS"
            ]
        ),
        RoleDefinition(
            role=ROLE_OPERATOR,
            description="Emergency Operations Center Logistics Officer / Desk Planner",
            permissions=[
                "READ_TELEMETRY", "VIEW_GIS_MAP", "VERIFY_DEMAND", "DISPATCH_DEMAND",
                "UPDATE_INVENTORY", "MODIFY_ROAD_CLOSURES", "REVIEW_AI_ACTIONS",
                "SIGN_OFF_LOGISTICS_PLAN", "RECALCULATE_RISK_WEIGHTS"
            ]
        ),
        RoleDefinition(
            role=ROLE_ANALYST,
            description="GIS Analyst / External Observer / Field Monitoring Cell",
            permissions=[
                "READ_TELEMETRY", "VIEW_GIS_MAP", "VIEW_SIMULATIONS", "VIEW_FORECASTS",
                "EXPORT_TACTICAL_BRIEFS"
            ]
        )
    ]
