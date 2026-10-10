"""
RELIEFOS Lite — Authentication API Endpoints.
Provides user login, credential verification, token issuance, and profile inspection.
"""

import hashlib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from app.core.auth import (
    REGISTERED_USERS, PRESHARED_TOKENS, create_access_token, get_current_user,
    ROLE_COMMANDER, ROLE_OPERATOR, ROLE_ANALYST, ALL_ROLES
)

router = APIRouter(prefix="/auth", tags=["Authentication & Security"])


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
    phone: Optional[str] = Field(None, max_length=30, description="Contact phone number")
    agency: Optional[str] = Field(None, max_length=150, description="Duty station or assigned agency cell")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=1, description="Current operational password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New secure password (min 6 chars)")


class RoleDefinition(BaseModel):
    role: str
    description: str
    permissions: List[str]


@router.post("/login", response_model=LoginResponse, summary="Authenticate and acquire access token")
async def login_endpoint(req: LoginRequest):
    """
    Authenticates operational user against registered credentials and issues a signed Bearer token.
    Preset accounts:
    - commander / asdma@2026 (Admin authority: all permissions)
    - operator / relief@2026 (Officer authority: operational writes, demand verify, dispatch, AI review)
    - analyst / view@2026 (Analyst authority: read-only telemetry, GIS map, reporting)
    """
    uname = req.username.strip().lower()
    user_record = REGISTERED_USERS.get(uname)

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    # Verify SHA-256 password hash
    hashed = hashlib.sha256(req.password.encode("utf-8")).hexdigest()
    if hashed != user_record["password_hash"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

    token = create_access_token(user_record, expires_delta_hours=24)

    return LoginResponse(
        success=True,
        access_token=token,
        token_type="bearer",
        expires_in_hours=24,
        user=UserProfileResponse(
            username=user_record["username"],
            role=user_record["role"],
            name=user_record["name"],
            agency=user_record["agency"],
            email=user_record.get("email"),
            phone=user_record.get("phone"),
            avatar_url=user_record.get("avatar_url")
        )
    )


@router.get("/me", response_model=UserProfileResponse, summary="Inspect current authenticated session")
@router.get("/profile", response_model=UserProfileResponse, summary="Inspect current authenticated session (alias)")
async def get_current_user_profile(user: Dict[str, Any] = Depends(get_current_user)):
    """Returns profile and role permissions of the currently authenticated officer from active registry."""
    uname = user.get("username", "").strip().lower()
    record = REGISTERED_USERS.get(uname)
    if record:
        return UserProfileResponse(
            username=record["username"],
            role=record["role"],
            name=record.get("name", user.get("name", "Unknown")),
            agency=record.get("agency", user.get("agency", "District Operations")),
            email=record.get("email", user.get("email")),
            phone=record.get("phone", user.get("phone")),
            avatar_url=record.get("avatar_url", user.get("avatar_url", "/officer_sharma.png"))
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
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Updates the authenticated officer's profile information (name, email, phone, agency).
    Role, permissions, and security privileges are strictly immutable from this endpoint.
    """
    uname = user.get("username", "").strip().lower()
    record = REGISTERED_USERS.get(uname)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User record for '{uname}' not found in registered database."
        )

    # Validate and update name
    if req.name is not None:
        name_clean = req.name.strip()
        if len(name_clean) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Full Name must be at least 2 characters."
            )
        record["name"] = name_clean

    # Validate and update email
    if req.email is not None:
        email_clean = req.email.strip()
        if email_clean:
            if "@" not in email_clean or "." not in email_clean.split("@")[-1]:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Please provide a valid email address."
                )
        record["email"] = email_clean

    # Validate and update phone
    if req.phone is not None:
        record["phone"] = req.phone.strip()

    # Validate and update agency
    if req.agency is not None:
        record["agency"] = req.agency.strip()

    # Synchronize pre-shared tokens so integration tests and active tokens reflect updates
    for token_key, token_data in PRESHARED_TOKENS.items():
        if token_data.get("username") == uname:
            token_data["name"] = record["name"]
            token_data["agency"] = record["agency"]
            token_data["email"] = record.get("email")
            token_data["phone"] = record.get("phone")

    return UserProfileResponse(
        username=record["username"],
        role=record["role"],
        name=record["name"],
        agency=record["agency"],
        email=record.get("email"),
        phone=record.get("phone"),
        avatar_url=record.get("avatar_url", "/officer_sharma.png")
    )


@router.post("/change-password", summary="Change current user password")
async def change_password_endpoint(
    req: ChangePasswordRequest,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Secure password change for the authenticated officer.
    Verifies current password hash and updates stored credential hash.
    """
    uname = user.get("username", "").strip().lower()
    record = REGISTERED_USERS.get(uname)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User record for '{uname}' not found."
        )

    current_hash = hashlib.sha256(req.current_password.encode("utf-8")).hexdigest()
    if current_hash != record["password_hash"]:
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

    # Hash new password
    new_hash = hashlib.sha256(req.new_password.encode("utf-8")).hexdigest()
    record["password_hash"] = new_hash

    return {
        "success": True,
        "message": "Password updated successfully."
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
