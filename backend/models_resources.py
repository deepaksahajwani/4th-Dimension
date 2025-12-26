"""
Resource Models for 4th Dimension
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ResourceCategory(str, Enum):
    ONBOARDING = "onboarding"
    STANDARDS = "standards"
    TEMPLATES = "templates"
    TUTORIALS = "tutorials"
    POLICIES = "policies"
    TOOLS = "tools"


class ResourceType(str, Enum):
    PDF = "pdf"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    VIDEO = "video"
    IMAGE = "image"
    LINK = "link"
    CAD = "cad"  # AutoCAD DWG, DXF files


class ResourceBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: ResourceCategory
    type: ResourceType = ResourceType.PDF
    url: Optional[str] = None
    external_link: Optional[str] = None  # For external resources like software downloads
    featured: bool = False
    tags: List[str] = []
    visible_to: List[str] = ["all"]  # Roles that can see this resource: "all", "owner", "team_member", "client", etc.
    order: int = 0  # For custom ordering within category


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[ResourceCategory] = None
    type: Optional[ResourceType] = None
    url: Optional[str] = None
    external_link: Optional[str] = None
    featured: Optional[bool] = None
    tags: Optional[List[str]] = None
    visible_to: Optional[List[str]] = None
    order: Optional[int] = None


class Resource(ResourceBase):
    id: str
    file_name: Optional[str] = None
    file_size: Optional[int] = None  # In bytes
    mime_type: Optional[str] = None
    download_count: int = 0
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ResourceResponse(Resource):
    created_by_name: Optional[str] = None
