"""
ArchFlow Projects Module - Data Models
Complete schema for project management, drawings, tasks, site visits, and notifications
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
from datetime import datetime, timezone
from enum import Enum
import uuid

# ==================== ENUMS ====================

class ProjectType(str, Enum):
    ARCHITECTURE = "Architecture"
    INTERIOR = "Interior"
    PLANNING = "Planning"
    LANDSCAPE = "Landscape"

class ProjectStatus(str, Enum):
    LEAD = "Lead"
    CONCEPT = "Concept"
    LAYOUT_DEV = "Layout_Dev"
    ELEVATION_3D = "Elevation_3D"
    STRUCTURAL_COORD = "Structural_Coord"
    WORKING_DRAWINGS = "Working_Drawings"
    EXECUTION = "Execution"
    ON_HOLD = "OnHold"
    CLOSED = "Closed"

class TeamMemberRole(str, Enum):
    OWNER = "Owner"
    ADMIN = "Admin"
    PROJECT_MANAGER = "ProjectManager"
    ARCHITECT = "Architect"
    INTERIOR_DESIGNER = "InteriorDesigner"
    DRAFTER = "Drafter"

class ConsultantType(str, Enum):
    STRUCTURAL = "Structural"
    MEP = "MEP"
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    HVAC = "HVAC"
    LANDSCAPE = "Landscape"
    OTHER = "Other"

class DrawingCategoryEnum(str, Enum):
    STRUCTURAL = "Structural"
    ARCHITECTURAL = "Architectural"
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    HVAC = "HVAC"
    FURNITURE = "Furniture"
    CEILING = "Ceiling"
    KITCHEN = "Kitchen"
    LANDSCAPE = "Landscape"
    OTHER = "Other"

class DrawingStatus(str, Enum):
    PLANNED = "Planned"
    IN_PROGRESS = "InProgress"
    FOR_REVIEW = "ForReview"
    REVISION = "Revision"
    APPROVED = "Approved"
    ISSUED = "Issued"

class TaskCategory(str, Enum):
    DRAWING = "Drawing"
    SITE_ISSUE = "SiteIssue"
    CONSULTANT_FOLLOWUP = "ConsultantFollowup"
    MEETING = "Meeting"
    OTHER = "Other"

class TaskStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    BLOCKED = "Blocked"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class Priority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"

class IssueStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "InProgress"
    NEEDS_CLIENT_INPUT = "NeedsClientInput"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class NotificationChannel(str, Enum):
    IN_APP = "InApp"
    EMAIL = "Email"

# ==================== MODELS ====================

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    project_types: List[str] = []  # Architecture, Interior, Landscape, Planning
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    archived: bool = False  # For keeping list clean
    created_by_id: Optional[str] = None
    owner_team_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class ClientUpdate(BaseModel):
    name: str
    project_types: List[str] = []
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    archived: bool = False

class ClientCreate(BaseModel):
    name: str
    project_types: List[str] = []
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class TeamMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_ref: str  # User ID
    role: TeamMemberRole
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class Consultant(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: ConsultantType
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class ConsultantCreate(BaseModel):
    name: str
    type: ConsultantType
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    notes: Optional[str] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # Unique project code
    title: str
    type: ProjectType
    status: ProjectStatus = ProjectStatus.LEAD
    client_id: str
    lead_architect_id: Optional[str] = None  # TeamMember ID
    project_manager_id: Optional[str] = None  # TeamMember ID
    start_date: Optional[datetime] = None
    expected_finish: Optional[datetime] = None
    site_address: Optional[str] = None
    plot_dimensions: Optional[str] = None
    notes: Optional[str] = None
    created_by_id: Optional[str] = None
    owner_team_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class ProjectCreate(BaseModel):
    code: str
    title: str
    type: ProjectType
    status: ProjectStatus = ProjectStatus.LEAD
    client_id: str
    lead_architect_id: Optional[str] = None
    project_manager_id: Optional[str] = None
    start_date: Optional[str] = None
    expected_finish: Optional[str] = None
    site_address: Optional[str] = None
    plot_dimensions: Optional[str] = None
    notes: Optional[str] = None
    checklist_preset_id: Optional[str] = None  # For auto-generation

class DrawingCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: DrawingCategoryEnum
    description: Optional[str] = None

class DrawingType(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category_id: str  # DrawingCategory ID
    name: str
    default_sequence: int
    default_due_offset_days: int = 7
    auto_template_file: Optional[str] = None
    auto_send: bool = False

class DrawingTypeCreate(BaseModel):
    category_id: str
    name: str
    default_sequence: int
    default_due_offset_days: int = 7
    auto_send: bool = False

class ProjectDrawing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    drawing_type_id: str
    title_override: Optional[str] = None
    sequence: int
    status: DrawingStatus = DrawingStatus.PLANNED
    assigned_to_id: Optional[str] = None  # TeamMember ID
    consultant_id: Optional[str] = None  # Consultant ID
    due_date: Optional[datetime] = None
    file_latest: Optional[str] = None
    version: int = 1
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProjectDrawingCreate(BaseModel):
    project_id: str
    drawing_type_id: str
    title_override: Optional[str] = None
    sequence: int
    assigned_to_id: Optional[str] = None
    consultant_id: Optional[str] = None
    due_date: Optional[str] = None

class DrawingRevision(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_drawing_id: str
    revision_no: str  # R1, R2, etc.
    change_note: Optional[str] = None
    file: Optional[str] = None
    submitted_by_id: str  # TeamMember ID
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    approved_by_id: Optional[str] = None  # TeamMember ID
    approved_at: Optional[datetime] = None

class ChecklistPreset(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    project_type: ProjectType  # Which project type this preset is for
    description: Optional[str] = None

class ChecklistItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    checklist_preset_id: str
    drawing_type_id: str
    sequence: int

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    description: Optional[str] = None
    category: TaskCategory
    status: TaskStatus = TaskStatus.OPEN
    priority: Priority = Priority.MEDIUM
    assigned_to_id: Optional[str] = None  # TeamMember ID
    due_date: Optional[datetime] = None
    related_drawing_id: Optional[str] = None  # ProjectDrawing ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    project_id: str
    title: str
    description: Optional[str] = None
    category: TaskCategory
    priority: Priority = Priority.MEDIUM
    assigned_to_id: Optional[str] = None
    due_date: Optional[str] = None
    related_drawing_id: Optional[str] = None

class SiteVisit(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    visit_date: datetime
    notes: Optional[str] = None
    created_by_id: str  # TeamMember ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SiteVisitCreate(BaseModel):
    project_id: str
    visit_date: str
    notes: Optional[str] = None

class SiteIssue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    site_visit_id: Optional[str] = None  # SiteVisit ID
    title: str
    description: Optional[str] = None
    status: IssueStatus = IssueStatus.OPEN
    severity: Priority
    raised_by_id: str  # TeamMember ID
    owner_id: str  # TeamMember ID
    due_date: Optional[datetime] = None
    related_drawing_id: Optional[str] = None  # ProjectDrawing ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SiteIssueCreate(BaseModel):
    project_id: str
    site_visit_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    severity: Priority
    raised_by_id: str
    owner_id: str
    due_date: Optional[str] = None
    related_drawing_id: Optional[str] = None

class Notification(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    message: str
    audience: List[str] = []  # ["Team", "Owner", "LeadArchitect", etc.]
    sent_to_emails: Optional[str] = None
    channel: NotificationChannel
    context_ref: Optional[str] = None  # e.g., "drawing:123", "task:456"
    sent_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class NotificationCreate(BaseModel):
    project_id: Optional[str] = None
    message: str
    audience: List[str] = []
    sent_to_emails: Optional[str] = None
    channel: NotificationChannel
    context_ref: Optional[str] = None
