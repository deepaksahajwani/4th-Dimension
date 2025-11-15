"""
ArchFlow Projects Module - Data Models
Complete schema for project management, drawings, tasks, site visits, and notifications
"""

from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict
from datetime import datetime, timezone, date
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
    contact_person: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    archived: bool = False

class ClientCreate(BaseModel):
    name: str
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

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

class ContactTypeMaster(BaseModel):
    """Master list of contact types that can be used across projects"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type_name: str  # e.g., "Structural Consultant", "MEP Consultant"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ContactTypeMasterCreate(BaseModel):
    type_name: str

class ContactTypeMasterUpdate(BaseModel):
    type_name: Optional[str] = None

class BrandCategory(BaseModel):
    category_name: str
    brands: List[str] = []

class BrandCategoryMaster(BaseModel):
    """Master list of brand categories that can be used across projects"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category_name: str
    suggested_brands: List[str] = []  # Suggested brand names
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BrandCategoryMasterCreate(BaseModel):
    category_name: str
    suggested_brands: List[str] = []

class BrandCategoryMasterUpdate(BaseModel):
    category_name: Optional[str] = None
    suggested_brands: Optional[List[str]] = None

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    code: str  # Unique project code
    title: str
    project_types: List[str] = []  # Multiple types: Architecture, Interior, Landscape, Planning
    status: ProjectStatus = ProjectStatus.LEAD
    client_id: str
    lead_architect_id: Optional[str] = None  # TeamMember ID
    project_manager_id: Optional[str] = None  # TeamMember ID
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None  # When set, project auto-archives
    archived: bool = False
    site_address: Optional[str] = None
    notes: Optional[str] = None
    
    # Contractors/Consultants/Suppliers - Fixed contacts
    civil_contractor: Optional[ContactInfo] = None
    structural_consultant: Optional[ContactInfo] = None
    tile_marble_contractor: Optional[ContactInfo] = None
    furniture_contractor: Optional[ContactInfo] = None
    electrical_contractor: Optional[ContactInfo] = None
    electrical_consultant: Optional[ContactInfo] = None
    plumbing_consultant: Optional[ContactInfo] = None
    plumbing_contractor: Optional[ContactInfo] = None
    false_ceiling_contractor: Optional[ContactInfo] = None
    furniture_material_supplier: Optional[ContactInfo] = None
    kitchen_contractor: Optional[ContactInfo] = None
    modular_contractor: Optional[ContactInfo] = None
    color_contractor: Optional[ContactInfo] = None
    landscape_consultant: Optional[ContactInfo] = None
    landscape_contractor: Optional[ContactInfo] = None
    automation_consultant: Optional[ContactInfo] = None
    readymade_furniture_supplier: Optional[ContactInfo] = None
    lights_supplier: Optional[ContactInfo] = None
    
    # Custom contacts (dynamic based on user-defined contact types)
    custom_contacts: dict = {}  # {contact_type_id: ContactInfo}
    
    # Brands used in project
    brands: List[BrandCategory] = []
    
    # Contractor assignments (contractor_type: contractor_id)
    assigned_contractors: Dict[str, str] = {}  # {"Civil": "contractor_id_123", ...}
    project_access_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])  # Unique 12-char code for sharing
    
    created_by_id: Optional[str] = None
    owner_team_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class ProjectCreate(BaseModel):
    code: str
    title: str
    project_types: List[str] = []
    status: ProjectStatus = ProjectStatus.LEAD
    client_id: str
    lead_architect_id: Optional[str] = None
    project_manager_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    site_address: Optional[str] = None
    notes: Optional[str] = None
    
    # Contractors/Consultants/Suppliers
    civil_contractor: Optional[ContactInfo] = None
    structural_consultant: Optional[ContactInfo] = None
    tile_marble_contractor: Optional[ContactInfo] = None
    furniture_contractor: Optional[ContactInfo] = None
    electrical_contractor: Optional[ContactInfo] = None
    electrical_consultant: Optional[ContactInfo] = None
    plumbing_consultant: Optional[ContactInfo] = None
    plumbing_contractor: Optional[ContactInfo] = None
    false_ceiling_contractor: Optional[ContactInfo] = None
    furniture_material_supplier: Optional[ContactInfo] = None
    kitchen_contractor: Optional[ContactInfo] = None
    modular_contractor: Optional[ContactInfo] = None
    color_contractor: Optional[ContactInfo] = None
    landscape_consultant: Optional[ContactInfo] = None
    landscape_contractor: Optional[ContactInfo] = None
    automation_consultant: Optional[ContactInfo] = None
    readymade_furniture_supplier: Optional[ContactInfo] = None
    lights_supplier: Optional[ContactInfo] = None
    
    custom_contacts: dict = {}
    
    brands: List[BrandCategory] = []
    assigned_contractors: Dict[str, str] = {}
    checklist_preset_id: Optional[str] = None

