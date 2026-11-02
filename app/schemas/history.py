# backend/app/schemas/history.py
from pydantic import BaseModel
from datetime import datetime

class CallRecordCreate(BaseModel):
    target_personly_id: int
    call_type: str
    status: str
    duration_seconds: int = 0
    is_caller: bool

class CallRecordResponse(BaseModel):
    id: str
    other_party_id: int
    other_party_name: str
    call_type: str
    status: str
    duration_seconds: int
    is_incoming: bool
    created_at: datetime