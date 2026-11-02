# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field

class RegisterOTPRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)

class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class ChangeIdRequest(BaseModel):
    new_personly_id: int = Field(..., ge=10000, le=99999)