class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    project_types: Optional[List[str]] = None
    status: Optional[ProjectStatus] = None
    lead_architect_id: Optional[str] = None
    project_manager_id: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    archived: Optional[bool] = None
    site_address: Optional[str] = None
    notes: Optional[str] = None
    
    civil_contractor: Optional[ContactInfo] = None
    structural_consultant: Optional[ContactInfo] = None
    tile_marble_contractor: Optional[ContactInfo] = None
    furniture_contractor: Optional[ContactInfo] = None
    electrical_contractor: Optional[ContactInfo] = None
    electrical_consultant: Optional[ContactInfo] = None
    plumbing_consultant: Optional[ContactInfo] = None
    plumbing_contractor: Optional[ContactInfo] = None
    false_ceiling_contractor: Optional[ContactInfo] = None
    furniture_material_supplier: Optional[ContactInfo] = None
    kitchen_contractor: Optional[ContactInfo] = None
    modular_contractor: Optional[ContactInfo] = None
    color_contractor: Optional[ContactInfo] = None
    landscape_consultant: Optional[ContactInfo] = None
    landscape_contractor: Optional[ContactInfo] = None
    automation_consultant: Optional[ContactInfo] = None
    readymade_furniture_supplier: Optional[ContactInfo] = None
    lights_supplier: Optional[ContactInfo] = None
    
    custom_contacts: Optional[dict] = None
    
    brands: Optional[List[BrandCategory]] = None
    assigned_contractors: Optional[Dict[str, str]] = None

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

class RevisionHistoryItem(BaseModel):
    """Individual revision cycle"""
    issued_date: datetime
    revision_requested_date: Optional[datetime] = None
    revision_notes: Optional[str] = None  # What revisions are needed
    revision_due_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None

class ProjectDrawing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    category: str  # Architecture, Interior, Landscape, Planning
    name: str  # Drawing name/title
    is_issued: bool = False  # Whether drawing has been issued
    issued_date: Optional[datetime] = None
    revision_count: int = 0  # Number of revisions
    has_pending_revision: bool = False  # True if there's a revision needed
    current_revision_notes: Optional[str] = None  # Current pending revision notes
    current_revision_due_date: Optional[datetime] = None  # Due date for current revision
    due_date: Optional[datetime] = None  # Original due date
    revision_history: List[RevisionHistoryItem] = []  # Complete revision history
    reminder_sent: bool = False
    notes: Optional[str] = None
    sequence_number: Optional[int] = None  # Order in the sequential workflow
    is_active: bool = True  # True if this drawing is currently active/pending in sequence
    file_url: Optional[str] = None  # URL to the issued drawing PDF
    revision_file_urls: List[str] = []  # URLs to revision PDFs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class ProjectDrawingCreate(BaseModel):
    project_id: str
    category: str  # Architecture, Interior, Landscape, Planning
    name: str
    due_date: Optional[str] = None
    notes: Optional[str] = None

class ProjectDrawingUpdate(BaseModel):
    name: Optional[str] = None
    is_issued: Optional[bool] = None
    has_pending_revision: Optional[bool] = None
    revision_notes: Optional[str] = None  # What revisions are needed
    revision_due_date: Optional[str] = None  # When revised drawing is due
    due_date: Optional[str] = None
    notes: Optional[str] = None
    file_url: Optional[str] = None  # PDF file URL
    revision_file_urls: Optional[List[str]] = None  # Revision PDF URLs

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

