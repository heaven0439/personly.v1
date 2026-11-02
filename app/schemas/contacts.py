# backend/app/schemas/contacts.py
from pydantic import BaseModel, Field

class ContactAddRequest(BaseModel):
    personly_id: int = Field(..., ge=10000, le=99999)
    custom_label: str = Field(..., min_length=1, max_length=50)

class ContactResponse(BaseModel):
    personly_id: int
    custom_label: str