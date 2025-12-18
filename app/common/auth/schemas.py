"""Pydantic schemas for authentication requests and responses."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# Request Schemas
class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


# Response Schemas
class PermissionResponse(BaseModel):
    """Schema for permission data."""
    id: int
    codename: str
    description: Optional[str] = None
    
    model_config = {"from_attributes": True}


class RoleResponse(BaseModel):
    """Schema for role data."""
    id: int
    name: str
    description: Optional[str] = None
    
    model_config = {"from_attributes": True}


class RoleWithPermissionsResponse(RoleResponse):
    """Schema for role with permissions."""
    permissions: list[PermissionResponse] = []


class UserResponse(BaseModel):
    """Schema for user data in responses (excludes sensitive data)."""
    id: int
    email: str
    is_active: bool
    is_superuser: bool
    roles: list[RoleResponse] = []
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """Schema for authentication token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for JWT token payload."""
    sub: str  # User ID as string
    exp: datetime
    type: str  # "access" or "refresh"
    roles: list[str] = []
    permissions: list[str] = []
    tenant_id: Optional[int] = None


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str

