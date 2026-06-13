"""
schemas/user.py
═══════════════
Pydantic v2 schemas for User, Role, and Authentication flows.

Schema hierarchy:
  Role   : RoleBase → RoleCreate | RoleUpdate → RoleResponse
  User   : UserBase → UserCreate | UserUpdate → UserResponse | UserBriefResponse
  Auth   : LoginRequest → TokenResponse | TokenPayload
  Misc   : AssignRoleRequest, RemoveRoleRequest, ChangePasswordRequest
"""
from datetime import datetime
from typing import Optional

import re
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Lenient email type
# ---------------------------------------------------------------------------
# Pydantic v2's built-in EmailStr uses the `email-validator` library which
# rejects reserved/private TLDs like .local, .internal, .test, etc.
# We use a plain str with a simple RFC-5322-style regex instead so that
# internal addresses (e.g. admin@company.local) are accepted alongside
# standard public-domain addresses.
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)*\.[a-zA-Z]{2,}$"
    r"|^[a-zA-Z0-9_.+\-]+@[a-zA-Z0-9\-]+(\.[a-zA-Z0-9\-]+)+$"  # allows .local etc.
)

# Use plain str everywhere — validated by the field_validator below.
EmailStr = str


# ──────────────────────────────────────────────────────────────
# Role Schemas
# ──────────────────────────────────────────────────────────────

class RoleBase(BaseModel):
    """Shared fields for role creation and response."""
    name: str = Field(
        ...,
        min_length=2,
        max_length=50,
        examples=["admin", "task_creator", "viewer"],
        description="Unique role name. Use lowercase with underscores.",
    )
    description: Optional[str] = Field(
        None,
        max_length=255,
        description="Human-readable description of what this role can do.",
    )

    @field_validator("name")
    @classmethod
    def name_must_be_lowercase(cls, v: str) -> str:
        """Enforce lowercase role names to avoid duplicates like 'Admin' vs 'admin'."""
        return v.strip().lower()


class RoleCreate(RoleBase):
    """Request body for creating a new role (admin only)."""
    pass


class RoleUpdate(BaseModel):
    """Request body for updating an existing role (admin only)."""
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    description: Optional[str] = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def name_must_be_lowercase(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if v else v


class RoleResponse(RoleBase):
    """Full role object returned from the API."""
    id: str = Field(..., description="UUID of the role.")

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────
# User Schemas
# ──────────────────────────────────────────────────────────────

class UserBase(BaseModel):
    """Shared fields present on every user schema."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_\-]+$",
        description="Username — letters, digits, underscores and hyphens only.",
        examples=["john_doe", "alice-smith"],
    )
    email: str = Field(
        ...,
        description="Unique email address for the user.",
        examples=["john@example.com"],
    )
    full_name: Optional[str] = Field(
        None,
        max_length=150,
        description="Optional display name.",
        examples=["John Doe"],
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """
        Validate email format with a lenient regex that accepts internal/private
        domains (.local, .internal, .test, etc.) that the strict email-validator
        library rejects. Normalises to lowercase.
        """
        v = v.strip().lower()
        if not _EMAIL_REGEX.match(v):
            raise ValueError(f"'{v}' is not a valid email address.")
        return v


class UserCreate(UserBase):
    """
    Request body for registering a new user.
    Password must be at least 8 characters.
    """
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Plaintext password (min 8 chars). Stored as a bcrypt hash.",
        examples=["SecurePass123!"],
    )

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """Basic strength check: require at least one digit."""
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit.")
        return v


class UserUpdate(BaseModel):
    """
    Request body for updating a user profile (admin only).
    All fields are optional — only provided fields will be updated (PATCH semantics).
    """
    email: Optional[str] = Field(None, description="New email address.")
    full_name: Optional[str] = Field(None, max_length=150, description="Updated display name.")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate the account.")
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=128,
        description="New password. Leave blank to keep current.",
    )


class ChangePasswordRequest(BaseModel):
    """
    Request body for a user changing their own password.
    Requires both the current and new password for security.
    """
    current_password: str = Field(..., description="The user's current password for verification.")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (min 8 chars, must contain a digit).",
    )

    @field_validator("new_password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("New password must contain at least one digit.")
        return v


class UserBriefResponse(BaseModel):
    """
    Lightweight user object embedded inside other responses
    (e.g. task.owner, project.owner) to avoid deep nesting.
    """
    id: str
    username: str
    full_name: Optional[str] = None
    email: str

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """
    Full user profile returned from the API.
    Includes assigned role names and account metadata.
    """
    id: str = Field(..., description="UUID of the user.")
    is_active: bool = Field(..., description="Whether the account is active.")
    roles: list[str] = Field(
        default=[],
        description="List of role names assigned to this user.",
        examples=[["admin"], ["task_creator", "viewer"]],
    )
    created_at: datetime = Field(..., description="Account creation timestamp (UTC).")
    updated_at: datetime = Field(..., description="Last profile update timestamp (UTC).")

    model_config = {"from_attributes": True}


class UserWithRolesResponse(UserResponse):
    """Extended user response that includes full role objects instead of just names."""
    role_objects: list[RoleResponse] = Field(
        default=[],
        description="Full role objects assigned to this user.",
    )

    model_config = {"from_attributes": True}


# ──────────────────────────────────────────────────────────────
# Role Assignment Schemas
# ──────────────────────────────────────────────────────────────

class AssignRoleRequest(BaseModel):
    """Request body for assigning a role to a user."""
    role_id: str = Field(..., description="UUID of the role to assign.")


class RemoveRoleRequest(BaseModel):
    """Request body for removing a role from a user (alternative to path param)."""
    role_id: str = Field(..., description="UUID of the role to remove.")


# ──────────────────────────────────────────────────────────────
# Authentication Schemas
# ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """Request body for the /auth/login endpoint."""
    username: str = Field(..., description="Registered username.", examples=["admin"])
    password: str = Field(..., description="Account password.", examples=["admin123"])


class TokenResponse(BaseModel):
    """
    Successful authentication response.
    Returns a JWT bearer token and the authenticated user's profile.
    """
    access_token: str = Field(..., description="JWT bearer token. Include in Authorization header.")
    token_type: str = Field(default="bearer", description="Always 'bearer'.")
    user: UserResponse = Field(..., description="Profile of the authenticated user.")


class TokenPayload(BaseModel):
    """
    Internal schema representing the decoded JWT payload.
    Used by auth_service.py when validating tokens.
    """
    sub: str = Field(..., description="Subject — the user's UUID.")
    exp: Optional[int] = Field(None, description="Expiry timestamp (Unix epoch).")


# ──────────────────────────────────────────────────────────────
# Pagination / List Wrappers
# ──────────────────────────────────────────────────────────────

class PaginatedUsersResponse(BaseModel):
    """Paginated list of users (for future pagination support)."""
    total: int = Field(..., description="Total number of users matching the query.")
    page: int = Field(..., description="Current page number (1-based).")
    page_size: int = Field(..., description="Number of items per page.")
    items: list[UserResponse] = Field(..., description="Users on the current page.")