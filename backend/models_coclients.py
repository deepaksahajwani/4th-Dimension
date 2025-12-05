"""
Co-Clients/Associate Clients Models
These are additional people from the client's side who can view/comment on projects
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class CoClientBase(BaseModel):
    name: str
    email: EmailStr
    phone: str
    relationship: str  # e.g., "Spouse", "Family Member", "Representative", "Staff"
    notes: Optional[str] = None

class CoClientCreate(CoClientBase):
    project_id: str
    main_client_id: str

class CoClient(CoClientBase):
    id: str
    project_id: str
    main_client_id: str
    created_at: datetime
    created_by: str
    
    class Config:
        from_attributes = True
