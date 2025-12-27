"""Pydantic schemas for authentication validation."""

from pydantic import BaseModel, EmailStr, Field, model_validator


class UserRegister(BaseModel):
    """User registration form validation schema"""

    email: EmailStr
    password: str = Field(
        ..., min_length=8, description="Password must be at least 8 characters"
    )
    password_confirm: str

    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    """Schema for login form validation."""

    email: EmailStr
    password: str = Field(..., min_length=1)