class DrawingComment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    drawing_id: str  # ProjectDrawing ID
    user_id: str  # User ID (can be client, contractor, consultant, team member)
    user_name: str  # Store user name for display
    user_role: str  # Store user role (client, contractor, consultant, team_member, owner)
    comment_text: str
    reference_files: List[str] = []  # URLs to uploaded reference images/PDFs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class DrawingCommentCreate(BaseModel):
    drawing_id: str
    comment_text: str

class DrawingCommentUpdate(BaseModel):
    comment_text: str

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


# ==================== WEEKLY TARGET & DAILY TASK SYSTEM ====================

class WeeklyTarget(BaseModel):
    """Weekly target assigned every Monday"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assigned_to_id: str  # Team member ID
    week_start_date: datetime  # Monday
    week_end_date: datetime  # Sunday
    target_type: str  # "drawing_completion", "site_visit", "revision", etc.
    target_description: str
    target_quantity: int  # Number of tasks to complete
    completed_quantity: int = 0
    project_id: Optional[str] = None
    drawing_ids: List[str] = []  # Related drawings
    status: str = "active"  # active, completed, overdue
    rating: Optional[float] = None  # 0-5 rating, calculated on Saturday
    created_by_id: str  # Owner/Manager who assigned
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DailyTask(BaseModel):
    """Daily breakdown of weekly target"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    weekly_target_id: str
    assigned_to_id: str  # Team member ID
    task_date: datetime  # Specific date
    task_description: str
    task_quantity: int  # Portion of weekly target
    completed: bool = False
    completed_at: Optional[datetime] = None
    project_id: Optional[str] = None
    drawing_id: Optional[str] = None
    notes: Optional[str] = None
    whatsapp_sent: bool = False
    whatsapp_sent_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ==================== CONTRACTOR/CONSULTANT MODELS ====================

class ContractorType(str, Enum):
    CIVIL = "Civil"
    PLUMBING = "Plumbing"
    ELECTRICAL = "Electrical"
    AIR_CONDITIONING = "Air Conditioning"
    MARBLE_TILE = "Marble and Tile"
    FALSE_CEILING = "False Ceiling"
    FURNITURE = "Furniture"
    MODULAR = "Modular"
    KITCHEN = "Kitchen"
    LANDSCAPE = "Landscape"
    GLASS = "Glass"
    PROFILE = "Profile"
    GARDNER = "Gardner"
    FABRICATOR = "Fabricator"
    CUSTOM = "Custom"  # For custom types

class Contractor(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contractor_type: str  # Civil, Plumbing, etc.
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    notes: Optional[str] = None
    unique_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])  # Short unique code
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    deleted_at: Optional[datetime] = None

class ContractorCreate(BaseModel):
    name: str
    contractor_type: str
    company_name: Optional[str] = None
    email: Optional[str] = None
    phone: str
    alternate_phone: Optional[str] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    notes: Optional[str] = None

class WeeklyRating(BaseModel):
    """Weekly performance rating calculated on Saturday"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    team_member_id: str
    week_start_date: datetime
    week_end_date: datetime
    total_targets: int
    completed_targets: int
    completion_percentage: float
    rating: float  # 0-5 scale
    feedback: Optional[str] = None
    weekly_targets: List[str] = []  # List of weekly_target_ids
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class WeeklyTargetCreate(BaseModel):
    assigned_to_id: str
    week_start_date: str  # ISO date string
    target_type: str
    target_description: str
    target_quantity: int
    project_id: Optional[str] = None
    drawing_ids: List[str] = []
    daily_breakdown: Optional[List[int]] = None  # How to split across days

class DailyTaskCreate(BaseModel):
    weekly_target_id: str
    assigned_to_id: str
    task_date: str
    task_description: str
    task_quantity: int
    project_id: Optional[str] = None
    drawing_id: Optional[str] = None

class DailyTaskUpdate(BaseModel):
    completed: Optional[bool] = None
    notes: Optional[str] = None

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
