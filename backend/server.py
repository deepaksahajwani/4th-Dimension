from fastapi import FastAPI, APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType
import random
import string

# Import new project models
from models_projects import (
    DrawingStatus, ConsultantType, Consultant, ConsultantCreate, ProjectDrawing, Task, TaskCreate, SiteVisit, SiteVisitCreate,
    SiteIssue, SiteIssueCreate, ChecklistPreset, DrawingType, ClientUpdate,
    Client as NewClient, ClientCreate as NewClientCreate,
    Project as NewProject, ProjectCreate as NewProjectCreate, ProjectUpdate as NewProjectUpdate,
    BrandCategoryMaster, BrandCategoryMasterCreate, BrandCategoryMasterUpdate,
    ContactTypeMaster, ContactTypeMasterCreate, ContactTypeMasterUpdate,
    ProjectDrawingCreate, ProjectDrawingUpdate,
    WeeklyTarget, DailyTask, WeeklyRating, WeeklyTargetCreate, DailyTaskUpdate,
    DrawingComment, DrawingCommentCreate, DrawingCommentUpdate,
    TeamMemberVerification, VerifyEmailRequest, VerifyPhoneRequest, ResendOTPRequest,
    Contractor, ContractorCreate, ContractorType,
    Vendor, VendorCreate, VendorUpdate, VendorType
)
from models_coclients import CoClientCreate
from drawing_templates import get_template_drawings
from email_templates import get_welcome_email_content

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Import notification_triggers AFTER loading .env so WhatsApp service can access credentials
import notification_triggers

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# JWT settings
JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'your-secret-key')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRE_MINUTES = int(os.environ.get('JWT_EXPIRE_MINUTES', 10080))

# File storage settings
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 524288000))
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Logger setup
logger = logging.getLogger(__name__)

# Email Configuration - Consistent sender name for all emails
EMAIL_SENDER_ADDRESS = os.getenv('SENDER_EMAIL', 'contact@4thdimensionarchitect.com')
EMAIL_SENDER_NAME = "4th Dimension Architects"

def get_email_sender():
    """Get SendGrid Email object with consistent sender name"""
    from sendgrid.helpers.mail import Email
    return Email(EMAIL_SENDER_ADDRESS, EMAIL_SENDER_NAME)

# Create the main app without a prefix
app = FastAPI(title="Architecture Firm Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# ==================== HEALTH CHECK ENDPOINT (Cold-Start Prevention) ====================

@app.get("/health")
async def health_check():
    """
    Lightweight health check endpoint for keep-alive pings.
    Use with UptimeRobot or cron job every 5 minutes to prevent cold starts.
    """
    return {"ok": True, "status": "healthy"}

@api_router.get("/health")
async def api_health_check():
    """API-prefixed health check"""
    return {"ok": True, "status": "healthy"}


# ==================== MODELS ====================

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    name: str
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    landmark: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pin_code: Optional[str] = None
    mobile: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    date_of_joining: Optional[datetime] = None  # Date of joining the firm
    gender: Optional[str] = None  # male, female, other
    marital_status: Optional[str] = None  # single, married, divorced, widowed
    role: str  # owner, team_member, client, contractor, consultant
    preferred_language: str = 'en'  # en, hi, ta, mr, gu
    salary: Optional[float] = None  # Monthly salary (owner only can see/edit)
    writeup: Optional[str] = None  # Brief writeup about the team member (owner sets)
    passions: Optional[str] = None  # Passions and hobbies
    contribution: Optional[str] = None  # Contribution to firm growth
    password_hash: Optional[str] = None
    picture: Optional[str] = None
    is_owner: bool = False  # Only for Deepak Sahajwani
    is_admin: bool = False
    is_validated: bool = False  # Requires owner approval after OTP verification
    approval_status: str = "pending"  # pending, approved, rejected
    mobile_verified: bool = False
    email_verified: bool = False
    registration_completed: bool = False  # Details form completed
    registered_via: Optional[str] = None  # email, google
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str

class PublicRegistration(BaseModel):
    """New public self-registration model"""
    name: str
    email: EmailStr
    mobile: str
    registration_type: str  # client, team_member, contractor, vendor, consultant
    preferred_language: str = 'en'  # en, hi, ta, mr, gu
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    pin_code: str
    registered_via: str  # email or google

class VerifyRegistrationOTP(BaseModel):
    """Verify both email and phone OTPs"""
    email: EmailStr
    email_otp: str
    phone_otp: str

class SetPasswordAfterOTP(BaseModel):
    """Set password after OTP verification (for email registration only)"""
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    """Request password reset"""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Reset password with token"""
    token: str
    new_password: str

class CompleteProfile(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: str
    landmark: Optional[str] = None
    city: str
    state: str
    pin_code: str
    email: EmailStr
    mobile: str
    date_of_birth: str
    date_of_joining: str  # Date of joining the firm
    gender: str
    marital_status: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UpdateTeamMember(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: str
    landmark: Optional[str] = None
    city: str
    state: str
    pin_code: str
    mobile: str
    date_of_birth: str
    date_of_joining: str
    gender: str
    marital_status: str
    role: str
    salary: Optional[float] = None
    writeup: Optional[str] = None
    passions: Optional[str] = None
    contribution: Optional[str] = None

class InviteTeamMember(BaseModel):
    email: EmailStr
    name: str
    phone: str
    role: str

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Old Client and ClientCreate models removed - now using models from models_projects.py

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    project_type: str  # Architecture, Interior, Planning, Landscape
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    team_leader: Optional[str] = None  # User ID
    status: str  # consultation, layout_design, elevation_design, structural, execution, interior, completed
    assigned_to: List[str] = []  # User IDs
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    plan_finalized: bool = False
    plan_revisions: int = 0
    first_advance_received: bool = False

class ProjectCreate(BaseModel):
    client_id: str
    project_type: str
    name: str
    address: Optional[str] = None
    city: Optional[str] = None
    team_leader: Optional[str] = None
    assigned_to: Optional[List[str]] = []

class Drawing(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    category: str  # Architectural, Structural, Plumbing, Electrical, HVAC, Furniture, Ceiling, Kitchen, Landscape, Others
    name: str
    description: Optional[str] = None
    order: int = 0
    status: str  # pending, in_progress, review, issued, approved
    s3_key: Optional[str] = None
    issue_date: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ai_review: Optional[dict] = None

class DrawingCreate(BaseModel):
    project_id: str
    category: str
    name: str
    description: Optional[str] = None
    order: int = 0

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None  # User ID
    due_date: Optional[datetime] = None
    status: str  # open, in_progress, resolved, closed
    priority: str  # low, medium, high, red_flag
    created_by: str  # User ID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

class TaskCreate(BaseModel):
    project_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_to_id: Optional[str] = None  # For ad-hoc tasks
    due_date: Optional[str] = None
    due_date_time: Optional[str] = None  # For ad-hoc tasks with specific time
    priority: str = "medium"
    category: Optional[str] = None
    status: Optional[str] = "open"

class Reminder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: Optional[str] = None
    task_id: Optional[str] = None
    drawing_id: Optional[str] = None
    reminder_type: str
    message: str
    next_reminder_date: datetime
    recurring: bool = False
    recurring_days: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Revision(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_id: str
    revision_type: str  # layout, elevation, structural, interior
    revision_number: int
    description: str
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    s3_key: Optional[str] = None

class RevisionCreate(BaseModel):
    project_id: str
    revision_type: str
    description: str

class Accounting(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transaction_type: str  # receivable, payment, salary, expense
    amount: float
    project_id: Optional[str] = None
    user_id: Optional[str] = None  # For salaries
    description: str
    category: Optional[str] = None
    date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str

class AccountingCreate(BaseModel):
    transaction_type: str
    amount: float
    project_id: Optional[str] = None
    user_id: Optional[str] = None
    description: str
    category: Optional[str] = None

class DrawingTemplate(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    description: Optional[str] = None
    order: int
    project_type: str  # architectural, interior, both

class DrawingTemplateCreate(BaseModel):
    name: str
    category: str
    description: Optional[str] = None
    order: int
    project_type: str

class OTP(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    otp_code: str
    action: str  # add_member, delete_member
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class OTPRequest(BaseModel):
    action: str  # add_member, delete_member
    target_user_id: Optional[str] = None  # For delete action

class OTPVerify(BaseModel):
    otp_code: str
    action: str
    target_user_id: Optional[str] = None

class PhoneOTPRequest(BaseModel):
    phone: str
    
class EmailVerificationToken(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UpdateUserAdmin(BaseModel):
    user_id: str
    is_admin: bool


# ==================== HELPER FUNCTIONS ====================

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    
    try:
        # Check if it's a JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        user_doc = await db.users.find_one({"email": email}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)
    
    except JWTError:
        # Try Emergent session token
        session = await db.user_sessions.find_one({"session_token": token})
        if not session:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        
        # Check expiry
        if isinstance(session['expires_at'], str):
            expires_at = datetime.fromisoformat(session['expires_at'])
        else:
            expires_at = session['expires_at']
        
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="Session expired")
        
        user_doc = await db.users.find_one({"id": session['user_id']}, {"_id": 0})
        if not user_doc:
            raise HTTPException(status_code=401, detail="User not found")
        
        return User(**user_doc)

async def require_owner(current_user: User = Depends(get_current_user)):
    if not current_user.is_owner:
        raise HTTPException(status_code=403, detail="Only owner can perform this action")
    return current_user

async def require_admin(current_user: User = Depends(get_current_user)):
    if not current_user.is_owner and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only owner or administrator can perform this action")
    return current_user

async def require_owner_or_team_leader(current_user: User = Depends(get_current_user)):
    """Allow owner or team members (who can be team leaders)"""
    if not current_user.is_owner and current_user.role != 'team_member':
        raise HTTPException(status_code=403, detail="Only owner or team leader can perform this action")
    return current_user


# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Auto-detect user role based on email
    # Check if email exists in Clients collection
    client = await db.clients.find_one({"email": user_data.email}, {"_id": 0})
    
    # Check if email exists in Contractors collection
    contractor = await db.contractors.find_one({"email": user_data.email}, {"_id": 0})
    
    # Determine role
    if client:
        detected_role = "client"
        is_external_user = True
    elif contractor:
        detected_role = "contractor"  # This covers both contractors and consultants
        is_external_user = True
    else:
        detected_role = "team_member"
        is_external_user = False
    
    # Check if this is the owner (Deepak Sahajwani)
    is_owner_email = user_data.email.lower() in ["deepaksahajwani@gmail.com", "deepak@4thdimension.com"] or user_data.name.lower() == "deepak sahajwani"
    
    # If owner, create complete profile automatically
    if is_owner_email:
        user = User(
            email=user_data.email,
            name="Deepak Shreechand Sahajwani",  # Full name
            address_line_1="",  # Can be updated later
            address_line_2="",
            landmark="",
            city="",
            state="",
            pin_code="",
            mobile="+919913899888",
            date_of_birth=datetime(1973, 9, 15),
            date_of_joining=datetime(2010, 1, 1),  # Founder date
            gender="male",
            marital_status="married",
            role="owner",
            password_hash=get_password_hash(user_data.password),
            is_owner=True,
            is_validated=True,
            mobile_verified=True,
            email_verified=True,
            registration_completed=True  # Profile already complete
        )
    else:
        # Regular user - auto-assign role based on email detection
        # External users (clients/contractors/consultants) are auto-validated
        user = User(
            email=user_data.email,
            name=user_data.name,
            role=detected_role,
            password_hash=get_password_hash(user_data.password),
            is_owner=False,
            is_validated=is_external_user,  # Auto-validate clients/contractors
            registration_completed=is_external_user  # External users don't need profile completion
        )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    if user_dict.get('date_of_birth'):
        user_dict['date_of_birth'] = user_dict['date_of_birth'].isoformat()
    if user_dict.get('date_of_joining'):
        user_dict['date_of_joining'] = user_dict['date_of_joining'].isoformat()
    
    await db.users.insert_one(user_dict)
    
    # Send notification to owner about new registration (if not owner registering)
    if not is_owner_email:
        try:
            # Create in-app notification for owner
            owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
            if owner:
                notification = {
                    "id": str(uuid4()),
                    "user_id": owner["id"],
                    "message": f"New registration: {user.name} ({user.email}) - Role: {detected_role}",
                    "link": "/pending-registrations",
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.notifications.insert_one(notification)
                
                # Send WhatsApp notification to owner (non-blocking)
                try:
                    await notification_triggers.notify_owner_new_registration(
                        user.name,
                        user.email,
                        detected_role
                    )
                except Exception as e:
                    print(f"WhatsApp notification failed (non-critical): {str(e)}")
        except Exception as e:
            print(f"Failed to notify owner about new registration: {str(e)}")
    
    # Create token
    access_token = create_access_token(data={"sub": user.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "is_owner": user.is_owner,
            "is_validated": user.is_validated,
            "registration_completed": user.registration_completed
        },
        "requires_profile_completion": not user.registration_completed
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Check approval status
    approval_status = user_doc.get('approval_status', 'approved')
    if approval_status == 'rejected':
        raise HTTPException(
            status_code=403, 
            detail="Your registration was rejected. Please contact admin or register again with updated information."
        )
    elif approval_status == 'pending':
        raise HTTPException(
            status_code=403, 
            detail="Your registration is pending approval. Please wait for admin approval."
        )
    
    if not user_doc.get('password_hash'):
        raise HTTPException(status_code=401, detail="Please use Google login")
    
    if not verify_password(credentials.password, user_doc['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": credentials.email})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user_doc['id'],
            "email": user_doc['email'],
            "name": user_doc['name'],
            "role": user_doc.get('role', ''),
            "is_owner": user_doc.get('is_owner', False),
            "is_validated": user_doc.get('is_validated', False),
            "approval_status": user_doc.get('approval_status', 'approved'),
            "registration_completed": user_doc.get('registration_completed', False)
        },
        "requires_profile_completion": not user_doc.get('registration_completed', False)
    }

@api_router.post("/auth/google/session")
async def process_google_session(session_id: str):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers={"X-Session-ID": session_id}
            )
            response.raise_for_status()
            session_data = response.json()
        
        # Check if user exists
        user_doc = await db.users.find_one({"email": session_data['email']}, {"_id": 0})
        
        if not user_doc:
            # Check if this is the owner
            is_owner = session_data['email'].lower() in ["deepaksahajwani@gmail.com", "deepak@4thdimension.com"]
            
            if is_owner:
                # Create owner with complete profile
                user = User(
                    email=session_data['email'],
                    name="Deepak Shreechand Sahajwani",
                    postal_address="",
                    mobile="+919913899888",
                    date_of_birth=datetime(1973, 9, 15),
                    gender="male",
                    marital_status="married",
                    role="owner",
                    picture=session_data.get('picture'),
                    is_owner=True,
                    is_validated=True,
                    mobile_verified=True,
                    email_verified=True,
                    registration_completed=True
                )
            else:
                # Create new user - needs profile completion
                user = User(
                    email=session_data['email'],
                    name=session_data['name'],
                    role="pending",
                    picture=session_data.get('picture'),
                    is_owner=False,
                    is_validated=False,
                    registration_completed=False
                )
            
            user_dict = user.model_dump()
            user_dict['created_at'] = user_dict['created_at'].isoformat()
            if user_dict.get('date_of_birth'):
                user_dict['date_of_birth'] = user_dict['date_of_birth'].isoformat()
            await db.users.insert_one(user_dict)
            user_id = user.id
        else:
            user_id = user_doc['id']
        
        # Create session
        session = UserSession(
            user_id=user_id,
            session_token=session_data['session_token'],
            expires_at=datetime.now(timezone.utc) + timedelta(days=7)
        )
        
        session_dict = session.model_dump()
        session_dict['created_at'] = session_dict['created_at'].isoformat()
        session_dict['expires_at'] = session_dict['expires_at'].isoformat()
        
        await db.user_sessions.insert_one(session_dict)
        
        # Get user data
        user_doc = await db.users.find_one({"id": user_id}, {"_id": 0})
        
        return {
            "session_token": session_data['session_token'],
            "user": {
                "id": user_doc['id'],
                "email": user_doc['email'],
                "name": user_doc['name'],
                "role": user_doc.get('role', ''),
                "is_owner": user_doc.get('is_owner', False),
                "is_validated": user_doc.get('is_validated', False),
                "approval_status": user_doc.get('approval_status', 'approved'),
                "registration_completed": user_doc.get('registration_completed', False),
                "picture": user_doc.get('picture')
            },
            "requires_profile_completion": not user_doc.get('registration_completed', False)
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@api_router.post("/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    await db.user_sessions.delete_one({"session_token": token})
    return {"message": "Logged out successfully"}



# ==================== PUBLIC SELF-REGISTRATION ROUTES ====================

@api_router.post("/auth/public-register")
async def public_register(registration_data: PublicRegistration):
    """
    Public self-registration with OTP verification
    Step 1: Submit registration details and send OTPs
    """
    try:
        # Check if user already exists with approved status
        # Note: We check for deleted_at to allow re-registration of deleted users
        existing_user = await db.users.find_one({"email": registration_data.email, "deleted_at": None}, {"_id": 0})
        if existing_user:
            # Allow re-registration for rejected users
            if existing_user.get('approval_status') == 'rejected':
                # Delete the rejected user to allow fresh registration
                await db.users.delete_one({"email": registration_data.email})
            elif existing_user.get('approval_status') == 'approved':
                raise HTTPException(status_code=400, detail="Email already registered. Please login instead.")
            elif existing_user.get('approval_status') == 'pending':
                raise HTTPException(status_code=400, detail="Registration pending approval. Please wait for admin approval.")
        
        # Also clean up any soft-deleted user records with the same email
        await db.users.delete_many({"email": registration_data.email, "deleted_at": {"$ne": None}})
        
        # Check if there's a pending registration
        pending_reg = await db.pending_registrations.find_one({"email": registration_data.email}, {"_id": 0})
        if pending_reg:
            # Delete old pending registration
            await db.pending_registrations.delete_one({"email": registration_data.email})
        
        # Generate OTPs
        import verification_service
        email_otp = verification_service.generate_otp()
        phone_otp = verification_service.generate_otp()
        
        # Store pending registration with OTPs
        pending_registration = {
            "id": str(uuid.uuid4()),
            "name": registration_data.name,
            "email": registration_data.email,
            "mobile": registration_data.mobile,
            "registration_type": registration_data.registration_type,
            "preferred_language": registration_data.preferred_language,
            "address_line_1": registration_data.address_line_1,
            "address_line_2": registration_data.address_line_2,
            "city": registration_data.city,
            "state": registration_data.state,
            "pin_code": registration_data.pin_code,
            "registered_via": registration_data.registered_via,
            "email_otp": email_otp,
            "phone_otp": phone_otp,
            "email_verified": False,
            "phone_verified": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        }
        
        await db.pending_registrations.insert_one(pending_registration)
        
        # Send email OTP
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5;">Welcome to 4th Dimension!</h1>
                        <p style="color: #666;">Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937;">Hello {registration_data.name},</h2>
                    <p>Thank you for registering with 4th Dimension as a <strong>{registration_data.registration_type.replace('_', ' ').title()}</strong>.</p>
                    
                    <div style="background: #FEF3C7; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0 0 10px 0;"><strong>Your Email Verification OTP:</strong></p>
                        <div style="font-size: 36px; font-weight: bold; color: #D97706; letter-spacing: 8px; text-align: center; padding: 15px; background: white; border-radius: 5px;">
                            {email_otp}
                        </div>
                        <p style="margin: 10px 0 0 0; font-size: 12px; color: #92400E; text-align: center;">
                            This OTP will expire in 1 hour
                        </p>
                    </div>
                    
                    <p>A separate OTP has been sent to your mobile number <strong>{registration_data.mobile}</strong> for phone verification.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                        <p><strong>4th Dimension - Architecture & Design</strong><br>Building Dreams, Creating Realities</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=get_email_sender(),
            to_emails=registration_data.email,
            subject='Verify Your Registration - 4th Dimension',
            html_content=html_content
        )
        
        sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        email_response = sendgrid_client.send(message)
        email_sent = email_response.status_code in [200, 201, 202]
        
        # Send SMS OTP (will fail for unverified numbers in trial)
        sms_success, sms_error = await verification_service.send_verification_sms(
            phone_number=registration_data.mobile,
            otp=phone_otp
        )
        
        return {
            "message": "Registration submitted. Please verify your email and phone with OTPs.",
            "email_sent": email_sent,
            "sms_sent": sms_success,
            "registration_id": pending_registration["id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Public registration error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@api_router.post("/auth/verify-registration-otp")
async def verify_registration_otp(otp_data: VerifyRegistrationOTP):
    """
    Step 2: Verify both email and phone OTPs
    """
    try:
        # Find pending registration
        pending_reg = await db.pending_registrations.find_one(
            {"email": otp_data.email},
            {"_id": 0}
        )
        
        if not pending_reg:
            raise HTTPException(status_code=404, detail="Registration not found or expired")
        
        # Check expiry
        expires_at = datetime.fromisoformat(pending_reg['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            await db.pending_registrations.delete_one({"email": otp_data.email})
            raise HTTPException(status_code=400, detail="OTPs expired. Please register again.")
        
        # Verify Email OTP (our generated OTP)
        if pending_reg['email_otp'] != otp_data.email_otp:
            raise HTTPException(status_code=400, detail="Invalid email OTP")
        
        # Verify Phone OTP
        if pending_reg['phone_otp'] != otp_data.phone_otp:
            raise HTTPException(status_code=400, detail="Invalid phone OTP")
        
        phone_verified = True
        print("✅ Phone OTP verified successfully")
        
        # Mark as verified
        await db.pending_registrations.update_one(
            {"email": otp_data.email},
            {"$set": {
                "email_verified": True,
                "phone_verified": True
            }}
        )
        
        return {
            "message": "OTPs verified successfully",
            "registered_via": pending_reg['registered_via'],
            "requires_password": pending_reg['registered_via'] == 'email'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"OTP verification error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")

@api_router.post("/auth/set-password-after-otp")
async def set_password_after_otp(password_data: SetPasswordAfterOTP):
    """
    Step 3: Set password after OTP verification (for email registration only)
    Then create user and send approval email to owner
    """
    try:
        # Find pending registration
        pending_reg = await db.pending_registrations.find_one(
            {"email": password_data.email, "email_verified": True, "phone_verified": True},
            {"_id": 0}
        )
        
        if not pending_reg:
            raise HTTPException(status_code=404, detail="Verified registration not found")
        
        # Create user account
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=pending_reg['email'],
            name=pending_reg['name'],
            mobile=pending_reg['mobile'],
            address_line_1=pending_reg['address_line_1'],
            address_line_2=pending_reg.get('address_line_2'),
            city=pending_reg['city'],
            state=pending_reg['state'],
            pin_code=pending_reg['pin_code'],
            role=pending_reg['registration_type'],
            preferred_language=pending_reg.get('preferred_language', 'en'),
            password_hash=get_password_hash(password_data.password) if pending_reg['registered_via'] == 'email' else None,
            is_owner=False,
            is_validated=False,
            approval_status="pending",
            email_verified=True,
            mobile_verified=True,
            registration_completed=True,
            registered_via=pending_reg['registered_via']
        )
        
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        
        await db.users.insert_one(user_dict)
        
        # Create corresponding client/contractor/consultant record based on role
        if pending_reg['registration_type'] == 'client':
            client_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": pending_reg['name'],
                "contact_person": pending_reg['name'],
                "email": pending_reg['email'],
                "phone": pending_reg['mobile'],
                "address": f"{pending_reg.get('address_line_1', '')}, {pending_reg.get('city', '')}, {pending_reg.get('state', '')}".strip(', '),
                "created_at": datetime.now(timezone.utc),
                "created_by": user_id,
                "notes": "",
                "archived": False
            }
            await db.clients.insert_one(client_record)
            print(f"✅ Client record created for {pending_reg['name']}")
            
        elif pending_reg['registration_type'] == 'contractor':
            contractor_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": pending_reg['name'],
                "email": pending_reg['email'],
                "phone": pending_reg['mobile'],
                "address": f"{pending_reg.get('address_line_1', '')}, {pending_reg.get('city', '')}, {pending_reg.get('state', '')}".strip(', '),
                "contractor_type": "Pending Assignment",  # Will be set during approval
                "created_at": datetime.now(timezone.utc),
                "created_by": user_id,
                "notes": "Awaiting role assignment during approval"
            }
            await db.contractors.insert_one(contractor_record)
            print(f"✅ Contractor record created for {pending_reg['name']}")
            
        elif pending_reg['registration_type'] == 'consultant':
            consultant_record = {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "name": pending_reg['name'],
                "email": pending_reg['email'],
                "phone": pending_reg['mobile'],
                "address": f"{pending_reg.get('address_line_1', '')}, {pending_reg.get('city', '')}, {pending_reg.get('state', '')}".strip(', '),
                "type": "Pending Assignment",  # Will be set during approval
                "created_at": datetime.now(timezone.utc),
                "created_by": user_id,
                "notes": "Awaiting role assignment during approval"
            }
            await db.consultants.insert_one(consultant_record)
            print(f"✅ Consultant record created for {pending_reg['name']}")
        
        # Delete pending registration
        await db.pending_registrations.delete_one({"email": password_data.email})
        
        # Send registration notifications using new system
        try:
            from notification_triggers_v2 import notify_user_registration
            await notify_user_registration(user_dict)
        except Exception as e:
            print(f"Registration notification failed (non-critical): {str(e)}")
        
        return {
            "message": "Registration complete. Awaiting owner approval.",
            "user_id": user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Password setup error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete registration: {str(e)}")

async def send_approval_request_email(owner_email: str, user_data: dict):
    """Send approval request email to owner"""
    try:
        backend_url = os.getenv('REACT_APP_BACKEND_URL')
        approval_link = f"{backend_url}/api/approve-user?user_id={user_data['id']}&action=approve"
        reject_link = f"{backend_url}/api/approve-user?user_id={user_data['id']}&action=reject"
        
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #4F46E5;">New Registration Pending Approval</h2>
                    
                    <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <p><strong>Name:</strong> {user_data['name']}</p>
                        <p><strong>Email:</strong> {user_data['email']}</p>
                        <p><strong>Mobile:</strong> {user_data['mobile']}</p>
                        <p><strong>Registration Type:</strong> {user_data['role'].replace('_', ' ').title()}</p>
                        <p><strong>Address:</strong> {user_data['address_line_1']}, {user_data['city']}, {user_data['state']}</p>
                    </div>
                    
                    <!-- Approve Button -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 20px 0;">
                        <tr>
                            <td align="center">
                                <table cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td align="center" bgcolor="#10B981" style="border-radius: 6px;">
                                            <a href="{approval_link}" target="_blank" style="font-size: 16px; font-family: Arial, sans-serif; color: #ffffff; text-decoration: none; border-radius: 6px; padding: 15px 50px; border: 1px solid #10B981; display: inline-block; font-weight: bold;">
                                                ✓ APPROVE
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Reject Button -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 20px 0;">
                        <tr>
                            <td align="center">
                                <table cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td align="center" bgcolor="#EF4444" style="border-radius: 6px;">
                                            <a href="{reject_link}" target="_blank" style="font-size: 16px; font-family: Arial, sans-serif; color: #ffffff; text-decoration: none; border-radius: 6px; padding: 15px 50px; border: 1px solid #EF4444; display: inline-block; font-weight: bold;">
                                                ✕ REJECT
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <!-- Backup text links -->
                    <p style="color: #666; font-size: 13px; text-align: center; margin-top: 20px; padding: 15px; background: #F9FAFB; border-radius: 6px;">
                        <strong>Can't see the buttons?</strong> Click these links:<br><br>
                        <a href="{approval_link}" target="_blank" style="color: #10B981; text-decoration: underline; font-weight: bold;">
                            Approve Registration
                        </a>
                        &nbsp;|&nbsp;
                        <a href="{reject_link}" target="_blank" style="color: #EF4444; text-decoration: underline; font-weight: bold;">
                            Reject Registration
                        </a>
                    </p>
                    
                    <p style="color: #666; font-size: 12px; text-align: center; margin-top: 20px;">
                        Or visit your dashboard:<br>
                        <a href="{backend_url}/pending-registrations" target="_blank" style="color: #4F46E5; text-decoration: underline;">
                            {backend_url}/pending-registrations
                        </a>
                    </p>
                </div>
            </body>
        </html>
        """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=get_email_sender(),
            to_emails=owner_email,
            subject=f'New Registration - {user_data["name"]} ({user_data["role"].replace("_", " ").title()})',
            html_content=html_content
        )
        
        sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sendgrid_client.send(message)
        
    except Exception as e:
        print(f"Failed to send approval email: {str(e)}")

async def send_registration_complete_email(user_data: dict):
    """Send welcome email to newly registered user"""
    try:
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5;">Welcome to the 4th Dimension Family!</h1>
                        <p style="color: #666;">Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937;">Dear {user_data['name']},</h2>
                    
                    <p>We are delighted to welcome you to the 4th Dimension family! Your registration as a <strong>{user_data['role'].replace('_', ' ').title()}</strong> has been received.</p>
                    
                    <div style="background: #EEF2FF; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="color: #4F46E5; margin-top: 0;">Your Login Credentials:</h3>
                        <p><strong>Username (Email):</strong> {user_data['email']}</p>
                        {'<p><strong>Password:</strong> As set during registration</p>' if user_data.get('registered_via') == 'email' else '<p><strong>Login Method:</strong> Google Account</p>'}
                        <p style="color: #DC2626; font-size: 14px; margin-top: 10px;">
                            <strong>⚠️ Please save these credentials securely</strong>
                        </p>
                    </div>
                    
                    <div style="background: #FEF3C7; padding: 15px; border-radius: 8px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>📝 Registration Status:</strong> Pending Approval</p>
                        <p style="margin: 10px 0 0 0; font-size: 14px;">
                            Your registration is currently being reviewed by our team. You will receive an email notification once your account is approved.
                        </p>
                    </div>
                    
                    <p>At 4th Dimension, we transform architectural dreams into reality. We look forward to your valuable contribution to our company and are excited to have you on board.</p>
                    
                    <p>If you have any questions, feel free to reach out to us.</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666;">
                        <p style="font-size: 18px; color: #4F46E5; font-weight: bold;">Building Dreams, Creating Realities</p>
                        <p style="margin-top: 15px;">
                            <strong>4th Dimension - Architecture & Design</strong><br>
                            Contact: contact@4thdimensionarchitect.com
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=get_email_sender(),
            to_emails=user_data['email'],
            subject='Welcome to 4th Dimension Family!',
            html_content=html_content
        )
        
        sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sendgrid_client.send(message)
        
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")


# ==================== TEAM MEMBER VERIFICATION ROUTES ====================

import verification_service

@api_router.post("/invite/send")
async def send_invite(
    name: str,
    phone: str,
    invitee_type: str,
    current_user: User = Depends(get_current_user)
):
    """
    Send WhatsApp invite to register
    invitee_type: 'team_member', 'client', 'contractor', 'consultant'
    """
    try:
        from invite_service import send_registration_invite
        
        result = await send_registration_invite(
            name=name,
            phone=phone,
            invitee_type=invitee_type,
            invited_by_name=current_user.name
        )
        
        if result['success']:
            return {
                "success": True,
                "message": result['message']
            }
        else:
            raise HTTPException(status_code=500, detail=result['message'])
            
    except Exception as e:
        logger.error(f"Error sending invite: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/team/invite")
async def invite_team_member(
    invite_data: InviteTeamMember,
    current_user: User = Depends(require_owner)
):
    """
    Owner invites team member - sends verification email and SMS (OLD METHOD)
    """
    try:
        # Check if user already exists
        existing_user = await db.users.find_one({"email": invite_data.email}, {"_id": 0})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create user with unverified status
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            email=invite_data.email,
            name=invite_data.name,
            role=invite_data.role,
            is_owner=False,
            is_validated=False,
            email_verified=False,
            mobile_verified=False,
            registration_completed=False
        )
        
        user_dict = user.model_dump()
        user_dict['created_at'] = user_dict['created_at'].isoformat()
        await db.users.insert_one(user_dict)
        
        # Generate verification tokens and OTPs
        email_token = verification_service.generate_verification_token()
        email_otp = verification_service.generate_otp()
        phone_otp = verification_service.generate_otp()
        
        # Store verification data
        verification = TeamMemberVerification(
            user_id=user_id,
            email=invite_data.email,
            phone=invite_data.phone,
            email_verification_token=email_token,
            email_otp=email_otp,
            phone_otp=phone_otp,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        
        verification_dict = verification.model_dump()
        verification_dict['created_at'] = verification_dict['created_at'].isoformat()
        verification_dict['otp_created_at'] = verification_dict['otp_created_at'].isoformat()
        verification_dict['expires_at'] = verification_dict['expires_at'].isoformat()
        
        await db.team_verifications.insert_one(verification_dict)
        
        # Generate verification link
        frontend_url = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:3000')
        verification_link = f"{frontend_url}/verify-email?token={email_token}"
        
        # Send verification email
        email_success, email_error = await verification_service.send_verification_email(
            to_email=invite_data.email,
            user_name=invite_data.name,
            verification_link=verification_link,
            otp=email_otp
        )
        
        if not email_success:
            print(f"Failed to send email: {email_error}")
        
        # Send verification SMS
        sms_success, sms_error = await verification_service.send_verification_sms(
            phone_number=invite_data.phone,
            otp=phone_otp
        )
        
        if not sms_success:
            print(f"Failed to send SMS: {sms_error}")
        
        return {
            "message": "Team member invited successfully",
            "user_id": user_id,
            "email_sent": email_success,
            "sms_sent": sms_success
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error inviting team member: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to invite team member: {str(e)}")

@api_router.get("/approve-user")
async def approve_reject_user(user_id: str, action: str):
    """
    Approve or reject user registration (called from email link)
    No authentication required - email link itself is the authorization
    Redirects to dashboard with success message
    """
    from fastapi.responses import RedirectResponse
    
    try:
        frontend_url = os.getenv('REACT_APP_BACKEND_URL')
        
        if action not in ['approve', 'reject']:
            return RedirectResponse(url=f"{frontend_url}/login?error=invalid_action")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            return RedirectResponse(url=f"{frontend_url}/login?error=user_not_found")
        
        if action == 'approve':
            await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "approval_status": "approved",
                    "is_validated": True
                }}
            )
            
            # Send approval notification to user
            await send_approval_notification(user, approved=True)
            
            # Send WhatsApp notification (don't fail if WhatsApp is not configured)
            try:
                await notification_triggers.notify_user_approved(user_id)
            except Exception as e:
                print(f"WhatsApp notification failed (non-critical): {str(e)}")
            
            # Redirect to success page (preserves owner's login state)
            from urllib.parse import quote
            user_name_encoded = quote(user['name'])
            return RedirectResponse(url=f"{frontend_url}/approval-success?action=approved&user={user_name_encoded}")
        else:
            await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "approval_status": "rejected"
                }}
            )
            
            # Send rejection notification to user
            await send_approval_notification(user, approved=False)
            
            # Redirect to success page (preserves owner's login state)
            from urllib.parse import quote
            user_name_encoded = quote(user['name'])
            return RedirectResponse(url=f"{frontend_url}/approval-success?action=rejected&user={user_name_encoded}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Approval error: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/login?error=unknown")

@api_router.post("/auth/approve-user-dashboard")
async def approve_user_from_dashboard(
    user_id: str = Query(...),
    action: str = Query(...),
    role: str = Query(None),
    current_user: User = Depends(require_owner)
):
    """
    Approve or reject user from owner dashboard - returns JSON response
    Can optionally assign a specific role during approval
    """
    try:
        if action not in ['approve', 'reject']:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if action == 'approve':
            update_data = {
                "approval_status": "approved",
                "is_validated": True
            }
            
            # If a specific role is provided, update it
            if role:
                update_data["role"] = role
                update_data["designation"] = role.replace('_', ' ').title()
            
            await db.users.update_one(
                {"id": user_id},
                {"$set": update_data}
            )
            
            # Update contractor/consultant record with the assigned type
            original_role = user.get('role', '')
            if role and original_role in ['contractor', 'civil_contractor', 'electrical_contractor', 'plumbing_contractor', 
                                          'furniture_contractor', 'hvac_contractor', 'painting_contractor', 'flooring_contractor',
                                          'structural_contractor', 'project_manager']:
                # Update contractor record with the specific type
                contractor_type = role.replace('_contractor', '').replace('_', ' ').title()
                if role == 'project_manager':
                    contractor_type = 'Project Manager'
                
                await db.contractors.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "contractor_type": contractor_type,
                        "notes": f"Approved as {contractor_type}"
                    }}
                )
                print(f"✅ Updated contractor type to '{contractor_type}' for {user['name']}")
                
            elif role and original_role in ['consultant', 'structural_consultant', 'mep_consultant', 'electrical_consultant',
                                             'plumbing_consultant', 'landscape_consultant', 'interior_consultant',
                                             'sustainability_consultant', 'fire_safety_consultant']:
                # Update consultant record with the specific type
                consultant_type = role.replace('_consultant', '').replace('_', ' ').title()
                
                await db.consultants.update_one(
                    {"user_id": user_id},
                    {"$set": {
                        "type": consultant_type,
                        "notes": f"Approved as {consultant_type} Consultant"
                    }}
                )
                print(f"✅ Updated consultant type to '{consultant_type}' for {user['name']}")
            
            # Send approval notification automatically
            try:
                from notification_triggers_v2 import notify_user_approval
                await notify_user_approval(user_id)
                print(f"✅ Approval notification sent to {user['name']}")
            except Exception as e:
                print(f"Approval notification failed (non-critical): {str(e)}")
            
            return {
                "success": True,
                "message": f"{user['name']} has been approved successfully",
                "user_role": role or user.get('role')
            }
        else:
            await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "approval_status": "rejected"
                }}
            )
            
            # Send rejection notification to user
            try:
                await send_approval_notification(user, approved=False)
            except Exception as e:
                print(f"Email notification failed (non-critical): {str(e)}")
            
            return {
                "success": True,
                "message": f"{user['name']}'s registration has been rejected"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Approval error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/auth/send-approval-notification")
async def send_approval_notification_endpoint(
    user_id: str = Query(...),
    current_user: User = Depends(require_owner)
):
    """
    Send approval notification to user after owner dismisses project creation prompt
    This separates approval from notification for better UX
    """
    try:
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user.get('approval_status') != 'approved':
            raise HTTPException(status_code=400, detail="User is not approved")
        
        # Send approval notification
        try:
            from notification_triggers_v2 import notify_user_approval
            await notify_user_approval(user_id)
            return {"success": True, "message": "Notification sent successfully"}
        except Exception as e:
            print(f"Approval notification failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Notification error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/auth/pending-registrations")
async def get_pending_registrations(current_user: User = Depends(require_owner)):
    """
    Get list of pending user registrations (Owner only)
    """
    try:
        pending_users = await db.users.find(
            {"approval_status": "pending"},
            {"_id": 0}
        ).to_list(1000)
        
        return pending_users
    except Exception as e:
        print(f"Error fetching pending registrations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

async def send_approval_notification(user: dict, approved: bool):
    """Send approval/rejection notification to user with role-specific welcome email"""
    try:
        login_url = os.getenv('REACT_APP_BACKEND_URL')
        
        if approved:
            # Use role-specific welcome email template
            subject, html_content = get_welcome_email_content(user, login_url)
        else:
            # Rejection email
            subject = "4th Dimension Registration Update"
            html_content = f"""
            <html>
                <head>
                    <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
                </head>
                <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                    <div style="max-width: 650px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #EF4444; font-size: 28px;">Registration Update</h1>
                        </div>
                        
                        <h2 style="color: #1F2937; font-size: 24px;">Dear {user['name']},</h2>
                        
                        <p style="font-size: 16px; line-height: 1.8;">Thank you for your interest in joining 4th Dimension.</p>
                        
                        <div style="background: #FEE2E2; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #EF4444;">
                            <p style="margin: 0; color: #991B1B;">After careful review, we regret to inform you that we are unable to approve your registration at this time.</p>
                        </div>
                        
                        <p style="font-size: 16px;">If you believe this is an error or have any questions, please contact us at <a href="mailto:contact@4thdimensionarchitect.com" style="color: #4F46E5;">contact@4thdimensionarchitect.com</a>.</p>
                        
                        <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                            <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                            <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=get_email_sender(),
            to_emails=user['email'],
            subject=subject,
            html_content=html_content
        )
        
        sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sendgrid_client.send(message)
        print(f"✅ {'Approval' if approved else 'Rejection'} notification sent to {user['email']}")
        
    except Exception as e:
        print(f"Failed to send approval notification: {str(e)}")

@api_router.get("/email-preview")
async def get_email_preview(user_id: str = Query(None), role: str = Query(...), lang: str = Query('en')):
    """
    Get email preview in different languages
    """
    try:
        from email_templates import get_translated_email_content
        
        # Create mock user data for preview
        mock_user = {
            'id': user_id or 'preview-user',
            'name': 'प्रिय उपयोगकर्ता' if lang == 'hi' else 'પ્રિય વપરાશકર્તા' if lang == 'gu' else 'Dear User',
            'email': 'user@example.com',
            'role': role,
            'registered_via': 'email',
            'preferred_language': lang
        }
        
        login_url = os.getenv('REACT_APP_BACKEND_URL', 'https://slim-api.preview.emergentagent.com')
        
        subject, html_content = get_translated_email_content(mock_user, login_url, lang)
        
        return {
            "subject": subject,
            "html_content": html_content
        }
    except Exception as e:
        print(f"Email preview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/auth/forgot-password")
async def forgot_password(request: ForgotPasswordRequest):
    """
    Send password reset email with token
    """
    try:
        # Check if user exists
        user = await db.users.find_one({"email": request.email}, {"_id": 0})
        
        if not user:
            # For security, don't reveal if email exists
            # Return success anyway
            return {"message": "If an account exists with this email, you will receive a password reset link."}
        
        # Generate secure reset token
        import secrets
        reset_token = secrets.token_urlsafe(32)
        
        # Store token with expiry (1 hour)
        from datetime import datetime, timezone, timedelta
        await db.password_resets.insert_one({
            "email": request.email,
            "token": reset_token,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
            "used": False
        })
        
        # Send password reset email
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        frontend_url = os.getenv('REACT_APP_BACKEND_URL')
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <html>
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            </head>
            <body style="font-family: 'Segoe UI', Arial, sans-serif; line-height: 1.8; color: #1F2937; background-color: #F9FAFB; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: white; padding: 40px; border-radius: 15px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                    
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #4F46E5; font-size: 28px; margin-bottom: 10px;">Password Reset Request</h1>
                        <p style="color: #6B7280; font-size: 14px;">4th Dimension - Architecture & Design</p>
                    </div>
                    
                    <h2 style="color: #1F2937; font-size: 20px;">Hello {user['name']},</h2>
                    
                    <p style="font-size: 16px; line-height: 1.8;">We received a request to reset your password for your 4th Dimension account.</p>
                    
                    <div style="background: #EEF2FF; padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #4F46E5;">
                        <p style="margin: 0; color: #3730A3; font-size: 14px;"><strong>🔒 Security Notice:</strong> If you didn't request this password reset, please ignore this email. Your password will remain unchanged.</p>
                    </div>
                    
                    <p style="font-size: 16px;">Click the button below to reset your password:</p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="display: inline-block; background: #4F46E5; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">
                            Reset My Password
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #6B7280;">Or copy and paste this link into your browser:</p>
                    <p style="font-size: 13px; color: #4F46E5; word-break: break-all; background: #F3F4F6; padding: 10px; border-radius: 6px;">
                        {reset_link}
                    </p>
                    
                    <div style="background: #FEF3C7; padding: 15px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; color: #92400E; font-size: 13px;"><strong>⏱️ Important:</strong> This link will expire in 1 hour for security reasons.</p>
                    </div>
                    
                    <p style="font-size: 14px; color: #6B7280; margin-top: 30px;">If you continue to have problems, please contact our support team.</p>
                    
                    <div style="margin-top: 40px; padding-top: 25px; border-top: 2px solid #E5E7EB; text-align: center; color: #6B7280; font-size: 13px;">
                        <p style="margin: 5px 0;"><strong style="color: #4F46E5;">4th Dimension - Architecture & Design</strong></p>
                        <p style="margin: 5px 0;">Building Dreams, Creating Realities</p>
                        <p style="margin: 15px 0 5px 0;">Need Help? <a href="mailto:support@4thdimension.com" style="color: #4F46E5;">support@4thdimension.com</a></p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        message = Mail(
            from_email=get_email_sender(),
            to_emails=request.email,
            subject='Reset Your 4th Dimension Password',
            html_content=html_content
        )
        
        sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sendgrid_client.send(message)
        
        print(f"✅ Password reset email sent to {request.email}")
        
        return {"message": "Password reset link has been sent to your email."}
        
    except Exception as e:
        print(f"Forgot password error: {str(e)}")
        # For security, still return success message
        return {"message": "If an account exists with this email, you will receive a password reset link."}

@api_router.get("/auth/validate-reset-token")
async def validate_reset_token(token: str = Query(...)):
    """
    Validate password reset token
    """
    try:
        from datetime import datetime, timezone
        
        # Find token
        reset_request = await db.password_resets.find_one({"token": token}, {"_id": 0})
        
        if not reset_request:
            raise HTTPException(status_code=400, detail="Invalid reset token")
        
        # Check if used
        if reset_request.get('used', False):
            raise HTTPException(status_code=400, detail="This reset link has already been used")
        
        # Check if expired
        expires_at = datetime.fromisoformat(reset_request['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Reset link has expired")
        
        return {"message": "Token is valid"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Token validation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate token")

@api_router.post("/auth/reset-password")
async def reset_password(request: ResetPasswordRequest):
    """
    Reset password using valid token
    """
    try:
        from datetime import datetime, timezone
        
        # Find and validate token
        reset_request = await db.password_resets.find_one({"token": request.token}, {"_id": 0})
        
        if not reset_request:
            raise HTTPException(status_code=400, detail="Invalid reset token")
        
        # Check if used
        if reset_request.get('used', False):
            raise HTTPException(status_code=400, detail="This reset link has already been used")
        
        # Check if expired
        expires_at = datetime.fromisoformat(reset_request['expires_at'])
        if datetime.now(timezone.utc) > expires_at:
            raise HTTPException(status_code=400, detail="Reset link has expired")
        
        # Validate new password
        if len(request.new_password) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        
        # Update user password
        new_password_hash = get_password_hash(request.new_password)
        
        result = await db.users.update_one(
            {"email": reset_request['email']},
            {"$set": {"password_hash": new_password_hash}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Mark token as used
        await db.password_resets.update_one(
            {"token": request.token},
            {"$set": {"used": True}}
        )
        
        print(f"✅ Password reset successfully for {reset_request['email']}")
        
        return {"message": "Password has been reset successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Reset password error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset password")

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error inviting team member: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to invite team member: {str(e)}")

@api_router.post("/team/verify-email")
async def verify_team_member_email(request: VerifyEmailRequest):
    """
    Verify team member email using token or OTP
    """
    try:
        query = {}
        if request.token:
            query["email_verification_token"] = request.token
        elif request.otp:
            query["email_otp"] = request.otp
        else:
            raise HTTPException(status_code=400, detail="Token or OTP required")
        
        verification = await db.team_verifications.find_one(query, {"_id": 0})
        
        if not verification:
            raise HTTPException(status_code=404, detail="Invalid verification token or OTP")
        
        # Check if already verified
        if verification.get('email_verified'):
            return {"message": "Email already verified", "user_id": verification['user_id']}
        
        # Check if expired
        if verification_service.is_otp_expired(verification['otp_created_at']):
            raise HTTPException(status_code=400, detail="Verification code expired")
        
        # Mark email as verified
        await db.team_verifications.update_one(
            {"id": verification['id']},
            {"$set": {
                "email_verified": True,
                "email_verified_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update user
        await db.users.update_one(
            {"id": verification['user_id']},
            {"$set": {"email_verified": True}}
        )
        
        return {
            "message": "Email verified successfully",
            "user_id": verification['user_id'],
            "phone_verified": verification.get('phone_verified', False)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying email: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify email")

@api_router.post("/team/verify-phone")
async def verify_team_member_phone(request: VerifyPhoneRequest):
    """
    Verify team member phone using OTP
    """
    try:
        verification = await db.team_verifications.find_one(
            {"user_id": request.user_id, "phone_otp": request.otp},
            {"_id": 0}
        )
        
        if not verification:
            raise HTTPException(status_code=404, detail="Invalid OTP")
        
        # Check if already verified
        if verification.get('phone_verified'):
            return {"message": "Phone already verified"}
        
        # Check if expired
        if verification_service.is_otp_expired(verification['otp_created_at']):
            raise HTTPException(status_code=400, detail="OTP expired")
        
        # Mark phone as verified
        await db.team_verifications.update_one(
            {"id": verification['id']},
            {"$set": {
                "phone_verified": True,
                "phone_verified_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        # Update user - mark as validated if both email and phone verified
        email_verified = verification.get('email_verified', False)
        if email_verified:
            await db.users.update_one(
                {"id": request.user_id},
                {"$set": {
                    "mobile_verified": True,
                    "is_validated": True,
                    "registration_completed": True
                }}
            )
        else:
            await db.users.update_one(
                {"id": request.user_id},
                {"$set": {"mobile_verified": True}}
            )
        
        return {
            "message": "Phone verified successfully",
            "fully_verified": email_verified,
            "can_login": email_verified
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error verifying phone: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify phone")

@api_router.post("/team/resend-otp")
async def resend_verification_otp(request: ResendOTPRequest):
    """
    Resend OTP for email or phone verification
    """
    try:
        verification = await db.team_verifications.find_one(
            {"user_id": request.user_id},
            {"_id": 0}
        )
        
        if not verification:
            raise HTTPException(status_code=404, detail="Verification record not found")
        
        # Generate new OTP
        new_otp = verification_service.generate_otp()
        
        # Update verification record
        update_data = {
            "otp_created_at": datetime.now(timezone.utc).isoformat(),
            "otp_attempts": verification.get('otp_attempts', 0) + 1
        }
        
        if request.type == "email":
            update_data["email_otp"] = new_otp
            
            # Send email
            user = await db.users.find_one({"id": request.user_id}, {"_id": 0})
            verification_link = f"{os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:3000')}/verify-email?token={verification['email_verification_token']}"
            
            success, error = await verification_service.send_verification_email(
                to_email=verification['email'],
                user_name=user['name'],
                verification_link=verification_link,
                otp=new_otp
            )
            
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to send email: {error}")
                
        elif request.type == "phone":
            update_data["phone_otp"] = new_otp
            
            # Send SMS
            success, error = await verification_service.send_verification_sms(
                phone_number=verification['phone'],
                otp=new_otp
            )
            
            if not success:
                raise HTTPException(status_code=500, detail=f"Failed to send SMS: {error}")
        else:
            raise HTTPException(status_code=400, detail="Invalid type. Must be 'email' or 'phone'")
        
        await db.team_verifications.update_one(
            {"id": verification['id']},
            {"$set": update_data}
        )
        
        return {"message": f"OTP resent successfully to {request.type}"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error resending OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resend OTP")


# ==================== PROFILE COMPLETION & OTP ====================

@api_router.post("/profile/request-otp")
async def request_verification_otp(mobile: str, email: str, current_user: User = Depends(get_current_user)):
    """Generate OTPs for mobile and email verification"""
    # Generate 6-digit OTPs
    mobile_otp = ''.join(random.choices(string.digits, k=6))
    email_otp = ''.join(random.choices(string.digits, k=6))
    
    # Store mobile OTP
    mobile_otp_doc = OTP(
        user_id=current_user.id,
        otp_code=mobile_otp,
        action=f"verify_mobile_{mobile}",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    mobile_dict = mobile_otp_doc.model_dump()
    mobile_dict['created_at'] = mobile_dict['created_at'].isoformat()
    mobile_dict['expires_at'] = mobile_dict['expires_at'].isoformat()
    await db.otps.insert_one(mobile_dict)
    
    # Store email OTP
    email_otp_doc = OTP(
        user_id=current_user.id,
        otp_code=email_otp,
        action=f"verify_email_{email}",
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10)
    )
    email_dict = email_otp_doc.model_dump()
    email_dict['created_at'] = email_dict['created_at'].isoformat()
    email_dict['expires_at'] = email_dict['expires_at'].isoformat()
    await db.otps.insert_one(email_dict)
    
    # In production, send via SMS and email
    return {
        "message": "OTPs sent successfully",
        "mobile_otp": mobile_otp,  # Remove in production
        "email_otp": email_otp,  # Remove in production
        "mobile": mobile,
        "email": email
    }

@api_router.post("/profile/complete")
async def complete_profile(
    profile: CompleteProfile,
    current_user: User = Depends(get_current_user)
):
    """Complete user profile and auto-validate"""
    
    # Update user profile directly
    dob = datetime.fromisoformat(profile.date_of_birth) if profile.date_of_birth else None
    doj = datetime.fromisoformat(profile.date_of_joining) if profile.date_of_joining else None
    
    await db.users.update_one(
        {"id": current_user.id},
        {"$set": {
            "name": profile.full_name,
            "address_line_1": profile.address_line_1,
            "address_line_2": profile.address_line_2,
            "landmark": profile.landmark,
            "city": profile.city,
            "state": profile.state,
            "pin_code": profile.pin_code,
            "email": profile.email,
            "mobile": profile.mobile,
            "date_of_birth": dob.isoformat() if dob else None,
            "date_of_joining": doj.isoformat() if doj else None,
            "gender": profile.gender,
            "marital_status": profile.marital_status,
            "role": profile.role,
            "mobile_verified": True,
            "email_verified": True,
            "registration_completed": True,
            "is_validated": True  # Auto-validate user
        }}
    )
    
    return {
        "message": "Profile completed successfully! You can now access the system.",
        "status": "validated"
    }



# ==================== USER ROUTES (Moved to routes/users.py) ====================


# ==================== CLIENT ROUTES (NEW ARCHFLOW) ====================

@api_router.post("/clients", response_model=NewClient)
async def create_client(client_data: NewClientCreate, current_user: User = Depends(get_current_user)):
    client = NewClient(
        name=client_data.name,
        contact_person=client_data.contact_person,
        phone=client_data.phone,
        email=client_data.email,
        address=client_data.address,
        notes=client_data.notes,
        archived=False,
        created_by_id=current_user.id,
        owner_team_id=None
    )
    
    client_dict = client.model_dump()
    client_dict['created_at'] = client_dict['created_at'].isoformat()
    client_dict['updated_at'] = client_dict['updated_at'].isoformat()
    
    await db.clients.insert_one(client_dict)
    return client

@api_router.get("/clients")
async def get_clients(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user)
):
    # By default, only show non-archived clients
    query = {"deleted_at": None}
    if not include_archived:
        query["archived"] = {"$ne": True}
    
    clients = await db.clients.find(query, {"_id": 0}).to_list(1000)
    
    # Filter out clients whose user accounts are not approved
    approved_clients = []
    for client in clients:
        # Check if client has a user_id and if that user is approved
        if client.get('user_id'):
            user = await db.users.find_one(
                {"id": client['user_id']}, 
                {"_id": 0, "approval_status": 1}
            )
            # Only include if user is approved
            if user and user.get('approval_status') == 'approved':
                if isinstance(client.get('created_at'), str):
                    client['created_at'] = datetime.fromisoformat(client['created_at'])
                if isinstance(client.get('updated_at'), str):
                    client['updated_at'] = datetime.fromisoformat(client['updated_at'])
                
                # Count projects for this client
                project_count = await db.projects.count_documents({"client_id": client["id"], "deleted_at": None})
                client['total_projects'] = project_count
                approved_clients.append(client)
        else:
            # Client created manually without user account (legacy) - always show
            if isinstance(client.get('created_at'), str):
                client['created_at'] = datetime.fromisoformat(client['created_at'])
            if isinstance(client.get('updated_at'), str):
                client['updated_at'] = datetime.fromisoformat(client['updated_at'])
            
            project_count = await db.projects.count_documents({"client_id": client["id"], "deleted_at": None})
            client['total_projects'] = project_count
            approved_clients.append(client)
    
    return approved_clients

@api_router.get("/clients/{client_id}")
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    # Try new clients collection first
    client = await db.clients.find_one({"id": client_id, "deleted_at": None}, {"_id": 0})
    
    # Fallback to users collection for backwards compatibility (old structure where clients were users)
    if not client:
        user = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
        if user:
            # Convert user format to client format
            client = {
                "id": user.get('id'),
                "name": user.get('name'),
                "email": user.get('email'),
                "phone": user.get('mobile'),
                "address": user.get('address', ''),
                "gst_number": None,
                "company_name": None,
                "contact_person_name": user.get('name'),
                "contact_person_email": user.get('email'),
                "contact_person_phone": user.get('mobile'),
                "notes": '',
                "created_at": user.get('created_at'),
                "updated_at": user.get('updated_at')
            }
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if isinstance(client.get('created_at'), str):
        client['created_at'] = datetime.fromisoformat(client['created_at'])
    if isinstance(client.get('updated_at'), str):
        client['updated_at'] = datetime.fromisoformat(client['updated_at'])
    
    # Get related projects
    projects = await db.projects.find({"client_id": client_id, "deleted_at": None}, {"_id": 0}).to_list(100)
    client['projects'] = projects
    
    return client

@api_router.put("/clients/{client_id}")
async def update_client(client_id: str, client_data: ClientUpdate, current_user: User = Depends(get_current_user)):
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "name": client_data.name,
            "contact_person": client_data.contact_person,
            "phone": client_data.phone,
            "email": client_data.email,
            "address": client_data.address,
            "notes": client_data.notes,
            "archived": client_data.archived,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Client updated successfully"}

@api_router.put("/clients/{client_id}/archive")
async def archive_client(client_id: str, archived: bool = True, current_user: User = Depends(get_current_user)):
    """Archive or unarchive a client"""
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {
            "archived": archived,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    action = "archived" if archived else "unarchived"
    return {"message": f"Client {action} successfully"}

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str, current_user: User = Depends(require_owner)):
    """Permanently delete client (HARD DELETE) - Only if no active projects exist"""
    # Check in both clients collection and users collection (legacy clients)
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    user_client = await db.users.find_one({"id": client_id, "role": "client"}, {"_id": 0})
    
    if not client and not user_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Check for active (non-deleted, non-archived) projects
    active_projects = await db.projects.find({
        "client_id": client_id,
        "deleted_at": None,  # Not deleted
        "$or": [
            {"archived": False},
            {"archived": {"$exists": False}}
        ]
    }, {"_id": 0, "title": 1, "code": 1}).to_list(10)
    
    if active_projects:
        project_names = ", ".join([p.get('code', 'Unnamed') for p in active_projects])
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete client. {len(active_projects)} active project(s) exist: {project_names}. Please archive or delete these projects first."
        )
    
    # Get client info for cleanup
    client_email = None
    client_phone = None
    client_user_id = None
    
    if client:
        client_email = client.get('email')
        client_phone = client.get('phone')
        client_user_id = client.get('user_id')
    if user_client:
        client_email = client_email or user_client.get('email')
        client_phone = client_phone or user_client.get('mobile')
    
    # HARD DELETE from clients collection
    if client:
        await db.clients.delete_one({"id": client_id})
        logger.info(f"Hard deleted client: {client.get('name')}")
    
    # Delete from users collection if exists (legacy clients stored as users)
    if user_client:
        await db.users.delete_one({"id": client_id})
        logger.info(f"Hard deleted legacy client from users: {user_client.get('name')}")
    
    # Also delete associated user account if stored separately
    if client_user_id:
        await db.users.delete_one({"id": client_user_id})
        logger.info(f"Hard deleted user account for client: {client.get('name')}")
    
    # Clean up related records to allow fresh re-registration
    if client_email:
        await db.pending_registrations.delete_many({"email": client_email})
        await db.invitations.delete_many({"email": client_email})
        await db.team_verifications.delete_many({"email": client_email})
    
    if client_phone:
        # Normalize phone for cleanup
        phone_digits = ''.join(filter(str.isdigit, client_phone))[-10:]
        await db.invitations.delete_many({"phone": {"$regex": phone_digits}})
        await db.pending_registrations.delete_many({"phone": {"$regex": phone_digits}})
    
    return {"message": "Client permanently deleted. They can now be invited fresh."}



# ==================== BRAND CATEGORY ROUTES ====================

@api_router.get("/brand-categories")
async def get_brand_categories(current_user: User = Depends(get_current_user)):
    """Get all brand categories"""
    categories = await db.brand_categories.find({}, {"_id": 0}).to_list(1000)
    return categories

@api_router.post("/brand-categories", response_model=BrandCategoryMaster)
async def create_brand_category(
    category_data: BrandCategoryMasterCreate, 
    current_user: User = Depends(require_owner)
):
    """Create a new brand category (owner only)"""
    category = BrandCategoryMaster(
        category_name=category_data.category_name,
        suggested_brands=category_data.suggested_brands
    )
    
    category_dict = category.model_dump()
    category_dict['created_at'] = category_dict['created_at'].isoformat()
    category_dict['updated_at'] = category_dict['updated_at'].isoformat()
    
    await db.brand_categories.insert_one(category_dict)
    return category

@api_router.put("/brand-categories/{category_id}")
async def update_brand_category(
    category_id: str,
    category_data: BrandCategoryMasterUpdate,
    current_user: User = Depends(require_owner)
):
    """Update a brand category (owner only)"""
    update_data = {k: v for k, v in category_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.brand_categories.update_one(
        {"id": category_id},
        {"$set": update_data}
    )
    return {"message": "Brand category updated successfully"}

@api_router.delete("/brand-categories/{category_id}")
async def delete_brand_category(
    category_id: str,
    current_user: User = Depends(require_owner)
):
    """Delete a brand category (owner only)"""
    await db.brand_categories.delete_one({"id": category_id})
    return {"message": "Brand category deleted successfully"}


# ==================== CONTACT TYPE ROUTES ====================

@api_router.get("/contact-types")
async def get_contact_types(current_user: User = Depends(get_current_user)):
    """Get all contact types"""
    types = await db.contact_types.find({}, {"_id": 0}).to_list(1000)
    return types

@api_router.post("/contact-types", response_model=ContactTypeMaster)
async def create_contact_type(
    type_data: ContactTypeMasterCreate, 
    current_user: User = Depends(get_current_user)
):
    """Create a new contact type"""
    contact_type = ContactTypeMaster(
        type_name=type_data.type_name
    )
    
    type_dict = contact_type.model_dump()
    type_dict['created_at'] = type_dict['created_at'].isoformat()
    type_dict['updated_at'] = type_dict['updated_at'].isoformat()
    
    await db.contact_types.insert_one(type_dict)
    return contact_type

@api_router.put("/contact-types/{type_id}")
async def update_contact_type(
    type_id: str,
    type_data: ContactTypeMasterUpdate,
    current_user: User = Depends(require_owner)
):
    """Update a contact type (owner only)"""
    update_data = {k: v for k, v in type_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.contact_types.update_one(
        {"id": type_id},
        {"$set": update_data}
    )
    return {"message": "Contact type updated successfully"}

@api_router.delete("/contact-types/{type_id}")
async def delete_contact_type(
    type_id: str,
    current_user: User = Depends(require_owner)
):
    """Delete a contact type (owner only)"""
    await db.contact_types.delete_one({"id": type_id})
    return {"message": "Contact type deleted successfully"}


# ==================== PROJECT ROUTES ====================

@api_router.post("/projects", response_model=NewProject)
async def create_project(project_data: NewProjectCreate, current_user: User = Depends(get_current_user)):
    """Create a new project with comprehensive details"""
    # Auto-archive if end_date is provided
    archived = False
    if project_data.end_date:
        archived = True
    
    project = NewProject(
        code=project_data.code,
        title=project_data.title,
        project_types=project_data.project_types,
        status=project_data.status,
        client_id=project_data.client_id,
        team_leader_id=project_data.team_leader_id,
        lead_architect_id=project_data.lead_architect_id,
        project_manager_id=project_data.project_manager_id,
        start_date=datetime.fromisoformat(project_data.start_date) if project_data.start_date else None,
        end_date=datetime.fromisoformat(project_data.end_date) if project_data.end_date else None,
        archived=archived,
        site_address=project_data.site_address,
        notes=project_data.notes,
        civil_contractor=project_data.civil_contractor,
        structural_consultant=project_data.structural_consultant,
        tile_marble_contractor=project_data.tile_marble_contractor,
        furniture_contractor=project_data.furniture_contractor,
        electrical_contractor=project_data.electrical_contractor,
        electrical_consultant=project_data.electrical_consultant,
        plumbing_consultant=project_data.plumbing_consultant,
        plumbing_contractor=project_data.plumbing_contractor,
        false_ceiling_contractor=project_data.false_ceiling_contractor,
        furniture_material_supplier=project_data.furniture_material_supplier,
        kitchen_contractor=project_data.kitchen_contractor,
        modular_contractor=project_data.modular_contractor,
        color_contractor=project_data.color_contractor,
        landscape_consultant=project_data.landscape_consultant,
        landscape_contractor=project_data.landscape_contractor,
        automation_consultant=project_data.automation_consultant,
        readymade_furniture_supplier=project_data.readymade_furniture_supplier,
        lights_supplier=project_data.lights_supplier,
        custom_contacts=project_data.custom_contacts,
        brands=project_data.brands,
        assigned_contractors=project_data.assigned_contractors,
        created_by_id=current_user.id
    )
    
    project_dict = project.model_dump()
    # Convert datetimes to ISO strings
    for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
        if project_dict.get(field):
            project_dict[field] = project_dict[field].isoformat() if isinstance(project_dict[field], datetime) else project_dict[field]
    
    await db.projects.insert_one(project_dict)
    
    # Auto-create ONLY first 3 drawings from template lists for each project type
    # Using progressive disclosure: 1 DUE + 2 UPCOMING initially
    
    base_date = project.start_date if project.start_date else datetime.now(timezone.utc)
    
    # Create drawings for each selected project type using templates
    for project_type in project.project_types:
        # Get template drawings for this category
        template_drawings = get_template_drawings(project_type)
        
        if not template_drawings:
            logger.warning(f"No template drawings found for project type: {project_type}")
            continue
        
        # Create ONLY first 3 drawings from template
        for i in range(min(3, len(template_drawings))):
            drawing_name = template_drawings[i]
            sequence_num = i + 1
            
            # Calculate due date
            # Drawing #1: project creation + 3 days (DUE)
            # Drawing #2 & #3: No due date yet (UPCOMING)
            if sequence_num == 1:
                due_date = base_date + timedelta(days=3)
            else:
                due_date = None  # Will be set when previous drawing is issued
            
            drawing = ProjectDrawing(
                project_id=project.id,
                category=project_type,
                name=drawing_name,
                status=DrawingStatus.PLANNED,
                due_date=due_date,
                is_issued=False,
                revision_count=0,
                sequence_number=sequence_num,
                is_active=True if sequence_num == 1 else False,  # Only first drawing is active
                assigned_to=project.team_leader_id or project.lead_architect_id,
                priority="high" if sequence_num == 1 else "medium"
            )
            drawing_dict = drawing.model_dump()
            
            # Convert datetimes to ISO strings
            for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                if drawing_dict.get(field):
                    drawing_dict[field] = drawing_dict[field].isoformat() if isinstance(drawing_dict[field], datetime) else drawing_dict[field]
            
            await db.project_drawings.insert_one(drawing_dict)
            
            logger.info(f"Created drawing #{sequence_num}: {drawing_name} for project {project.id}")
    
    # Send project creation notifications (AFTER drawings are created)
    try:
        from notification_triggers_v2 import notify_project_creation
        await notify_project_creation(project.id)
    except Exception as e:
        logger.error(f"Error sending project creation notification: {str(e)}")
    
    # Send WhatsApp notifications to all project stakeholders about onboarding
    try:
        from notification_triggers import notify_project_onboarding
        await notify_project_onboarding(project.id, current_user.id)
    except Exception as e:
        logger.warning(f"Failed to send project onboarding notifications: {e}")
    
    # Notify owner and team leader about first drawing due date
    try:
        from notification_triggers import notify_drawing_due_soon
        if project.lead_architect_id and project.lead_architect_id != current_user.id:
            # Get the first drawing name for notification
            first_drawing_name = "First Drawing"
            if project.project_types:
                first_type = project.project_types[0]
                if first_type in project_type_drawings:
                    first_drawing_name = project_type_drawings[first_type][0]["name"]
            
            await notify_drawing_due_soon(project.id, first_drawing_name, due_date=base_date + timedelta(days=3))
    except Exception as e:
        logger.warning(f"Failed to send drawing due date notification: {e}")
    
    # Auto-generate drawings from presets if preset_id provided (legacy support)
    if project_data.checklist_preset_id:
        preset = await db.checklist_presets.find_one({"id": project_data.checklist_preset_id}, {"_id": 0})
        if preset:
            for item in preset.get('items', []):
                drawing = ProjectDrawing(
                    project_id=project.id,
                    category=item['category'],
                    name=item['name'],
                    status=DrawingStatus.PLANNED,
                    due_date=datetime.now(timezone.utc) if not project.start_date else project.start_date,
                    is_issued=False,
                    revision_count=0
                )
                drawing_dict = drawing.model_dump()
                for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                    if drawing_dict.get(field):
                        drawing_dict[field] = drawing_dict[field].isoformat() if isinstance(drawing_dict[field], datetime) else drawing_dict[field]
                await db.project_drawings.insert_one(drawing_dict)
    
    return project

@api_router.get("/projects")
async def get_projects(
    include_archived: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get projects based on user role with proper access control"""
    query = {"deleted_at": None}
    if not include_archived:
        query["archived"] = {"$ne": True}
    
    # Role-based filtering
    if current_user.is_owner:
        # Owner sees all projects
        pass
    elif current_user.role == "client":
        # Clients see ONLY projects where they are the client
        client = await db.clients.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        if client:
            # Also check co-clients
            co_client_projects = await db.project_co_clients.find(
                {"client_id": client["id"]},
                {"_id": 0, "project_id": 1}
            ).to_list(100)
            co_client_project_ids = [p["project_id"] for p in co_client_projects]
            
            query["$or"] = [
                {"client_id": client["id"]},
                {"id": {"$in": co_client_project_ids}}
            ]
        else:
            # Also check if user_id matches
            query["$or"] = [
                {"client_id": current_user.id},
                {"user_id": current_user.id}
            ]
    elif current_user.role in ["contractor", "consultant"]:
        # Contractors/Consultants see ONLY projects where they're assigned
        contractor = await db.contractors.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        if not contractor:
            contractor = await db.consultants.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        
        if contractor:
            contractor_id = contractor["id"]
            # Need to find projects where this contractor is in assigned_contractors or assigned_consultants
            all_projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
            filtered_projects = []
            
            for project in all_projects:
                assigned_contractors = project.get('assigned_contractors', {})
                assigned_consultants = project.get('assigned_consultants', {})
                
                # Check if contractor is assigned
                is_assigned = False
                if isinstance(assigned_contractors, dict) and contractor_id in assigned_contractors.values():
                    is_assigned = True
                elif isinstance(assigned_consultants, dict) and contractor_id in assigned_consultants.values():
                    is_assigned = True
                
                if is_assigned:
                    # Convert date fields
                    for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
                        if isinstance(project.get(field), str) and project.get(field):
                            try:
                                project[field] = datetime.fromisoformat(project[field])
                            except ValueError:
                                pass
                    filtered_projects.append(project)
            
            return filtered_projects
        else:
            return []
    else:
        # All other roles (team_member, senior_architect, junior_architect, 
        # senior_interior_designer, junior_interior_designer, landscape_designer,
        # 3d_visualizer, site_engineer, site_supervisor, intern, etc.)
        # These are internal team members who can be assigned as team leaders
        
        # Define internal team member roles (not client, contractor, consultant, vendor)
        internal_roles = [
            'team_member', 'team_leader', 'owner',
            'senior_architect', 'junior_architect', 
            'senior_interior_designer', 'junior_interior_designer',
            'associate_architect', 'associate_interior_designer',
            'landscape_designer', '3d_visualizer',
            'site_engineer', 'site_supervisor', 'intern',
            'administrator', 'human_resource', 'accountant', 'office_staff'
        ]
        
        if current_user.role in internal_roles or current_user.role not in ['client', 'contractor', 'consultant', 'vendor']:
            # Internal team members see projects they lead OR have temporary access to
            team_access_projects = await db.project_team_access.find({
                "user_id": current_user.id,
                "$or": [
                    {"expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}},
                    {"expires_at": None}
                ]
            }, {"_id": 0, "project_id": 1}).to_list(100)
            
            access_project_ids = [p["project_id"] for p in team_access_projects]
            
            if access_project_ids:
                query["$or"] = [
                    {"team_leader_id": current_user.id},
                    {"id": {"$in": access_project_ids}}
                ]
            else:
                query["team_leader_id"] = current_user.id
    
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    for project in projects:
        # Convert ISO strings to datetime for proper serialization
        for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
            if isinstance(project.get(field), str) and project.get(field):
                try:
                    project[field] = datetime.fromisoformat(project[field])
                except ValueError:
                    pass
        
        # Auto-fix legacy status values
        if project.get('status') not in ['Lead', 'Concept', 'Layout_Dev', 'Elevation_3D', 'Structural_Coord', 'Working_Drawings', 'Execution', 'OnHold', 'Closed']:
            project['status'] = 'Lead'
            # Update in database
            await db.projects.update_one(
                {"id": project['id']},
                {"$set": {"status": "Lead"}}
            )
        
        # Populate team leader info
        if project.get('team_leader_id'):
            team_leader = await db.users.find_one(
                {"id": project['team_leader_id']},
                {"_id": 0, "id": 1, "name": 1, "email": 1, "mobile": 1, "role": 1}
            )
            if team_leader:
                project['team_leader_name'] = team_leader.get('name')
                project['team_leader_email'] = team_leader.get('email')
                project['team_leader_phone'] = team_leader.get('mobile')
                project['team_leader_role'] = team_leader.get('role')
    
    return projects

@api_router.get("/users/{user_id}/projects")
async def get_user_projects(user_id: str, current_user: User = Depends(get_current_user)):
    """Get projects assigned to a specific team member as team leader"""
    # Only owner can view other users' projects
    if not current_user.is_owner and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to view this user's projects")
    
    query = {"team_leader_id": user_id, "deleted_at": None}
    projects = await db.projects.find(query, {"_id": 0}).to_list(100)
    
    for project in projects:
        # Convert ISO strings to datetime
        for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
            if isinstance(project.get(field), str) and project.get(field):
                try:
                    project[field] = datetime.fromisoformat(project[field])
                except ValueError:
                    project[field] = None
        
        # Get drawings count for each project
        drawings_count = await db.project_drawings.count_documents({
            "project_id": project['id'], 
            "deleted_at": None
        })
        project['drawings_count'] = drawings_count
        
        # Get pending drawings count
        pending_count = await db.project_drawings.count_documents({
            "project_id": project['id'],
            "deleted_at": None,
            "$or": [
                {"is_issued": {"$ne": True}},
                {"has_pending_revision": True}
            ]
        })
        project['pending_drawings_count'] = pending_count
        
        # Populate team leader info
        if project.get('team_leader_id'):
            team_leader = await db.users.find_one(
                {"id": project['team_leader_id']},
                {"_id": 0, "id": 1, "name": 1, "email": 1, "mobile": 1, "role": 1}
            )
            if team_leader:
                project['team_leader_name'] = team_leader.get('name')
                project['team_leader_email'] = team_leader.get('email')
                project['team_leader_phone'] = team_leader.get('mobile')
                project['team_leader_role'] = team_leader.get('role')
    
    return projects

@api_router.get("/projects/{project_id}")
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    """Get project details"""
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Convert ISO strings to datetime
    for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
        if isinstance(project.get(field), str) and project.get(field):
            try:
                project[field] = datetime.fromisoformat(project[field])
            except ValueError:
                project[field] = None
        elif project.get(field) == '':
            project[field] = None
    
    # Auto-fix legacy status values
    if project.get('status') not in ['Lead', 'Concept', 'Layout_Dev', 'Elevation_3D', 'Structural_Coord', 'Working_Drawings', 'Execution', 'OnHold', 'Closed']:
        project['status'] = 'Lead'
        # Update in database
        await db.projects.update_one(
            {"id": project['id']},
            {"$set": {"status": "Lead"}}
        )
    
    # Get project drawings count
    drawings_count = await db.project_drawings.count_documents({"project_id": project_id, "deleted_at": None})
    project['drawings_count'] = drawings_count
    
    # Populate team leader info
    if project.get('team_leader_id'):
        team_leader = await db.users.find_one(
            {"id": project['team_leader_id']},
            {"_id": 0, "id": 1, "name": 1, "email": 1, "mobile": 1, "role": 1}
        )
        if team_leader:
            project['team_leader_name'] = team_leader.get('name')
            project['team_leader_email'] = team_leader.get('email')
            project['team_leader_phone'] = team_leader.get('mobile')
            project['team_leader_role'] = team_leader.get('role')
    
    return project

@api_router.put("/projects/{project_id}")
async def update_project(
    project_id: str, 
    project_data: NewProjectUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update project details"""
    # Get existing project to check for new contractors/consultants
    existing_project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    update_dict = {k: v for k, v in project_data.model_dump().items() if v is not None}
    
    # Auto-archive if end_date is being set
    if update_dict.get('end_date'):
        update_dict['archived'] = True
        if isinstance(update_dict['end_date'], str):
            update_dict['end_date'] = datetime.fromisoformat(update_dict['end_date']).isoformat()
    
    # Convert start_date if provided
    if update_dict.get('start_date') and isinstance(update_dict['start_date'], str):
        update_dict['start_date'] = datetime.fromisoformat(update_dict['start_date']).isoformat()
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.projects.update_one(
        {"id": project_id},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if contractors or consultants were added and send notifications
    try:
        from notification_triggers_v2 import notify_contractor_consultant_added
        
        # Check assigned_contractors
        if update_dict.get('assigned_contractors'):
            existing_contractors = existing_project.get('assigned_contractors', {})
            new_contractors = update_dict['assigned_contractors']
            
            # Find newly added contractors
            for contractor_type, contractor_id in new_contractors.items():
                if contractor_id and contractor_id != existing_contractors.get(contractor_type):
                    # New contractor added
                    await notify_contractor_consultant_added(
                        project_id=project_id,
                        person_id=contractor_id,
                        person_type='contractor'
                    )
        
        # Check for consultants (structural_consultant, etc.)
        consultant_fields = ['structural_consultant', 'electrical_consultant', 'plumbing_consultant', 
                            'landscape_consultant', 'mep_consultant']
        
        for field in consultant_fields:
            if update_dict.get(field):
                new_consultant = update_dict[field]
                existing_consultant = existing_project.get(field)
                
                # If consultant has an id field and it's new
                if isinstance(new_consultant, dict) and new_consultant.get('id'):
                    consultant_id = new_consultant['id']
                    existing_id = existing_consultant.get('id') if isinstance(existing_consultant, dict) else None
                    
                    if consultant_id != existing_id:
                        await notify_contractor_consultant_added(
                            project_id=project_id,
                            person_id=consultant_id,
                            person_type='consultant'
                        )
    except Exception as e:
        logger.error(f"Error sending contractor/consultant notification: {str(e)}")
    
    return {"message": "Project updated successfully"}

@api_router.post("/projects/{project_id}/request-deletion-otp")
async def request_project_deletion_otp(
    project_id: str,
    current_user: User = Depends(require_owner)
):
    """Request OTP for project deletion (owner only)"""
    try:
        # Verify project exists
        project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate OTP
        from verification_service import generate_otp
        otp = generate_otp(6)
        
        # Store OTP in database with 10-minute expiry
        otp_record = {
            "otp": otp,
            "user_id": current_user.id,
            "project_id": project_id,
            "action": "delete_project",
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=10),
            "verified": False
        }
        await db.otp_verifications.insert_one(otp_record)
        
        # Send OTP via email
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #DC2626; margin-bottom: 10px;">⚠️ Project Deletion Request</h1>
                    </div>
                    
                    <div style="background: #FEE2E2; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #DC2626;">
                        <h2 style="color: #991B1B; margin-top: 0;">Security Verification Required</h2>
                        <p style="font-size: 16px;">
                            You have requested to delete the following project:
                        </p>
                        <div style="background: white; padding: 15px; border-radius: 5px; margin: 15px 0;">
                            <strong>{project.get('code', 'N/A')}</strong> - {project.get('title', 'Untitled')}
                        </div>
                    </div>
                    
                    <div style="background: #F3F4F6; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px;">
                        <p style="font-size: 14px; color: #666; margin-bottom: 10px;">Your One-Time Password (OTP):</p>
                        <div style="font-size: 32px; font-weight: bold; letter-spacing: 8px; color: #DC2626; background: white; padding: 15px; border-radius: 8px; border: 2px dashed #DC2626;">
                            {otp}
                        </div>
                        <p style="font-size: 12px; color: #666; margin-top: 10px;">This OTP will expire in 10 minutes</p>
                    </div>
                    
                    <div style="background: #FEF3C7; padding: 15px; border-radius: 8px; border-left: 4px solid #F59E0B;">
                        <p style="margin: 0; font-size: 14px; color: #92400E;">
                            <strong>⚠️ Warning:</strong> Deleting this project is a permanent action. All associated drawings, comments, and data will be removed.
                        </p>
                    </div>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center;">
                        <p style="font-size: 12px; color: #666;">
                            If you did not request this action, please ignore this email or contact support immediately.
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=get_email_sender(),
            to_emails=current_user.email,
            subject='🚨 Project Deletion - OTP Verification Required',
            html_content=html_content
        )
        
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sg.send(message)
        
        return {"message": "OTP sent to your email", "expires_in": 600}
    
    except Exception as e:
        logger.error(f"Request deletion OTP error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_owner)
):
    """Soft delete project - OTP verification temporarily suspended (owner only)"""
    try:
        # OTP VERIFICATION TEMPORARILY SUSPENDED
        # Original OTP verification code commented out:
        # otp_record = await db.otp_verifications.find_one({
        #     "otp": otp,
        #     "user_id": current_user.id,
        #     "project_id": project_id,
        #     "action": "delete_project",
        #     "verified": False
        # }, {"_id": 0})
        # 
        # if not otp_record:
        #     raise HTTPException(status_code=400, detail="Invalid OTP")
        # 
        # # Check if OTP expired
        # expires_at = otp_record['expires_at']
        # if isinstance(expires_at, str):
        #     expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        # 
        # # Ensure timezone awareness
        # if expires_at.tzinfo is None:
        #     expires_at = expires_at.replace(tzinfo=timezone.utc)
        # 
        # if expires_at < datetime.now(timezone.utc):
        #     raise HTTPException(status_code=400, detail="OTP has expired. Please request a new one.")
        # 
        # # Mark OTP as verified
        # await db.otp_verifications.update_one(
        #     {"otp": otp, "user_id": current_user.id},
        #     {"$set": {"verified": True}}
        # )
        
        # Soft delete project
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": "Project deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete project error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== DRAWING ROUTES ====================

@api_router.get("/projects/{project_id}/drawings")
async def get_project_drawings(
    project_id: str, 
    active_only: bool = False,
    current_user: User = Depends(get_current_user)
):
    """Get all drawings for a project, optionally filter to active only"""
    query = {"project_id": project_id, "deleted_at": None}
    
    # If active_only is True, only return active drawings in the sequence
    if active_only:
        query["is_active"] = True
    
    drawings = await db.project_drawings.find(
        query, 
        {"_id": 0}
    ).to_list(1000)
    
    # Sort by sequence_number if available, otherwise by created_at
    drawings.sort(key=lambda x: (x.get('sequence_number') or 999999, x.get('created_at', '')))
    
    for drawing in drawings:
        if isinstance(drawing.get('created_at'), str):
            drawing['created_at'] = datetime.fromisoformat(drawing['created_at'])
        if drawing.get('issue_date') and isinstance(drawing['issue_date'], str):
            drawing['issue_date'] = datetime.fromisoformat(drawing['issue_date'])
    return drawings


@api_router.post("/projects/{project_id}/drawings")
async def create_drawing(
    project_id: str,
    drawing_data: ProjectDrawingCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new drawing for a project"""
    from models_projects import ProjectDrawing
    
    drawing = ProjectDrawing(
        project_id=project_id,
        category=drawing_data.category,
        name=drawing_data.name,
        due_date=datetime.fromisoformat(drawing_data.due_date) if drawing_data.due_date else None,
        notes=drawing_data.notes
    )
    
    drawing_dict = drawing.model_dump()
    for field in ['created_at', 'updated_at', 'issued_date', 'due_date']:
        if drawing_dict.get(field):
            drawing_dict[field] = drawing_dict[field].isoformat() if isinstance(drawing_dict[field], datetime) else drawing_dict[field]
    
    await db.project_drawings.insert_one(drawing_dict)
    
    # Return without _id
    return {k: v for k, v in drawing_dict.items() if k != '_id'}

@api_router.put("/drawings/{drawing_id}")
async def update_drawing(
    drawing_id: str,
    drawing_data: ProjectDrawingUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a drawing"""
    update_dict = {k: v for k, v in drawing_data.model_dump().items() if v is not None}
    
    # Get current drawing state
    drawing = await db.project_drawings.find_one({"id": drawing_id})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # If marking under_review (upload complete, ready for review)
    if update_dict.get('under_review') == True:
        update_dict['reviewed_date'] = datetime.now(timezone.utc).isoformat()
        update_dict['is_approved'] = False  # Reset approval when new file uploaded
    
    # If marking as approved
    if update_dict.get('is_approved') == True:
        update_dict['approved_date'] = datetime.now(timezone.utc).isoformat()
    
    # If marking as issued, set issued_date
    if update_dict.get('is_issued') == True:
        update_dict['issued_date'] = datetime.now(timezone.utc).isoformat()
    
    # REMOVED: Un-issue feature disabled - drawings cannot be un-issued once issued
    # If someone tries to un-issue, we simply ignore this update
    if update_dict.get('is_issued') == False and drawing.get('is_issued') == True:
        # Block un-issuing - remove is_issued from update dict
        del update_dict['is_issued']
        logger.info(f"Un-issue attempt blocked for drawing {drawing_id}")
    
    # If marking has_pending_revision as True (requesting revision)
    if update_dict.get('has_pending_revision') == True:
        update_dict['is_issued'] = False
        update_dict['current_revision_notes'] = update_dict.pop('revision_notes', None)
        
        # Handle revision due date
        if update_dict.get('revision_due_date'):
            update_dict['current_revision_due_date'] = datetime.fromisoformat(update_dict.pop('revision_due_date')).isoformat()
        
        # Update the current revision history item if drawing was issued
        if drawing.get('issued_date'):
            revision_history = drawing.get('revision_history', [])
            
            # Create or update the latest history item
            if revision_history and not revision_history[-1].get('resolved_date'):
                # Update existing pending revision
                revision_history[-1]['revision_requested_date'] = datetime.now(timezone.utc).isoformat()
                revision_history[-1]['revision_notes'] = update_dict.get('current_revision_notes')
                revision_history[-1]['revision_due_date'] = update_dict.get('current_revision_due_date')
            else:
                # Create new revision history item
                new_history = {
                    'issued_date': drawing.get('issued_date'),
                    'revision_requested_date': datetime.now(timezone.utc).isoformat(),
                    'revision_notes': update_dict.get('current_revision_notes'),
                    'revision_due_date': update_dict.get('current_revision_due_date'),
                    'resolved_date': None
                }
                revision_history.append(new_history)
            
            update_dict['revision_history'] = revision_history
    
    # If resolving revision
    if update_dict.get('has_pending_revision') == False and drawing.get('has_pending_revision') == True:
        update_dict['current_revision_notes'] = None
        update_dict['current_revision_due_date'] = None
        update_dict['revision_count'] = drawing.get('revision_count', 0) + 1
        
        # Update revision history
        revision_history = drawing.get('revision_history', [])
        if revision_history and not revision_history[-1].get('resolved_date'):
            revision_history[-1]['resolved_date'] = datetime.now(timezone.utc).isoformat()
            update_dict['revision_history'] = revision_history
    
    # If drawing is being issued, activate next drawing and create new one
    if update_dict.get('is_issued') == True and drawing.get('is_issued') == False:
        issue_date = datetime.now(timezone.utc)
        update_dict['issued_date'] = issue_date.isoformat()
        
        current_sequence = drawing.get('sequence_number')
        project_id = drawing.get('project_id')
        category = drawing.get('category')
        
        if current_sequence and project_id and category:
            # 1. Find next drawing in sequence (current + 1)
            next_sequence = current_sequence + 1
            next_drawing = await db.project_drawings.find_one({
                "project_id": project_id,
                "category": category,
                "sequence_number": next_sequence,
                "deleted_at": None
            }, {"_id": 0})
            
            if next_drawing:
                # Set the next drawing as DUE with due_date = issue_date + 3 days
                await db.project_drawings.update_one(
                    {"id": next_drawing['id']},
                    {"$set": {
                        "is_active": True,
                        "due_date": (issue_date + timedelta(days=3)).isoformat(),
                        "updated_at": issue_date.isoformat()
                    }}
                )
                logger.info(f"Activated drawing #{next_sequence} as DUE")
            
            # 2. Auto-create the 4th drawing ahead (current + 3)
            # This maintains: 1 DUE + 2 UPCOMING
            fourth_sequence = current_sequence + 3
            
            # Check if this drawing already exists
            existing_fourth = await db.project_drawings.find_one({
                "project_id": project_id,
                "category": category,
                "sequence_number": fourth_sequence,
                "deleted_at": None
            }, {"_id": 0})
            
            if not existing_fourth:
                # Get template drawings for this category
                template_drawings = get_template_drawings(category)
                
                # Check if template has this drawing
                if template_drawings and fourth_sequence <= len(template_drawings):
                    drawing_name = template_drawings[fourth_sequence - 1]  # 0-indexed
                    
                    # Create the new drawing
                    new_drawing = ProjectDrawing(
                        project_id=project_id,
                        category=category,
                        name=drawing_name,
                        status=DrawingStatus.PLANNED,
                        due_date=None,  # Will be set when it becomes due
                        is_issued=False,
                        revision_count=0,
                        sequence_number=fourth_sequence,
                        is_active=False,  # UPCOMING, not active yet
                        assigned_to=drawing.get('assigned_to'),
                        priority="medium"
                    )
                    new_drawing_dict = new_drawing.model_dump()
                    
                    # Convert datetimes to ISO strings
                    for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                        if new_drawing_dict.get(field):
                            new_drawing_dict[field] = new_drawing_dict[field].isoformat() if isinstance(new_drawing_dict[field], datetime) else new_drawing_dict[field]
                    
                    await db.project_drawings.insert_one(new_drawing_dict)
                    logger.info(f"Auto-created drawing #{fourth_sequence}: {drawing_name} as UPCOMING")
    
    # Update the drawing
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": update_dict}
    )
    
    # Fetch and return updated drawing
    updated_drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    
    # Send owner notifications for drawing events (non-blocking)
    try:
        from notification_triggers_v2 import (
            notify_owner_drawing_issued,
            notify_owner_drawing_revision_posted
        )
        from drawing_approval_reminders import send_immediate_approval_notification
        
        project_id = drawing.get('project_id')
        drawing_name = drawing.get('name', 'Drawing')
        
        # Notification 1: Drawing uploaded for review - Send IMMEDIATE approval notification
        if update_dict.get('under_review') == True and not drawing.get('under_review'):
            # Send immediate notification with deep link and reminder warning
            await send_immediate_approval_notification(
                drawing_id=drawing_id,
                drawing_name=drawing_name,
                project_id=project_id,
                uploaded_by_name=current_user.name
            )
        
        # Notification 2: Drawing issued
        if update_dict.get('is_issued') == True and not drawing.get('is_issued'):
            await notify_owner_drawing_issued(
                drawing_id=drawing_id,
                drawing_name=drawing_name,
                project_id=project_id,
                issued_by_name=current_user.name,
                revision_number=drawing.get('revision_count', 0)
            )
        
        # Notification 3: Revision posted (has_pending_revision cleared after upload)
        if update_dict.get('has_pending_revision') == False and drawing.get('has_pending_revision') == True:
            await notify_owner_drawing_revision_posted(
                drawing_id=drawing_id,
                drawing_name=drawing_name,
                project_id=project_id,
                posted_by_name=current_user.name,
                revision_number=updated_drawing.get('revision_count', 1)
            )
    except Exception as e:
        logger.warning(f"Drawing notification failed (non-critical): {str(e)}")
    
    # Convert ISO strings to datetime for serialization
    for field in ['created_at', 'updated_at', 'due_date', 'issued_date', 'current_revision_due_date']:
        if isinstance(updated_drawing.get(field), str) and updated_drawing.get(field):
            try:
                updated_drawing[field] = datetime.fromisoformat(updated_drawing[field])
            except ValueError:
                updated_drawing[field] = None
    
    return updated_drawing


# ==================== FILE UPLOAD ROUTES ====================

@api_router.post("/drawings/upload")
async def upload_drawing_file(
    files: List[UploadFile] = File(...),
    drawing_id: str = Form(...),
    upload_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple PDF files for drawing"""
    uploaded_files = []
    
    for file in files:
        # Validate file type - expanded to support architectural files
        allowed_extensions = ['.pdf', '.dwg', '.dxf', '.dwf', '.dgn']
        file_extension = Path(file.filename).suffix.lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File {file.filename}: Only PDF and CAD files (.dwg, .dxf, .dwf, .dgn) are allowed for drawings")
        
        # Check file size (50MB limit)
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail=f"File {file.filename}: File size exceeds maximum")
        
        # Create uploads directory
        upload_dir = Path("uploads/drawings")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        file_extension = Path(file.filename).suffix
        unique_filename = f"{drawing_id}_{upload_type}_{timestamp}_{len(uploaded_files)}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            buffer.write(content)
        
        # Return file URL
        file_url = f"/uploads/drawings/{unique_filename}"
        uploaded_files.append({
            "url": file_url,
            "filename": file.filename,
            "original_name": file.filename,
            "size": len(content)
        })
    
    return {
        "uploaded_files": uploaded_files,
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)"
    }

@api_router.get("/drawings/{drawing_id}/download")
async def download_drawing_file(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Download drawing file with proper headers for iOS compatibility"""
    # Fetch drawing from database
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    if not drawing.get("file_url"):
        raise HTTPException(status_code=404, detail="No file attached to this drawing")
    
    # Extract filename from file_url (e.g., "/uploads/drawings/filename.pdf")
    file_url = drawing["file_url"]
    filename = file_url.split("/")[-1]
    file_path = Path("uploads/drawings") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    from fastapi.responses import FileResponse
    
    # Create a clean filename for download
    drawing_name = drawing.get("name", "drawing").replace(" ", "_")
    download_filename = f"{drawing_name}.pdf"
    
    # Return file with proper headers for iOS compatibility
    # Using 'inline' for viewing in browser (iOS-friendly)
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=download_filename,
        headers={
            "Content-Disposition": f'inline; filename="{download_filename}"',
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Expose-Headers": "Content-Disposition",
        }
    )


# ==================== PROJECT COMMENTS ROUTES ====================

@api_router.get("/projects/{project_id}/comments")
async def get_project_comments(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a project (for client/contractor/consultant portal)"""
    try:
        # Verify project exists and user has access
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get comments from project_comments collection
        comments = await db.project_comments.find(
            {"project_id": project_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(500)
        
        return comments
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching project comments: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch comments")


@api_router.post("/projects/{project_id}/comments")
async def create_project_comment(
    project_id: str,
    text: str = Form(""),
    file: UploadFile = File(None),
    voice_note: UploadFile = File(None),
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a project (supports text, file, voice note)"""
    from uuid import uuid4
    
    try:
        # Verify project exists
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        comment_id = str(uuid4())
        comment = {
            "id": comment_id,
            "project_id": project_id,
            "user_id": current_user.id,
            "user_name": current_user.name,
            "user_role": current_user.role or "user",
            "text": text,
            "file_url": None,
            "file_name": None,
            "voice_note_url": None,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Handle file upload
        if file and file.filename:
            import os
            upload_dir = "/app/backend/uploads/comments"
            os.makedirs(upload_dir, exist_ok=True)
            
            file_ext = os.path.splitext(file.filename)[1]
            file_id = str(uuid4())
            file_path = f"{upload_dir}/{file_id}{file_ext}"
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            comment["file_url"] = f"{BACKEND_URL}/api/comments/file/{file_id}{file_ext}"
            comment["file_name"] = file.filename
        
        # Handle voice note upload
        if voice_note and voice_note.filename:
            import os
            upload_dir = "/app/backend/uploads/voice_notes"
            os.makedirs(upload_dir, exist_ok=True)
            
            voice_id = str(uuid4())
            voice_path = f"{upload_dir}/{voice_id}.webm"
            
            content = await voice_note.read()
            with open(voice_path, "wb") as f:
                f.write(content)
            
            comment["voice_note_url"] = f"{BACKEND_URL}/api/comments/voice/{voice_id}.webm"
        
        # Insert comment
        await db.project_comments.insert_one(comment)
        
        # Send notification to project team (owner + team leader)
        try:
            from notification_triggers_v2 import notify_project_comment
            asyncio.create_task(notify_project_comment(
                project_id=project_id,
                comment_id=comment_id,
                commenter_name=current_user.name,
                comment_preview=text[:100] if text else "Voice/File attachment"
            ))
        except Exception as e:
            print(f"Comment notification error: {str(e)}")
        
        return {"success": True, "comment_id": comment_id}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error creating project comment: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create comment")


@api_router.get("/comments/file/{filename}")
async def get_comment_file(filename: str):
    """Serve comment file attachments"""
    from fastapi.responses import FileResponse
    import os
    
    file_path = f"/app/backend/uploads/comments/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path)


@api_router.get("/comments/voice/{filename}")
async def get_comment_voice(filename: str):
    """Serve comment voice notes"""
    from fastapi.responses import FileResponse
    import os
    
    file_path = f"/app/backend/uploads/voice_notes/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Voice note not found")
    
    return FileResponse(file_path, media_type="audio/webm")


# ==================== DRAWING COMMENTS ROUTES ====================

@api_router.post("/drawings/{drawing_id}/comments")
async def create_drawing_comment(
    drawing_id: str,
    comment_data: DrawingCommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a drawing"""
    
    # Verify drawing exists
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Create comment
    comment = DrawingComment(
        drawing_id=drawing_id,
        user_id=current_user.id,
        user_name=current_user.name,
        user_role=current_user.role,
        comment_text=comment_data.comment_text
    )
    
    comment_dict = comment.model_dump()
    comment_dict['created_at'] = comment_dict['created_at'].isoformat()
    comment_dict['updated_at'] = comment_dict['updated_at'].isoformat()
    
    await db.drawing_comments.insert_one(comment_dict)
    
    # If comment requires revision, update drawing status
    if comment_data.requires_revision:
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {
                "$set": {
                    "has_pending_revision": True,
                    "status": "revision_needed",
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
            }
        )
        logger.info(f"Drawing {drawing_id} marked for revision due to comment")
    
    # Increment comment count and unread comments on drawing
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {
            "$inc": {
                "comment_count": 1,
                "unread_comments": 1
            }
        }
    )
    
    # Create in-app notifications for relevant users
    try:
        # Get project details
        project = await db.projects.find_one({"id": drawing.get("project_id")}, {"_id": 0})
        if project:
            notification_users = set()
            
            # Notify team leader if exists and not the commenter
            if project.get("lead_architect_id") and project["lead_architect_id"] != current_user.id:
                notification_users.add(project["lead_architect_id"])
            
            # Notify owner if not the commenter
            owner = await db.users.find_one({"role": "owner"}, {"_id": 0, "id": 1})
            if owner and owner["id"] != current_user.id:
                notification_users.add(owner["id"])
            
            # Create notifications for each user
            for user_id in notification_users:
                notification = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "type": "comment_added",
                    "title": "New Comment on Drawing",
                    "message": f"{current_user.name} commented on {drawing.get('name', 'a drawing')} in {project.get('title', 'a project')}",
                    "related_id": comment_dict["id"],
                    "related_type": "comment",
                    "project_id": drawing.get("project_id"),
                    "project_name": project.get("title"),
                    "is_read": False,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "created_by_id": current_user.id,
                    "created_by_name": current_user.name
                }
                await db.notifications.insert_one(notification)
    except Exception as e:
        logger.warning(f"Failed to create comment notifications: {e}")
    
    # Send WhatsApp notification to owner for drawing comment
    try:
        from notification_triggers_v2 import notify_owner_drawing_comment
        await notify_owner_drawing_comment(
            drawing_id=drawing_id,
            drawing_name=drawing.get('name', 'Drawing'),
            project_id=drawing.get('project_id'),
            commenter_name=current_user.name,
            comment_text=comment_data.comment_text,
            requires_revision=comment_data.requires_revision or False
        )
    except Exception as e:
        logger.warning(f"Owner WhatsApp notification failed (non-critical): {str(e)}")
    
    return comment

@api_router.get("/drawings/{drawing_id}/comments")
async def get_drawing_comments(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all comments for a drawing"""
    comments = await db.drawing_comments.find(
        {"drawing_id": drawing_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(1000)
    
    for comment in comments:
        if isinstance(comment.get('created_at'), str):
            comment['created_at'] = datetime.fromisoformat(comment['created_at'])
        if isinstance(comment.get('updated_at'), str):
            comment['updated_at'] = datetime.fromisoformat(comment['updated_at'])
    
    return comments

@api_router.put("/drawings/comments/{comment_id}")
async def update_drawing_comment(
    comment_id: str,
    comment_data: DrawingCommentUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a comment (only by comment author)"""
    
    # Find comment
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own comments")
    
    # Update comment
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {
            "comment_text": comment_data.comment_text,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    updated_comment = await db.drawing_comments.find_one({"id": comment_id}, {"_id": 0})
    return updated_comment

@api_router.delete("/drawings/comments/{comment_id}")
async def delete_drawing_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only by comment author)"""
    # Find comment
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own comments")
    
    # Soft delete
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Comment deleted successfully"}

@api_router.post("/drawings/comments/{comment_id}/upload-reference")
async def upload_comment_reference(
    comment_id: str,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload multiple reference files (images/PDFs) for a comment"""
    # Find comment
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add files to your own comments")
    
    uploaded_files = []
    current_files = comment.get('reference_files', [])
    
    for file in files:
        # Validate file type (expanded support for architectural files)
        allowed_extensions = [
            # Documents
            '.pdf', '.doc', '.docx', '.txt', '.rtf',
            # Images  
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
            # CAD/Drawing files
            '.dwg', '.dxf', '.dwf', '.dgn',
            # Spreadsheets
            '.xls', '.xlsx', '.csv',
            # Presentations
            '.ppt', '.pptx',
            # Archives
            '.zip', '.rar', '.7z'
        ]
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail=f"File type {file_extension} not allowed. Supported: PDF, images, CAD files (.dwg, .dxf), documents, spreadsheets, and archives")
        
        # Create uploads directory
        upload_dir = Path("uploads/comment_references")
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        unique_filename = f"{comment_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{len(uploaded_files)}{file_extension}"
        file_path = upload_dir / unique_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Return file URL
        file_url = f"/uploads/comment_references/{unique_filename}"
        uploaded_files.append({
            "url": file_url,
            "filename": file.filename,
            "original_name": file.filename
        })
        current_files.append(file_url)
    
    # Update comment with all reference files
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"reference_files": current_files}}
    )
    
    return {
        "uploaded_files": uploaded_files,
        "total_files": len(current_files),
        "message": f"Successfully uploaded {len(uploaded_files)} file(s)"
    }

@api_router.post("/drawings/comments/{comment_id}/upload-voice")
async def upload_comment_voice_note(
    comment_id: str,
    voice_note: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload voice note for a comment"""
    # Find comment
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add voice notes to your own comments")
    
    # Validate file type (audio files only)
    allowed_extensions = ['.webm', '.mp3', '.wav', '.m4a', '.ogg']
    file_extension = Path(voice_note.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only audio files are allowed")
    
    # Create uploads directory
    upload_dir = Path("uploads/voice_notes")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"voice_{comment_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.webm"
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await voice_note.read()
        buffer.write(content)
    
    # Return file URL
    voice_url = f"/uploads/voice_notes/{unique_filename}"
    
    # Add voice note URL to comment
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"voice_note_url": voice_url}}
    )
    
    # Trigger enhanced WhatsApp notification for voice note
    try:
        # Get drawing and project details for notification
        drawing = await db.project_drawings.find_one({"id": comment.get("drawing_id")}, {"_id": 0})
        if drawing:
            project_id = drawing.get("project_id")
            drawing_name = drawing.get("name", "Unknown Drawing")
            
            # Import notification function
            from notification_triggers import notify_voice_note_added
            await notify_voice_note_added(
                project_id=project_id,
                drawing_name=drawing_name,
                commenter_id=current_user.id,
                comment_id=comment_id
            )
    except Exception as e:
        logger.warning(f"Failed to send voice note notification: {e}")
    
    return {"voice_url": voice_url, "message": "Voice note uploaded successfully"}


@api_router.post("/drawings/{drawing_id}/voice-note")
async def upload_drawing_voice_note(
    drawing_id: str,
    voice_note: UploadFile = File(...),
    type: str = Form("revision_request"),
    current_user: User = Depends(get_current_user)
):
    """Upload a voice note for a drawing (revision request or feedback)"""
    # Verify drawing exists
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Validate file type
    file_extension = Path(voice_note.filename).suffix.lower()
    if file_extension not in ['.webm', '.mp3', '.wav', '.m4a', '.ogg']:
        raise HTTPException(status_code=400, detail="Invalid audio file type")
    
    # Create unique filename
    unique_filename = f"drawing_{drawing_id}_{type}_{uuid.uuid4().hex[:8]}{file_extension}"
    
    # Save voice note
    upload_dir = Path("uploads/drawing_voice_notes")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / unique_filename
    try:
        content = await voice_note.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save voice note: {str(e)}")
    
    voice_url = f"/api/drawing-voice-notes/{unique_filename}"
    
    # Update drawing with voice note URL based on type
    if type == "revision_request":
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {"revision_voice_note_url": voice_url}}
        )
    
    return {"voice_url": voice_url, "message": "Voice note uploaded successfully"}


@api_router.post("/drawings/{drawing_id}/revision-files")
async def upload_drawing_revision_files(
    drawing_id: str,
    files: List[UploadFile] = File(...),
    type: str = Form("revision_reference"),
    current_user: User = Depends(get_current_user)
):
    """Upload reference files for a drawing revision request"""
    # Verify drawing exists
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Allowed file types
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.dwg', '.dxf', '.webp']
    
    upload_dir = Path("uploads/revision_files")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_files = []
    for file in files:
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in allowed_extensions:
            continue  # Skip invalid files
        
        # Create unique filename
        unique_filename = f"rev_{drawing_id}_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = upload_dir / unique_filename
        
        try:
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            file_url = f"/api/revision-files/{unique_filename}"
            uploaded_files.append({
                "filename": file.filename,
                "url": file_url,
                "uploaded_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to save revision file: {str(e)}")
    
    # Update drawing with revision file URLs
    if uploaded_files:
        existing_files = drawing.get("revision_reference_files", [])
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {"revision_reference_files": existing_files + uploaded_files}}
        )
    
    return {"files": uploaded_files, "message": f"{len(uploaded_files)} file(s) uploaded successfully"}


@api_router.get("/drawing-voice-notes/{filename}")
async def serve_drawing_voice_note(filename: str, current_user: User = Depends(get_current_user)):
    """Serve drawing voice note files"""
    from fastapi.responses import FileResponse
    
    file_path = Path("uploads/drawing_voice_notes") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Voice note not found")
    
    return FileResponse(
        path=str(file_path),
        media_type="audio/webm",
        filename=filename
    )


@api_router.get("/revision-files/{filename}")
async def serve_revision_file(filename: str, current_user: User = Depends(get_current_user)):
    """Serve revision reference files"""
    from fastapi.responses import FileResponse
    
    file_path = Path("uploads/revision_files") / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type
    ext = Path(filename).suffix.lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.webp': 'image/webp',
        '.dwg': 'application/acad',
        '.dxf': 'application/dxf'
    }
    
    return FileResponse(
        path=str(file_path),
        media_type=media_types.get(ext, 'application/octet-stream'),
        filename=filename
    )


@api_router.post("/drawings/{drawing_id}/notify-issue")
async def notify_drawing_issue(
    drawing_id: str,
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Send notifications when a drawing is issued to selected recipients"""
    try:
        recipient_ids = request_data.get("recipient_ids", [])
        
        # Get drawing and project details
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        project = await db.projects.find_one({"id": drawing["project_id"]}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Import new notification function
        from notification_triggers_v2 import notify_drawing_issued
        await notify_drawing_issued(
            project_id=drawing["project_id"],
            drawing_id=drawing_id,
            recipient_ids=recipient_ids,
            issued_by_id=current_user.id
        )
        
        return {"message": f"Notifications sent to {len(recipient_ids)} recipient(s)"}
        
    except Exception as e:
        logger.error(f"Error sending drawing issue notifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notifications")

@api_router.post("/projects/{project_id}/unlock-next-drawing")
async def unlock_next_drawing(
    project_id: str,
    request_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Unlock the next drawing in sequence after one is issued"""
    try:
        current_sequence = request_data.get("current_sequence", 0)
        
        # Find the next drawing in sequence
        next_drawing = await db.project_drawings.find_one({
            "project_id": project_id,
            "sequence_number": current_sequence + 1,
            "deleted_at": None
        }, {"_id": 0})
        
        if next_drawing:
            # Activate the next drawing
            await db.project_drawings.update_one(
                {"id": next_drawing["id"]},
                {
                    "$set": {
                        "is_active": True,
                        "status": "planned",
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }
                }
            )
            
            # Notify team about new drawing availability
            from notification_triggers import notify_next_drawing_available
            await notify_next_drawing_available(
                project_id=project_id,
                drawing_name=next_drawing["name"],
                sequence_number=next_drawing["sequence_number"]
            )
            
            return {"message": f"Next drawing '{next_drawing['name']}' has been unlocked"}
        else:
            return {"message": "No more drawings in sequence"}
            
    except Exception as e:
        logger.error(f"Error unlocking next drawing: {e}")
        raise HTTPException(status_code=500, detail="Failed to unlock next drawing")

@api_router.post("/drawings/{drawing_id}/mark-comments-read")
async def mark_comments_read(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark all comments as read for a drawing"""
    # Reset unread_comments to 0
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"unread_comments": 0}}
    )
    return {"message": "Comments marked as read"}

@api_router.get("/voice-notes/{filename}")
async def get_voice_note(filename: str):
    """Serve voice note file - no auth required for playback"""
    from fastapi.responses import FileResponse
    
    file_path = Path("uploads/voice_notes") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Voice note not found")
    
    # Determine media type based on file extension
    extension = file_path.suffix.lower()
    media_types = {
        '.webm': 'audio/webm',
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.m4a': 'audio/mp4',
        '.ogg': 'audio/ogg'
    }
    media_type = media_types.get(extension, 'audio/webm')
    
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        }
    )

@api_router.get("/comments/reference/{filename}/download")
async def download_comment_reference(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Download comment reference file with authentication"""
    from fastapi.responses import FileResponse
    
    file_path = Path("uploads/comment_references") / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Determine media type based on file extension
    extension = file_path.suffix.lower()
    media_types = {
        '.pdf': 'application/pdf',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif'
    }
    media_type = media_types.get(extension, 'application/octet-stream')
    
    # Return file with proper headers for viewing/downloading
    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Cache-Control": "public, max-age=3600",
        }
    )


# ==================== CONTRACTOR PROGRESS TRACKING ====================

@api_router.get("/contractor-task-types")
async def get_contractor_task_types():
    """Get all contractor types and their task checklists"""
    from contractor_progress import CONTRACTOR_TASK_CHECKLISTS, get_all_contractor_types
    return {
        "contractor_types": get_all_contractor_types(),
        "task_checklists": CONTRACTOR_TASK_CHECKLISTS
    }


@api_router.get("/contractor-tasks/{contractor_type}")
async def get_tasks_for_contractor_type(contractor_type: str):
    """Get task checklist for a specific contractor type"""
    from contractor_progress import get_contractor_tasks
    tasks = get_contractor_tasks(contractor_type)
    return {"contractor_type": contractor_type, "tasks": tasks}


@api_router.get("/drawings/{drawing_id}/contractor-progress/{contractor_id}")
async def get_drawing_contractor_progress(
    drawing_id: str,
    contractor_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get contractor's progress on a specific drawing"""
    from contractor_progress import get_contractor_tasks, calculate_progress_percentage
    
    # Get the drawing
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Get contractor info
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    if not contractor:
        contractor = await db.users.find_one({"id": contractor_id}, {"_id": 0})
    
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    contractor_type = contractor.get('contractor_type', 'Other')
    
    # Get all tasks for this contractor type
    all_tasks = get_contractor_tasks(contractor_type)
    
    # Get progress data for this drawing+contractor
    progress_data = drawing.get('contractor_progress', {}).get(contractor_id, {})
    completed_tasks = progress_data.get('completed_tasks', [])
    
    # Calculate percentage
    percentage = calculate_progress_percentage(completed_tasks, contractor_type)
    
    return {
        "drawing_id": drawing_id,
        "contractor_id": contractor_id,
        "contractor_type": contractor_type,
        "tasks": all_tasks,
        "completed_tasks": completed_tasks,
        "progress_percentage": percentage,
        "last_updated": progress_data.get('last_updated')
    }


@api_router.post("/drawings/{drawing_id}/contractor-progress/{contractor_id}/update")
async def update_drawing_contractor_progress(
    drawing_id: str,
    contractor_id: str,
    task_id: str = Body(..., embed=True),
    completed: bool = Body(..., embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Update contractor progress on a drawing - mark a task as complete or incomplete.
    Contractors can mark tasks complete.
    Owner/Client can remove completed tasks (with required comment).
    """
    from contractor_progress import get_contractor_tasks, calculate_progress_percentage
    
    # Get the drawing
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Get contractor info
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    if not contractor:
        contractor = await db.users.find_one({"id": contractor_id}, {"_id": 0})
    
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    contractor_type = contractor.get('contractor_type', 'Other')
    
    # Verify task exists
    all_tasks = get_contractor_tasks(contractor_type)
    task_ids = [t['id'] for t in all_tasks]
    if task_id not in task_ids:
        raise HTTPException(status_code=400, detail="Invalid task ID for this contractor type")
    
    # Get current progress
    progress_data = drawing.get('contractor_progress', {})
    contractor_progress = progress_data.get(contractor_id, {'completed_tasks': []})
    completed_tasks = contractor_progress.get('completed_tasks', [])
    
    # Permission check for removing completion (only owner/client can remove)
    if not completed and task_id in completed_tasks:
        if not current_user.is_owner and current_user.role != 'client':
            raise HTTPException(
                status_code=403, 
                detail="Only owner or client can remove completed task marks"
            )
    
    # Update completed tasks
    if completed and task_id not in completed_tasks:
        completed_tasks.append(task_id)
    elif not completed and task_id in completed_tasks:
        completed_tasks.remove(task_id)
    
    # Update the database
    contractor_progress['completed_tasks'] = completed_tasks
    contractor_progress['last_updated'] = datetime.now(timezone.utc).isoformat()
    contractor_progress['last_updated_by'] = current_user.id
    
    progress_data[contractor_id] = contractor_progress
    
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"contractor_progress": progress_data}}
    )
    
    # Calculate new percentage
    percentage = calculate_progress_percentage(completed_tasks, contractor_type)
    
    return {
        "success": True,
        "task_id": task_id,
        "completed": completed,
        "progress_percentage": percentage,
        "completed_tasks": completed_tasks
    }


@api_router.post("/drawings/{drawing_id}/contractor-progress/{contractor_id}/remove-task")
async def remove_contractor_task_completion(
    drawing_id: str,
    contractor_id: str,
    task_id: str = Body(..., embed=True),
    reason: str = Body(..., embed=True, min_length=10),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a completed task mark - requires a reason comment.
    Only owner or client can do this.
    """
    # Verify permission
    if not current_user.is_owner and current_user.role != 'client':
        raise HTTPException(
            status_code=403, 
            detail="Only owner or client can remove completed task marks"
        )
    
    # Get the drawing
    drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    # Get current progress
    progress_data = drawing.get('contractor_progress', {})
    contractor_progress = progress_data.get(contractor_id, {'completed_tasks': []})
    completed_tasks = contractor_progress.get('completed_tasks', [])
    
    if task_id not in completed_tasks:
        raise HTTPException(status_code=400, detail="Task is not marked as completed")
    
    # Remove the task
    completed_tasks.remove(task_id)
    
    # Log the removal with reason
    removal_log = contractor_progress.get('removal_log', [])
    removal_log.append({
        "task_id": task_id,
        "removed_by": current_user.id,
        "removed_by_name": current_user.name,
        "reason": reason,
        "removed_at": datetime.now(timezone.utc).isoformat()
    })
    
    contractor_progress['completed_tasks'] = completed_tasks
    contractor_progress['removal_log'] = removal_log
    contractor_progress['last_updated'] = datetime.now(timezone.utc).isoformat()
    
    progress_data[contractor_id] = contractor_progress
    
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"contractor_progress": progress_data}}
    )
    
    # Also add a comment on the drawing about the removal
    comment = {
        "id": str(uuid.uuid4()),
        "drawing_id": drawing_id,
        "user_id": current_user.id,
        "user_name": current_user.name,
        "comment_text": f"Task completion removed: {reason}",
        "comment_type": "progress_removal",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.drawing_comments.insert_one(comment)
    
    return {
        "success": True,
        "message": "Task completion removed",
        "reason": reason
    }


@api_router.get("/contractors/{contractor_id}/projects-progress")
async def get_contractor_projects_progress(
    contractor_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get all projects a contractor is involved in with their progress on each.
    Shows overall progress report for the contractor.
    """
    from contractor_progress import get_contractor_tasks, calculate_progress_percentage
    
    # Get contractor info
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    if not contractor:
        contractor = await db.users.find_one({"id": contractor_id}, {"_id": 0})
    
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    contractor_type = contractor.get('contractor_type', 'Other')
    contractor_name = contractor.get('name', 'Contractor')
    
    # Find all projects where this contractor is assigned
    projects = []
    async for project in db.projects.find({}, {"_id": 0}):
        assigned_contractors = project.get('assigned_contractors', {})
        is_assigned = False
        
        if isinstance(assigned_contractors, dict):
            if contractor_id in assigned_contractors.values():
                is_assigned = True
        elif isinstance(assigned_contractors, list):
            if contractor_id in assigned_contractors:
                is_assigned = True
        
        if not is_assigned:
            continue
        
        # Get all issued drawings for this project
        drawings = await db.project_drawings.find({
            "project_id": project['id'],
            "is_issued": True
        }, {"_id": 0}).to_list(100)
        
        # Calculate progress for each drawing
        drawing_progress = []
        total_tasks = 0
        completed_tasks_count = 0
        
        for drawing in drawings:
            progress_data = drawing.get('contractor_progress', {}).get(contractor_id, {})
            completed_tasks = progress_data.get('completed_tasks', [])
            all_tasks = get_contractor_tasks(contractor_type)
            
            percentage = calculate_progress_percentage(completed_tasks, contractor_type)
            
            drawing_progress.append({
                "drawing_id": drawing['id'],
                "drawing_name": drawing.get('name', 'Drawing'),
                "progress_percentage": percentage,
                "completed_tasks": len(completed_tasks),
                "total_tasks": len(all_tasks)
            })
            
            total_tasks += len(all_tasks)
            completed_tasks_count += len(completed_tasks)
        
        # Calculate overall project progress
        overall_progress = int((completed_tasks_count / total_tasks) * 100) if total_tasks > 0 else 0
        
        projects.append({
            "project_id": project['id'],
            "project_name": project.get('title', project.get('name', 'Project')),
            "project_code": project.get('code'),
            "issued_drawings_count": len(drawings),
            "overall_progress": overall_progress,
            "drawing_progress": drawing_progress
        })
    
    return {
        "contractor_id": contractor_id,
        "contractor_name": contractor_name,
        "contractor_type": contractor_type,
        "total_projects": len(projects),
        "projects": projects
    }


# ==================== CONTRACTOR MANAGEMENT ROUTES ====================

@api_router.post("/contractors")
async def create_contractor(
    contractor_data: ContractorCreate,
    current_user: User = Depends(require_owner)
):
    """Create a new contractor/consultant (Owner only)"""
    contractor = Contractor(**contractor_data.model_dump())
    contractor_dict = contractor.model_dump()
    
    # Convert datetimes to ISO strings
    for field in ['created_at', 'updated_at']:
        if contractor_dict.get(field):
            contractor_dict[field] = contractor_dict[field].isoformat()
    
    await db.contractors.insert_one(contractor_dict)
    return contractor

@api_router.get("/contractors")
async def get_contractors(current_user: User = Depends(get_current_user)):
    """
    Get contractors based on user role:
    - Owner/Team Members: See all approved contractors
    - Clients: See ONLY contractors assigned to their projects
    - Contractors: See only themselves
    """
    
    # If client, filter to only contractors on their projects
    if current_user.role == "client":
        # Find client's projects
        client = await db.clients.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        if client:
            client_projects = await db.projects.find(
                {"client_id": client["id"], "deleted_at": None},
                {"_id": 0, "assigned_contractors": 1}
            ).to_list(100)
        else:
            client_projects = await db.projects.find(
                {"client_id": current_user.id, "deleted_at": None},
                {"_id": 0, "assigned_contractors": 1}
            ).to_list(100)
        
        # Collect all contractor IDs from client's projects
        contractor_ids = set()
        for project in client_projects:
            assigned = project.get('assigned_contractors', {})
            if isinstance(assigned, dict):
                contractor_ids.update(assigned.values())
        
        if not contractor_ids:
            return []
        
        # Get only those contractors
        contractors = await db.contractors.find(
            {"id": {"$in": list(contractor_ids)}, "deleted_at": None},
            {"_id": 0}
        ).to_list(100)
        
        return contractors
    
    # If contractor, only return self
    if current_user.role == "contractor":
        contractor = await db.contractors.find_one(
            {"email": current_user.email, "deleted_at": None},
            {"_id": 0}
        )
        return [contractor] if contractor else []
    
    # Owner and team members see all
    contractors = await db.contractors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    
    # Filter out contractors whose user accounts are not approved
    approved_contractors = []
    for contractor in contractors:
        if contractor.get('user_id'):
            user = await db.users.find_one(
                {"id": contractor['user_id']}, 
                {"_id": 0, "approval_status": 1}
            )
            # Only include if user is approved
            if user and user.get('approval_status') == 'approved':
                approved_contractors.append(contractor)
        else:
            # Contractor created manually without user account - always show
            approved_contractors.append(contractor)
    
    return approved_contractors

@api_router.get("/contractors/{contractor_id}")
async def get_contractor(
    contractor_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific contractor"""
    contractor = await db.contractors.find_one(
        {"id": contractor_id, "deleted_at": None},
        {"_id": 0}
    )
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    return contractor

@api_router.put("/contractors/{contractor_id}")
async def update_contractor(
    contractor_id: str,
    contractor_data: ContractorCreate,
    current_user: User = Depends(require_owner)
):
    """Update a contractor (Owner only)"""
    update_dict = contractor_data.model_dump()
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.contractors.update_one(
        {"id": contractor_id, "deleted_at": None},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    return await get_contractor(contractor_id, current_user)

@api_router.delete("/contractors/{contractor_id}")
async def delete_contractor(
    contractor_id: str,
    current_user: User = Depends(require_owner)
):
    """HARD DELETE a contractor (Owner only) - Only if no active projects exist"""
    # Get contractor to find associated user_id
    contractor = await db.contractors.find_one({"id": contractor_id}, {"_id": 0})
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    # Check for active projects where this contractor is assigned
    active_projects = await db.projects.find({
        "contractors": contractor_id,
        "$or": [
            {"archived": False},
            {"archived": {"$exists": False}}
        ]
    }, {"_id": 0, "name": 1}).to_list(10)
    
    if active_projects:
        project_names = ", ".join([p.get('name', 'Unnamed') for p in active_projects])
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete contractor. Active projects exist: {project_names}. Please archive these projects first."
        )
    
    # Get contractor info for cleanup
    contractor_email = contractor.get('email')
    contractor_phone = contractor.get('phone')
    contractor_user_id = contractor.get('user_id')
    
    # HARD DELETE from contractors collection
    await db.contractors.delete_one({"id": contractor_id})
    logger.info(f"Hard deleted contractor: {contractor.get('name')}")
    
    # Delete the associated user account (if exists)
    if contractor_user_id:
        await db.users.delete_one({"id": contractor_user_id})
        logger.info(f"Hard deleted user account for contractor: {contractor.get('name')}")
    
    # Clean up related records to allow fresh re-registration
    if contractor_email:
        await db.pending_registrations.delete_many({"email": contractor_email})
        await db.invitations.delete_many({"email": contractor_email})
        await db.team_verifications.delete_many({"email": contractor_email})
    
    if contractor_phone:
        # Normalize phone for cleanup
        phone_digits = ''.join(filter(str.isdigit, contractor_phone))[-10:]
        await db.invitations.delete_many({"phone": {"$regex": phone_digits}})
        await db.pending_registrations.delete_many({"phone": {"$regex": phone_digits}})
    
    return {"message": "Contractor permanently deleted. They can now be invited fresh."}

@api_router.get("/contractor-types")
async def get_contractor_types():
    """Get list of predefined contractor types"""
    return [{"value": t.value, "label": t.value} for t in ContractorType]

@api_router.get("/consultant-types")
async def get_consultant_types():
    """Get list of predefined consultant types"""
    return [{"value": t.value, "label": t.value} for t in ConsultantType]


# ==================== PROJECT TEMPORARY ACCESS MANAGEMENT ====================

@api_router.post("/projects/{project_id}/grant-access")
async def grant_temporary_project_access(
    project_id: str,
    user_id: str = Body(..., embed=True),
    expires_at: str = Body(..., embed=True),  # ISO date string
    current_user: User = Depends(get_current_user)
):
    """
    Grant temporary access to a project for another team member.
    Only owner or project team leader can grant access.
    """
    # Get project
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permission - only owner or team leader of this project
    if not current_user.is_owner and project.get('team_leader_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner or team leader can grant access")
    
    # Get the user to grant access to
    target_user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Parse expiry date
    try:
        expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
    except:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Check if access already exists
    existing = await db.project_team_access.find_one({
        "project_id": project_id,
        "user_id": user_id
    })
    
    if existing:
        # Update existing access
        await db.project_team_access.update_one(
            {"project_id": project_id, "user_id": user_id},
            {"$set": {
                "expires_at": expiry_date.isoformat(),
                "granted_by": current_user.id,
                "granted_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        # Create new access
        access_record = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "user_id": user_id,
            "user_name": target_user.get('name'),
            "granted_by": current_user.id,
            "granted_by_name": current_user.name,
            "expires_at": expiry_date.isoformat(),
            "granted_at": datetime.now(timezone.utc).isoformat()
        }
        await db.project_team_access.insert_one(access_record)
    
    return {
        "success": True,
        "message": f"Access granted to {target_user.get('name')} until {expiry_date.strftime('%d %b %Y')}"
    }


@api_router.delete("/projects/{project_id}/revoke-access/{user_id}")
async def revoke_project_access(
    project_id: str,
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Revoke temporary project access"""
    # Get project
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permission
    if not current_user.is_owner and project.get('team_leader_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner or team leader can revoke access")
    
    result = await db.project_team_access.delete_one({
        "project_id": project_id,
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Access record not found")
    
    return {"success": True, "message": "Access revoked"}


@api_router.get("/projects/{project_id}/access-list")
async def get_project_access_list(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get list of users with temporary access to project"""
    # Get project
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check permission - only owner or team leader
    if not current_user.is_owner and project.get('team_leader_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    access_list = await db.project_team_access.find(
        {"project_id": project_id},
        {"_id": 0}
    ).to_list(100)
    
    # Filter out expired entries
    now = datetime.now(timezone.utc)
    active_access = []
    for access in access_list:
        expires_at = access.get('expires_at')
        if expires_at:
            try:
                exp_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                if exp_date > now:
                    access['is_active'] = True
                    active_access.append(access)
            except:
                pass
    
    return active_access


@api_router.post("/projects/{project_id}/request-access")
async def request_project_access(
    project_id: str,
    message: str = Body("", embed=True),
    current_user: User = Depends(get_current_user)
):
    """
    Request access to a project from team leader/owner.
    Creates an access request that team leader/owner can approve.
    """
    # Get project
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check if already has access or is the team leader
    if project.get('team_leader_id') == current_user.id:
        raise HTTPException(status_code=400, detail="You are already the team leader of this project")
    
    existing_access = await db.project_team_access.find_one({
        "project_id": project_id,
        "user_id": current_user.id,
        "expires_at": {"$gt": datetime.now(timezone.utc).isoformat()}
    })
    
    if existing_access:
        raise HTTPException(status_code=400, detail="You already have access to this project")
    
    # Check for pending request
    pending_request = await db.project_access_requests.find_one({
        "project_id": project_id,
        "requester_id": current_user.id,
        "status": "pending"
    })
    
    if pending_request:
        raise HTTPException(status_code=400, detail="You already have a pending access request")
    
    # Create access request
    request_record = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "project_name": project.get('title', project.get('name', 'Project')),
        "requester_id": current_user.id,
        "requester_name": current_user.name,
        "message": message,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.project_access_requests.insert_one(request_record)
    
    # TODO: Send notification to team leader/owner
    
    return {
        "success": True,
        "message": "Access request sent. The team leader or owner will review your request."
    }


@api_router.get("/project-access-requests")
async def get_pending_access_requests(
    current_user: User = Depends(get_current_user)
):
    """Get pending access requests for projects the user leads or owns"""
    if current_user.is_owner:
        # Owner sees all pending requests
        requests = await db.project_access_requests.find(
            {"status": "pending"},
            {"_id": 0}
        ).to_list(100)
    else:
        # Team leader sees requests for their projects
        user_projects = await db.projects.find(
            {"team_leader_id": current_user.id, "deleted_at": None},
            {"_id": 0, "id": 1}
        ).to_list(100)
        project_ids = [p["id"] for p in user_projects]
        
        requests = await db.project_access_requests.find(
            {"project_id": {"$in": project_ids}, "status": "pending"},
            {"_id": 0}
        ).to_list(100)
    
    return requests


@api_router.post("/project-access-requests/{request_id}/respond")
async def respond_to_access_request(
    request_id: str,
    approved: bool = Body(..., embed=True),
    expires_at: str = Body(None, embed=True),
    current_user: User = Depends(get_current_user)
):
    """Approve or deny an access request"""
    # Get the request
    access_request = await db.project_access_requests.find_one(
        {"id": request_id, "status": "pending"},
        {"_id": 0}
    )
    
    if not access_request:
        raise HTTPException(status_code=404, detail="Access request not found")
    
    # Get project
    project = await db.projects.find_one(
        {"id": access_request["project_id"]},
        {"_id": 0}
    )
    
    # Check permission
    if not current_user.is_owner and project.get('team_leader_id') != current_user.id:
        raise HTTPException(status_code=403, detail="Only owner or team leader can respond to requests")
    
    if approved:
        if not expires_at:
            # Default to 30 days
            expiry_date = datetime.now(timezone.utc) + timedelta(days=30)
        else:
            try:
                expiry_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            except:
                expiry_date = datetime.now(timezone.utc) + timedelta(days=30)
        
        # Grant access
        access_record = {
            "id": str(uuid.uuid4()),
            "project_id": access_request["project_id"],
            "user_id": access_request["requester_id"],
            "user_name": access_request["requester_name"],
            "granted_by": current_user.id,
            "granted_by_name": current_user.name,
            "expires_at": expiry_date.isoformat(),
            "granted_at": datetime.now(timezone.utc).isoformat()
        }
        await db.project_team_access.insert_one(access_record)
    
    # Update request status
    await db.project_access_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": "approved" if approved else "denied",
            "responded_by": current_user.id,
            "responded_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "success": True,
        "message": "Access granted" if approved else "Access denied"
    }


# ==================== PROJECT TEAM MANAGEMENT ROUTES ====================

@api_router.get("/projects/{project_id}/team")
async def get_project_team(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all team members assigned to a project (contractors, consultants, co-clients)"""
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    team = {
        "contractors": [],
        "consultants": [],
        "co_clients": [],
        "team_leader": None
    }
    
    # Get assigned contractors
    assigned_contractors = project.get('assigned_contractors', {})
    for contractor_type, contractor_id in assigned_contractors.items():
        if contractor_id:
            contractor = await db.contractors.find_one({"id": contractor_id, "deleted_at": None}, {"_id": 0})
            if contractor:
                contractor['assigned_type'] = contractor_type
                team['contractors'].append(contractor)
    
    # Get assigned consultants from project fields
    consultant_fields = {
        'structural_consultant': 'Structural',
        'electrical_consultant': 'Electrical',
        'plumbing_consultant': 'Plumbing',
        'landscape_consultant': 'Landscape',
        'automation_consultant': 'Automation'
    }
    
    for field, consultant_type in consultant_fields.items():
        consultant_info = project.get(field)
        if consultant_info and isinstance(consultant_info, dict):
            # Check if it has an ID (linked to consultant record)
            if consultant_info.get('id'):
                consultant = await db.consultants.find_one({"id": consultant_info['id'], "deleted_at": None}, {"_id": 0})
                if consultant:
                    consultant['assigned_type'] = consultant_type
                    team['consultants'].append(consultant)
            elif consultant_info.get('name'):
                # Contact info style (not linked to consultant record)
                team['consultants'].append({
                    'name': consultant_info.get('name'),
                    'phone': consultant_info.get('phone'),
                    'email': consultant_info.get('email'),
                    'assigned_type': consultant_type,
                    'is_contact_only': True
                })
    
    # Get co-clients
    co_clients = await db.co_clients.find(
        {"project_id": project_id, "deleted_at": None},
        {"_id": 0}
    ).to_list(100)
    team['co_clients'] = co_clients
    
    # Get team leader
    if project.get('team_leader_id'):
        team_leader = await db.users.find_one(
            {"id": project['team_leader_id']},
            {"_id": 0, "password": 0}
        )
        team['team_leader'] = team_leader
    
    return team

@api_router.post("/projects/{project_id}/assign-contractor")
async def assign_contractor_to_project(
    project_id: str,
    contractor_id: str = Body(...),
    contractor_type: str = Body(...),
    send_notification: bool = Body(True),
    current_user: User = Depends(require_owner_or_team_leader)
):
    """Assign a contractor to a project"""
    # Verify project exists
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify contractor exists
    contractor = await db.contractors.find_one({"id": contractor_id, "deleted_at": None}, {"_id": 0})
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    # Update project's assigned_contractors
    assigned_contractors = project.get('assigned_contractors', {})
    assigned_contractors[contractor_type] = contractor_id
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            "assigned_contractors": assigned_contractors,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send notification to contractor
    if send_notification:
        try:
            from notification_triggers_v2 import notify_project_assignment
            await notify_project_assignment(
                project=project,
                person_id=contractor_id,
                person_type='contractor',
                role_type=contractor_type
            )
        except Exception as e:
            logger.error(f"Error sending contractor assignment notification: {str(e)}")
    
    return {
        "message": f"{contractor['name']} assigned as {contractor_type} contractor",
        "contractor": contractor
    }

@api_router.delete("/projects/{project_id}/unassign-contractor/{contractor_type}")
async def unassign_contractor_from_project(
    project_id: str,
    contractor_type: str,
    current_user: User = Depends(require_owner_or_team_leader)
):
    """Remove a contractor assignment from a project"""
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    assigned_contractors = project.get('assigned_contractors', {})
    if contractor_type in assigned_contractors:
        del assigned_contractors[contractor_type]
        
        await db.projects.update_one(
            {"id": project_id},
            {"$set": {
                "assigned_contractors": assigned_contractors,
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
    
    return {"message": f"{contractor_type} contractor unassigned from project"}

@api_router.post("/projects/{project_id}/assign-consultant")
async def assign_consultant_to_project(
    project_id: str,
    consultant_id: str = Body(None),
    consultant_type: str = Body(...),
    consultant_name: str = Body(None),
    consultant_phone: str = Body(None),
    consultant_email: str = Body(None),
    send_notification: bool = Body(True),
    current_user: User = Depends(require_owner_or_team_leader)
):
    """Assign a consultant to a project (either existing consultant or contact info)"""
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Map consultant type to project field
    field_mapping = {
        'Structural': 'structural_consultant',
        'Structure': 'structural_consultant',
        'Electrical': 'electrical_consultant',
        'Plumbing': 'plumbing_consultant',
        'Landscape': 'landscape_consultant',
        'Automation': 'automation_consultant',
        'MEP': 'mep_consultant',
        'Air Conditioning': 'ac_consultant'
    }
    
    field_name = field_mapping.get(consultant_type)
    if not field_name:
        field_name = f"{consultant_type.lower().replace(' ', '_')}_consultant"
    
    consultant_data = None
    consultant_record = None
    
    if consultant_id:
        # Link to existing consultant
        consultant_record = await db.consultants.find_one({"id": consultant_id, "deleted_at": None}, {"_id": 0})
        if not consultant_record:
            raise HTTPException(status_code=404, detail="Consultant not found")
        
        consultant_data = {
            "id": consultant_id,
            "name": consultant_record.get('name'),
            "phone": consultant_record.get('phone'),
            "email": consultant_record.get('email')
        }
    else:
        # Create contact info only
        consultant_data = {
            "name": consultant_name,
            "phone": consultant_phone,
            "email": consultant_email
        }
    
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {
            field_name: consultant_data,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    # Send notification
    if send_notification and consultant_id and consultant_record:
        try:
            from notification_triggers_v2 import notify_project_assignment
            await notify_project_assignment(
                project=project,
                person_id=consultant_id,
                person_type='consultant',
                role_type=consultant_type
            )
        except Exception as e:
            logger.error(f"Error sending consultant assignment notification: {str(e)}")
    
    return {
        "message": f"Consultant assigned as {consultant_type}",
        "consultant": consultant_data
    }

@api_router.delete("/projects/{project_id}/unassign-consultant/{consultant_type}")
async def unassign_consultant_from_project(
    project_id: str,
    consultant_type: str,
    current_user: User = Depends(require_owner_or_team_leader)
):
    """Remove a consultant assignment from a project"""
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    field_mapping = {
        'Structural': 'structural_consultant',
        'Structure': 'structural_consultant',
        'Electrical': 'electrical_consultant',
        'Plumbing': 'plumbing_consultant',
        'Landscape': 'landscape_consultant',
        'Automation': 'automation_consultant',
        'MEP': 'mep_consultant'
    }
    
    field_name = field_mapping.get(consultant_type)
    if not field_name:
        field_name = f"{consultant_type.lower().replace(' ', '_')}_consultant"
    
    await db.projects.update_one(
        {"id": project_id},
        {"$unset": {field_name: ""}}
    )
    
    return {"message": f"{consultant_type} consultant unassigned from project"}


# ==================== VENDOR ROUTES ====================

@api_router.post("/vendors")
async def create_vendor(
    vendor_data: VendorCreate,
    current_user: User = Depends(require_owner)
):
    """Create a new vendor (Owner only)"""
    vendor = Vendor(**vendor_data.model_dump())
    vendor_dict = vendor.model_dump()
    
    # Convert datetimes to ISO strings
    for field in ['created_at', 'updated_at']:
        if vendor_dict.get(field):
            vendor_dict[field] = vendor_dict[field].isoformat()
    
    await db.vendors.insert_one(vendor_dict)
    return vendor

@api_router.get("/vendors")
async def get_vendors(current_user: User = Depends(get_current_user)):
    """Get all vendors"""
    vendors = await db.vendors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    return vendors

@api_router.get("/vendors/{vendor_id}")
async def get_vendor(
    vendor_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific vendor"""
    vendor = await db.vendors.find_one(
        {"id": vendor_id, "deleted_at": None},
        {"_id": 0}
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    return vendor

@api_router.put("/vendors/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    vendor_data: VendorUpdate,
    current_user: User = Depends(require_owner)
):
    """Update a vendor (Owner only)"""
    update_dict = {k: v for k, v in vendor_data.model_dump().items() if v is not None}
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.vendors.update_one(
        {"id": vendor_id, "deleted_at": None},
        {"$set": update_dict}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return await get_vendor(vendor_id, current_user)

@api_router.delete("/vendors/{vendor_id}")
async def delete_vendor(
    vendor_id: str,
    current_user: User = Depends(require_owner)
):
    """Soft delete a vendor (Owner only)"""
    result = await db.vendors.update_one(
        {"id": vendor_id},
        {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return {"message": "Vendor deleted successfully"}

@api_router.get("/vendor-types")
async def get_vendor_types():
    """Get list of predefined vendor types"""
    return [{"value": t.value, "label": t.value} for t in VendorType]


# ==================== TASK MANAGEMENT ROUTES ====================

@api_router.post("/weekly-targets")
async def create_weekly_target(
    target_data: WeeklyTargetCreate,
    current_user: User = Depends(require_owner)
):
    """Create a weekly target for a team member (owner only)"""
    from datetime import timedelta
    
    week_start = datetime.fromisoformat(target_data.week_start_date)
    week_end = week_start + timedelta(days=6)
    
    weekly_target = WeeklyTarget(
        assigned_to_id=target_data.assigned_to_id,
        week_start_date=week_start,
        week_end_date=week_end,
        target_type=target_data.target_type,
        target_description=target_data.target_description,
        target_quantity=target_data.target_quantity,
        project_id=target_data.project_id,
        drawing_ids=target_data.drawing_ids,
        created_by_id=current_user.id
    )
    
    target_dict = weekly_target.model_dump()
    for field in ['week_start_date', 'week_end_date', 'created_at', 'updated_at']:
        if target_dict.get(field):
            target_dict[field] = target_dict[field].isoformat() if isinstance(target_dict[field], datetime) else target_dict[field]
    
    await db.weekly_targets.insert_one(target_dict)
    
    # Auto-create daily tasks if breakdown provided
    if target_data.daily_breakdown:
        workdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for i, quantity in enumerate(target_data.daily_breakdown[:5]):  # Max 5 days
            if quantity > 0:
                task_date = week_start + timedelta(days=i)
                daily_task = DailyTask(
                    weekly_target_id=weekly_target.id,
                    assigned_to_id=target_data.assigned_to_id,
                    task_date=task_date,
                    task_description=f"{workdays[i]}: {target_data.target_description}",
                    task_quantity=quantity,
                    project_id=target_data.project_id,
                    drawing_id=target_data.drawing_ids[0] if target_data.drawing_ids else None
                )
                task_dict = daily_task.model_dump()
                for field in ['task_date', 'completed_at', 'whatsapp_sent_at', 'created_at', 'updated_at']:
                    if task_dict.get(field):
                        task_dict[field] = task_dict[field].isoformat() if isinstance(task_dict[field], datetime) else task_dict[field]
                await db.daily_tasks.insert_one(task_dict)
    
    return {k: v for k, v in target_dict.items() if k != '_id'}

@api_router.get("/weekly-targets")
async def get_weekly_targets(
    user_id: Optional[str] = None,
    week_start: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get weekly targets (own or all if owner)"""
    query = {}
    
    # If not owner, can only see own targets
    if not current_user.is_owner:
        query["assigned_to_id"] = current_user.id
    elif user_id:
        query["assigned_to_id"] = user_id
    
    if week_start:
        query["week_start_date"] = week_start
    
    targets = await db.weekly_targets.find(query, {"_id": 0}).to_list(1000)
    
    for target in targets:
        for field in ['week_start_date', 'week_end_date', 'created_at', 'updated_at']:
            if isinstance(target.get(field), str):
                target[field] = datetime.fromisoformat(target[field])
    
    return targets

@api_router.get("/daily-tasks")
async def get_daily_tasks(
    date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get daily tasks for current user or specific date"""
    query = {"assigned_to_id": current_user.id}
    
    if date:
        query["task_date"] = date
    
    tasks = await db.daily_tasks.find(query, {"_id": 0}).to_list(1000)
    
    for task in tasks:
        for field in ['task_date', 'completed_at', 'whatsapp_sent_at', 'created_at', 'updated_at']:
            if isinstance(task.get(field), str):
                task[field] = datetime.fromisoformat(task[field])
    
    return tasks

@api_router.put("/daily-tasks/{task_id}")
async def update_daily_task(
    task_id: str,
    task_data: DailyTaskUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update daily task (mark as completed)"""
    update_dict = {k: v for k, v in task_data.model_dump().items() if v is not None}
    
    if update_dict.get('completed') == True:
        update_dict['completed_at'] = datetime.now(timezone.utc).isoformat()
        
        # Update weekly target progress
        task = await db.daily_tasks.find_one({"id": task_id})
        if task:
            weekly_target = await db.weekly_targets.find_one({"id": task['weekly_target_id']})
            if weekly_target:
                new_completed = weekly_target.get('completed_quantity', 0) + task['task_quantity']
                await db.weekly_targets.update_one(
                    {"id": task['weekly_target_id']},
                    {"$set": {
                        "completed_quantity": new_completed,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.daily_tasks.update_one(
        {"id": task_id},
        {"$set": update_dict}
    )
    
    return {"message": "Task updated successfully"}

@api_router.get("/weekly-ratings")
async def get_weekly_ratings(
    user_id: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get weekly ratings"""
    query = {}
    
    if not current_user.is_owner:
        query["team_member_id"] = current_user.id
    elif user_id:
        query["team_member_id"] = user_id
    
    ratings = await db.weekly_ratings.find(query, {"_id": 0}).sort("week_start_date", -1).to_list(100)
    
    for rating in ratings:
        for field in ['week_start_date', 'week_end_date', 'created_at']:
            if isinstance(rating.get(field), str):
                rating[field] = datetime.fromisoformat(rating[field])
    
    return ratings

@api_router.post("/calculate-weekly-ratings")
async def calculate_weekly_ratings(
    week_start: str,
    current_user: User = Depends(require_owner)
):
    """Calculate ratings for all team members for a specific week (owner only, run on Saturday)"""
    from datetime import timedelta
    
    week_start_date = datetime.fromisoformat(week_start)
    week_end_date = week_start_date + timedelta(days=6)
    
    # Get all team members
    team_members = await db.users.find({}, {"_id": 0}).to_list(1000)
    
    ratings_created = []
    
    for member in team_members:
        # Get weekly targets for this member
        targets = await db.weekly_targets.find({
            "assigned_to_id": member['id'],
            "week_start_date": week_start
        }, {"_id": 0}).to_list(100)
        
        if not targets:
            continue
        
        total_targets = sum(t.get('target_quantity', 0) for t in targets)
        completed_targets = sum(t.get('completed_quantity', 0) for t in targets)
        
        if total_targets == 0:
            continue
        
        completion_percentage = (completed_targets / total_targets) * 100
        
        # Rating scale: 0-5
        # 100%+ = 5, 90-99% = 4.5, 80-89% = 4, 70-79% = 3.5, 60-69% = 3, 50-59% = 2.5, <50% = 1-2
        if completion_percentage >= 100:
            rating = 5.0
        elif completion_percentage >= 90:
            rating = 4.5
        elif completion_percentage >= 80:
            rating = 4.0
        elif completion_percentage >= 70:
            rating = 3.5
        elif completion_percentage >= 60:
            rating = 3.0
        elif completion_percentage >= 50:
            rating = 2.5
        else:
            rating = max(1.0, completion_percentage / 50 * 2)
        
        weekly_rating = WeeklyRating(
            team_member_id=member['id'],
            week_start_date=week_start_date,
            week_end_date=week_end_date,
            total_targets=total_targets,
            completed_targets=completed_targets,
            completion_percentage=completion_percentage,
            rating=rating,
            weekly_targets=[t['id'] for t in targets]
        )
        
        rating_dict = weekly_rating.model_dump()
        for field in ['week_start_date', 'week_end_date', 'created_at']:
            if rating_dict.get(field):
                rating_dict[field] = rating_dict[field].isoformat() if isinstance(rating_dict[field], datetime) else rating_dict[field]
        
        # Update weekly targets with ratings
        for target in targets:
            await db.weekly_targets.update_one(
                {"id": target['id']},
                {"$set": {"rating": rating}}
            )
        
        await db.weekly_ratings.insert_one(rating_dict)
        ratings_created.append({k: v for k, v in rating_dict.items() if k != '_id'})
    
    return {"message": f"Calculated ratings for {len(ratings_created)} team members", "ratings": ratings_created}

    # If marking has_pending_revision as False (resolving revision)
    if update_dict.get('has_pending_revision') == False:
        # Increment revision count
        update_dict['revision_count'] = drawing.get('revision_count', 0) + 1
        
        # Update revision history - mark as resolved
        revision_history = drawing.get('revision_history', [])
        if revision_history and not revision_history[-1].get('resolved_date'):
            revision_history[-1]['resolved_date'] = datetime.now(timezone.utc).isoformat()
            update_dict['revision_history'] = revision_history
        
        # Clear current revision fields
        update_dict['current_revision_notes'] = None
        update_dict['current_revision_due_date'] = None
    
    if update_dict.get('due_date') and isinstance(update_dict['due_date'], str):
        update_dict['due_date'] = datetime.fromisoformat(update_dict['due_date']).isoformat()
    
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": update_dict}
    )
    return {"message": "Drawing updated successfully"}

@api_router.delete("/drawings/{drawing_id}")
async def delete_drawing(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Soft delete a drawing"""
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Drawing deleted successfully"}


@api_router.post("/drawings/{drawing_id}/upload")
async def upload_drawing(
    drawing_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    drawing = await db.drawings.find_one({"id": drawing_id})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    try:
        # Validate file size
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds maximum allowed size")
        
        # Save to local storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_dir = UPLOAD_DIR / "drawings" / drawing['project_id']
        project_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = project_dir / f"{drawing_id}_{timestamp}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_key = str(file_path.relative_to(UPLOAD_DIR))
        
        # Update drawing
        await db.drawings.update_one(
            {"id": drawing_id},
            {"$set": {"s3_key": file_key, "status": "review"}}
        )
        
        return {
            "message": "Drawing uploaded successfully",
            "file_key": file_key
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.post("/drawings/{drawing_id}/ai-review")
async def ai_review_drawing(drawing_id: str, current_user: User = Depends(get_current_user)):
    drawing = await db.drawings.find_one({"id": drawing_id})
    if not drawing:
        raise HTTPException(status_code=404, detail="Drawing not found")
    
    if not drawing.get('s3_key'):
        raise HTTPException(status_code=400, detail="No drawing file uploaded")
    
    try:
        # Get file from local storage
        file_path = UPLOAD_DIR / drawing['s3_key']
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Drawing file not found")
        
        # AI Review using GPT-5
        llm_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=llm_key,
            session_id=f"drawing_review_{drawing_id}",
            system_message="You are an expert architectural drawing reviewer. Analyze the drawing and provide detailed feedback on compliance, quality, and potential issues."
        ).with_model("openai", "gpt-5")
        
        file_content = FileContentWithMimeType(
            file_path=str(file_path),
            mime_type="application/pdf"
        )
        
        message = UserMessage(
            text=f"Please review this {drawing['category']} drawing named '{drawing['name']}'. Check for: 1) Technical accuracy 2) Compliance with standards 3) Clarity and completeness 4) Potential issues or improvements",
            file_contents=[file_content]
        )
        
        ai_response = await chat.send_message(message)
        
        # Update drawing with AI review
        review_data = {
            "review_text": ai_response,
            "reviewed_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.drawings.update_one(
            {"id": drawing_id},
            {"$set": {"ai_review": review_data}}
        )
        
        return {
            "message": "AI review completed",
            "review": review_data
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI review failed: {str(e)}")

@api_router.patch("/drawings/{drawing_id}")
async def update_drawing(drawing_id: str, updates: dict, current_user: User = Depends(get_current_user)):
    if 'issue_date' in updates and updates['issue_date']:
        updates['issue_date'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.drawings.update_one({"id": drawing_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Drawing not found")
    return {"message": "Drawing updated successfully"}


@api_router.patch("/drawings/{drawing_id}/mark-not-applicable")
async def mark_drawing_not_applicable(
    drawing_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a drawing as not applicable - removes from list and creates next drawing"""
    try:
        # Get the drawing first
        drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
        if not drawing:
            raise HTTPException(status_code=404, detail="Drawing not found")
        
        # Mark as N/A
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {"is_not_applicable": True, "updated_at": datetime.now(timezone.utc)}}
        )
        
        # Now create the next drawing to replace it (maintain 3 visible drawings)
        project_id = drawing.get('project_id')
        category = drawing.get('category')
        current_sequence = drawing.get('sequence_number')
        
        if project_id and category and current_sequence:
            # Get template drawings
            template_drawings = get_template_drawings(category)
            
            # Find the highest sequence number currently in the project
            all_drawings = await db.project_drawings.find({
                "project_id": project_id,
                "category": category,
                "deleted_at": None
            }, {"_id": 0, "sequence_number": 1}).sort("sequence_number", -1).limit(1).to_list(1)
            
            if all_drawings:
                max_sequence = all_drawings[0]['sequence_number']
                next_sequence = max_sequence + 1
                
                # Check if template has this drawing
                if template_drawings and next_sequence <= len(template_drawings):
                    drawing_name = template_drawings[next_sequence - 1]
                    
                    # Create the new drawing
                    new_drawing = ProjectDrawing(
                        project_id=project_id,
                        category=category,
                        name=drawing_name,
                        status=DrawingStatus.PLANNED,
                        due_date=None,
                        is_issued=False,
                        revision_count=0,
                        sequence_number=next_sequence,
                        is_active=False,
                        assigned_to=drawing.get('assigned_to'),
                        priority="medium"
                    )
                    new_drawing_dict = new_drawing.model_dump()
                    
                    # Convert datetimes
                    for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                        if new_drawing_dict.get(field):
                            new_drawing_dict[field] = new_drawing_dict[field].isoformat() if isinstance(new_drawing_dict[field], datetime) else new_drawing_dict[field]
                    
                    await db.project_drawings.insert_one(new_drawing_dict)
                    logger.info(f"Auto-created drawing #{next_sequence} to replace N/A drawing")
        
        return {"message": "Drawing marked as not applicable"}
    except Exception as e:
        logger.error(f"Error marking drawing as N/A: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/dashboard/team-member-stats")
async def get_team_member_dashboard_stats(
    current_user: User = Depends(get_current_user)
):
    """Get dashboard statistics for team members with proper drawing status logic"""
    try:
        # Get all projects assigned to this team member
        projects = await db.projects.find({
            "$or": [
                {"team_leader_id": current_user.id},
                {"lead_architect_id": current_user.id}
            ],
            "deleted_at": None,
            "archived": {"$ne": True}
        }, {"_id": 0}).to_list(1000)
        
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        due_drawings = []
        upcoming_drawings = []
        overdue_count = 0
        due_today_count = 0
        
        for project in projects:
            # Get all drawings for this project, sorted by sequence
            drawings = await db.project_drawings.find({
                "project_id": project["id"],
                "deleted_at": None,
                "is_not_applicable": {"$ne": True}
            }, {"_id": 0}).sort("sequence_number", 1).to_list(1000)
            
            if not drawings:
                continue
            
            # Find the last issued drawing (without pending revision)
            last_issued_index = -1
            for i, drawing in enumerate(drawings):
                if drawing.get("is_issued") and not drawing.get("has_pending_revision"):
                    last_issued_index = i
            
            # Determine due and upcoming drawings with new progressive disclosure logic
            for i, drawing in enumerate(drawings):
                drawing_data = {**drawing, "project": project}
                
                # Drawing is DUE if:
                # 1. It has a pending revision (ALWAYS due - highest priority)
                # 2. It has is_active = True (current sequential drawing)
                # 3. It has a due_date set (means it's ready to be worked on)
                
                # Drawing is UPCOMING if:
                # 1. It has no due_date yet
                # 2. It's not issued
                # 3. It's after the currently due drawing
                
                is_due = False
                is_upcoming = False
                
                if drawing.get("has_pending_revision"):
                    # Revisions are ALWAYS due, regardless of sequence
                    is_due = True
                elif not drawing.get("is_issued"):
                    # Check if this drawing is currently due
                    if drawing.get("is_active") or drawing.get("due_date"):
                        # Drawing has been activated or has a due date = DUE
                        is_due = True
                    else:
                        # No due date, not active, not issued = UPCOMING
                        is_upcoming = True
                
                if is_due:
                    due_drawings.append(drawing_data)
                    
                    # Check if overdue or due today
                    if drawing.get("due_date"):
                        if isinstance(drawing["due_date"], str):
                            due_date = datetime.fromisoformat(drawing["due_date"].replace('Z', '+00:00'))
                        else:
                            due_date = drawing["due_date"]
                        
                        # Ensure timezone awareness
                        if due_date.tzinfo is None:
                            due_date = due_date.replace(tzinfo=timezone.utc)
                        
                        due_date = due_date.replace(hour=0, minute=0, second=0, microsecond=0)
                        
                        if due_date < today:
                            overdue_count += 1
                        elif due_date == today:
                            due_today_count += 1
                elif is_upcoming:
                    # Upcoming drawings (prepare in advance)
                    upcoming_drawings.append(drawing_data)
        
        # Sort due drawings by due date (earliest first)
        due_drawings.sort(key=lambda d: d.get("due_date") or "9999-12-31")
        
        return {
            "due_drawings": due_drawings,
            "upcoming_drawings": upcoming_drawings,
            "overdue_count": overdue_count,
            "due_today_count": due_today_count,
            "total_due": len(due_drawings),
            "total_projects": len(projects)
        }
    except Exception as e:
        logger.error(f"Dashboard stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== TASK ROUTES ====================

@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    task = Task(
        project_id=task_data.project_id,
        title=task_data.title,
        description=task_data.description,
        assigned_to=task_data.assigned_to,
        due_date=datetime.fromisoformat(task_data.due_date) if task_data.due_date else None,
        priority=task_data.priority,
        status="open",
        created_by=current_user.id
    )
    
    task_dict = task.model_dump()
    task_dict['created_at'] = task_dict['created_at'].isoformat()
    if task_dict['due_date']:
        task_dict['due_date'] = task_dict['due_date'].isoformat()
    
    await db.tasks.insert_one(task_dict)
    return task

@api_router.get("/projects/{project_id}/tasks", response_model=List[Task])
async def get_project_tasks(project_id: str, current_user: User = Depends(get_current_user)):
    tasks = await db.tasks.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    for task in tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
        if task.get('due_date') and isinstance(task['due_date'], str):
            task['due_date'] = datetime.fromisoformat(task['due_date'])
        if task.get('resolved_at') and isinstance(task['resolved_at'], str):
            task['resolved_at'] = datetime.fromisoformat(task['resolved_at'])
    return tasks

@api_router.get("/tasks", response_model=List[Task])
async def get_all_tasks(current_user: User = Depends(get_current_user)):
    tasks = await db.tasks.find({}, {"_id": 0}).to_list(1000)
    for task in tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
        if task.get('due_date') and isinstance(task['due_date'], str):
            task['due_date'] = datetime.fromisoformat(task['due_date'])
        if task.get('resolved_at') and isinstance(task['resolved_at'], str):
            task['resolved_at'] = datetime.fromisoformat(task['resolved_at'])
    return tasks

@api_router.patch("/tasks/{task_id}")
async def update_task(task_id: str, updates: dict, current_user: User = Depends(get_current_user)):
    if updates.get('status') == 'resolved':
        updates['resolved_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.tasks.update_one({"id": task_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task updated successfully"}


# ==================== REVISION ROUTES ====================

@api_router.post("/revisions", response_model=Revision)
async def create_revision(revision_data: RevisionCreate, current_user: User = Depends(get_current_user)):
    # Get current revision count
    count = await db.revisions.count_documents({"project_id": revision_data.project_id, "revision_type": revision_data.revision_type})
    
    revision = Revision(
        project_id=revision_data.project_id,
        revision_type=revision_data.revision_type,
        revision_number=count + 1,
        description=revision_data.description
    )
    
    revision_dict = revision.model_dump()
    revision_dict['date'] = revision_dict['date'].isoformat()
    
    await db.revisions.insert_one(revision_dict)
    
    # Update project revision count
    if revision_data.revision_type == "layout":
        await db.projects.update_one(
            {"id": revision_data.project_id},
            {"$inc": {"plan_revisions": 1}}
        )
    
    return revision

@api_router.get("/projects/{project_id}/revisions", response_model=List[Revision])
async def get_project_revisions(project_id: str, current_user: User = Depends(get_current_user)):
    revisions = await db.revisions.find({"project_id": project_id}, {"_id": 0}).sort("date", -1).to_list(1000)
    for revision in revisions:
        if isinstance(revision.get('date'), str):
            revision['date'] = datetime.fromisoformat(revision['date'])
    return revisions


# ==================== ACCOUNTING ROUTES (Moved to routes/accounting.py) ====================

# ==================== DRAWING TEMPLATE ROUTES ====================

@api_router.post("/drawing-templates", response_model=DrawingTemplate)
async def create_drawing_template(template_data: DrawingTemplateCreate, current_user: User = Depends(require_owner)):
    template = DrawingTemplate(**template_data.model_dump())
    template_dict = template.model_dump()
    await db.drawing_templates.insert_one(template_dict)
    return template

@api_router.get("/drawing-templates", response_model=List[DrawingTemplate])
async def get_drawing_templates(current_user: User = Depends(get_current_user)):
    templates = await db.drawing_templates.find({}, {"_id": 0}).sort("order", 1).to_list(1000)
    return templates

@api_router.delete("/drawing-templates/{template_id}")
async def delete_drawing_template(template_id: str, current_user: User = Depends(require_owner)):
    result = await db.drawing_templates.delete_one({"id": template_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"message": "Template deleted successfully"}


# ==================== DASHBOARD/STATS ROUTES ====================

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    total_projects = await db.projects.count_documents({"deleted_at": None})
    active_projects = await db.projects.count_documents({
        "status": {"$nin": ["Closed"]},
        "deleted_at": None
    })
    total_clients = await db.clients.count_documents({"deleted_at": None})
    pending_tasks = await db.tasks.count_documents({
        "status": {"$in": ["Open", "InProgress"]}
    })
    overdue_drawings = await db.project_drawings.count_documents({
        "status": {"$in": ["Planned", "InProgress"]},
        "due_date": {"$lt": datetime.now(timezone.utc).isoformat()}
    })
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_clients": total_clients,
        "pending_tasks": pending_tasks,
        "overdue_drawings": overdue_drawings
    }

@api_router.get("/reminders/pending")
async def get_pending_reminders(current_user: User = Depends(get_current_user)):
    now = datetime.now(timezone.utc)
    
    # Get overdue tasks
    overdue_tasks = await db.tasks.find({
        "status": {"$in": ["open", "in_progress"]},
        "due_date": {"$lt": now.isoformat()}
    }, {"_id": 0}).to_list(100)
    
    # Get pending drawings
    pending_drawings = await db.drawings.find({
        "status": {"$in": ["pending", "in_progress"]}
    }, {"_id": 0}).to_list(100)
    
    # Get projects needing attention
    projects_needing_attention = await db.projects.find({
        "plan_finalized": False,
        "created_at": {"$lt": (now - timedelta(days=14)).isoformat()}
    }, {"_id": 0}).to_list(100)
    
    return {
        "overdue_tasks": len(overdue_tasks),
        "pending_drawings": len(pending_drawings),
        "projects_needing_attention": len(projects_needing_attention),
        "details": {
            "overdue_tasks": overdue_tasks[:5],
            "pending_drawings": pending_drawings[:5],
            "projects_needing_attention": projects_needing_attention[:5]
        }
    }


# ==================== FILE MANAGEMENT ====================

@api_router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    category: str = "general",
    current_user: User = Depends(get_current_user)
):
    try:
        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(status_code=413, detail="File size exceeds maximum")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        category_dir = UPLOAD_DIR / "files" / category / (project_id or "general")
        category_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = category_dir / f"{timestamp}_{file.filename}"
        
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        file_key = str(file_path.relative_to(UPLOAD_DIR))
        
        return {
            "message": "File uploaded successfully",
            "file_key": file_key,
            "size": file_size
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/files/download/{file_key:path}")
async def download_file(file_key: str, current_user: User = Depends(get_current_user)):
    try:
        file_path = UPLOAD_DIR / file_key
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")


# ==================== NEW ARCHFLOW PROJECTS MODULE ====================

# Consultants
@api_router.post("/consultants", response_model=Consultant)
async def create_consultant(consultant_data: ConsultantCreate, current_user: User = Depends(get_current_user)):
    consultant = Consultant(**consultant_data.model_dump())
    consultant_dict = consultant.model_dump()
    consultant_dict['created_at'] = consultant_dict['created_at'].isoformat()
    consultant_dict['updated_at'] = consultant_dict['updated_at'].isoformat()
    await db.consultants.insert_one(consultant_dict)
    return consultant

@api_router.get("/consultants", response_model=List[Consultant])
async def get_consultants(current_user: User = Depends(get_current_user)):
    consultants = await db.consultants.find({"deleted_at": None}, {"_id": 0}).to_list(1000)
    
    approved_consultants = []
    for c in consultants:
        # Check if consultant has approved user account
        if c.get('user_id'):
            user = await db.users.find_one(
                {"id": c['user_id']}, 
                {"_id": 0, "approval_status": 1}
            )
            # Only include if user is approved
            if not (user and user.get('approval_status') == 'approved'):
                continue
        
        # Process dates
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
        if isinstance(c.get('updated_at'), str):
            c['updated_at'] = datetime.fromisoformat(c['updated_at'])
        
        # Auto-fix legacy "Structural" type to "Structure"
        if c.get('type') == 'Structural':
            c['type'] = 'Structure'
            await db.consultants.update_one(
                {"id": c['id']},
                {"$set": {"type": "Structure"}}
            )
        
        approved_consultants.append(c)
    
    return approved_consultants

@api_router.put("/consultants/{consultant_id}", response_model=Consultant)
async def update_consultant(
    consultant_id: str,
    consultant_data: ConsultantCreate,
    current_user: User = Depends(get_current_user)
):
    """Update consultant"""
    existing = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    update_dict = consultant_data.model_dump()
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.consultants.update_one(
        {"id": consultant_id},
        {"$set": update_dict}
    )
    
    updated = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    if isinstance(updated.get('updated_at'), str):
        updated['updated_at'] = datetime.fromisoformat(updated['updated_at'])
    
    return updated

@api_router.delete("/consultants/{consultant_id}")
async def delete_consultant(
    consultant_id: str,
    current_user: User = Depends(get_current_user)
):
    """HARD DELETE consultant - Only if no active projects exist"""
    existing = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    # Check for active projects where this consultant is assigned
    active_projects = await db.projects.find({
        "consultants": consultant_id,
        "$or": [
            {"archived": False},
            {"archived": {"$exists": False}}
        ]
    }, {"_id": 0, "name": 1}).to_list(10)
    
    if active_projects:
        project_names = ", ".join([p.get('name', 'Unnamed') for p in active_projects])
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete consultant. Active projects exist: {project_names}. Please archive these projects first."
        )
    
    # Get consultant info for cleanup
    consultant_email = existing.get('email')
    consultant_phone = existing.get('phone')
    consultant_user_id = existing.get('user_id')
    
    # HARD DELETE from consultants collection
    await db.consultants.delete_one({"id": consultant_id})
    logger.info(f"Hard deleted consultant: {existing.get('name')}")
    
    # Delete the associated user account (if exists)
    if consultant_user_id:
        await db.users.delete_one({"id": consultant_user_id})
        logger.info(f"Hard deleted user account for consultant: {existing.get('name')}")
    
    # Clean up related records to allow fresh re-registration
    if consultant_email:
        await db.pending_registrations.delete_many({"email": consultant_email})
        await db.invitations.delete_many({"email": consultant_email})
        await db.team_verifications.delete_many({"email": consultant_email})
    
    if consultant_phone:
        # Normalize phone for cleanup
        phone_digits = ''.join(filter(str.isdigit, consultant_phone))[-10:]
        await db.invitations.delete_many({"phone": {"$regex": phone_digits}})
        await db.pending_registrations.delete_many({"phone": {"$regex": phone_digits}})
    
    return {"message": "Consultant permanently deleted. They can now be invited fresh."}

# Checklist Presets
@api_router.get("/checklist-presets", response_model=List[ChecklistPreset])
async def get_checklist_presets(current_user: User = Depends(get_current_user)):
    presets = await db.checklist_presets.find({}, {"_id": 0}).to_list(100)
    return presets

# Drawing Types
@api_router.get("/drawing-types", response_model=List[DrawingType])
async def get_drawing_types(current_user: User = Depends(get_current_user)):
    types = await db.drawing_types.find({}, {"_id": 0}).to_list(1000)
    return types

# Project Drawings
@api_router.post("/projects/{project_id}/drawings", response_model=ProjectDrawing)
async def create_project_drawing(project_id: str, drawing_data: ProjectDrawingCreate, current_user: User = Depends(get_current_user)):
    drawing = ProjectDrawing(**drawing_data.model_dump())
    drawing_dict = drawing.model_dump()
    drawing_dict['created_at'] = drawing_dict['created_at'].isoformat()
    drawing_dict['updated_at'] = drawing_dict['updated_at'].isoformat()
    if drawing_dict.get('due_date'):
        drawing_dict['due_date'] = drawing_dict['due_date'].isoformat()
    await db.project_drawings.insert_one(drawing_dict)
    return drawing

@api_router.put("/drawings/{drawing_id}/status")
async def update_drawing_status(drawing_id: str, status: DrawingStatus, current_user: User = Depends(get_current_user)):
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Status updated"}

# Auto-generate drawings from preset
@api_router.post("/projects/{project_id}/generate-from-preset")
async def generate_drawings_from_preset(
    project_id: str,
    preset_id: str,
    current_user: User = Depends(get_current_user)
):
    # Get preset and its checklist items
    preset = await db.checklist_presets.find_one({"id": preset_id}, {"_id": 0})
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    checklist_items = await db.checklist_items.find({"checklist_preset_id": preset_id}, {"_id": 0}).to_list(100)
    
    # Get drawing types
    generated = []
    today = datetime.now(timezone.utc)
    
    for item in checklist_items:
        drawing_type = await db.drawing_types.find_one({"id": item["drawing_type_id"]}, {"_id": 0})
        if drawing_type:
            # Calculate staggered due date
            stagger_days = item["sequence"] // 10
            due_date = today + timedelta(days=drawing_type["default_due_offset_days"] + stagger_days)
            
            drawing = ProjectDrawing(
                project_id=project_id,
                drawing_type_id=drawing_type["id"],
                sequence=item["sequence"],
                status=DrawingStatus.PLANNED,
                due_date=due_date
            )
            
            drawing_dict = drawing.model_dump()
            drawing_dict['created_at'] = drawing_dict['created_at'].isoformat()
            drawing_dict['updated_at'] = drawing_dict['updated_at'].isoformat()
            drawing_dict['due_date'] = drawing_dict['due_date'].isoformat()
            
            await db.project_drawings.insert_one(drawing_dict)
            generated.append(drawing_dict)
    
    return {"message": f"Generated {len(generated)} drawings", "count": len(generated)}

# Tasks
@api_router.get("/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str, current_user: User = Depends(get_current_user)):
    tasks = await db.tasks.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    for t in tasks:
        if isinstance(t.get('created_at'), str):
            t['created_at'] = datetime.fromisoformat(t['created_at'])
        if isinstance(t.get('updated_at'), str):
            t['updated_at'] = datetime.fromisoformat(t['updated_at'])
        if isinstance(t.get('due_date'), str):
            t['due_date'] = datetime.fromisoformat(t['due_date'])
    return tasks

@api_router.post("/tasks", response_model=Task)
async def create_task(task_data: TaskCreate, current_user: User = Depends(get_current_user)):
    task = Task(**task_data.model_dump())
    task_dict = task.model_dump()
    task_dict['created_at'] = task_dict['created_at'].isoformat()
    task_dict['updated_at'] = task_dict['updated_at'].isoformat()
    if task_dict.get('due_date'):
        task_dict['due_date'] = task_dict['due_date'].isoformat()
    await db.tasks.insert_one(task_dict)
    return task

# Site Visits
@api_router.post("/site-visits", response_model=SiteVisit)
async def create_site_visit(visit_data: SiteVisitCreate, current_user: User = Depends(get_current_user)):
    visit = SiteVisit(
        project_id=visit_data.project_id,
        visit_date=datetime.fromisoformat(visit_data.visit_date),
        notes=visit_data.notes,
        created_by_id=current_user.id
    )
    visit_dict = visit.model_dump()
    visit_dict['visit_date'] = visit_dict['visit_date'].isoformat()
    visit_dict['created_at'] = visit_dict['created_at'].isoformat()
    await db.site_visits.insert_one(visit_dict)
    return visit

# Site Issues
@api_router.get("/projects/{project_id}/issues")
async def get_project_issues(project_id: str, current_user: User = Depends(get_current_user)):
    issues = await db.site_issues.find({"project_id": project_id}, {"_id": 0}).to_list(1000)
    for i in issues:
        if isinstance(i.get('created_at'), str):
            i['created_at'] = datetime.fromisoformat(i['created_at'])
        if isinstance(i.get('updated_at'), str):
            i['updated_at'] = datetime.fromisoformat(i['updated_at'])
        if isinstance(i.get('due_date'), str):
            i['due_date'] = datetime.fromisoformat(i['due_date'])
    return issues

@api_router.post("/issues", response_model=SiteIssue)
async def create_site_issue(issue_data: SiteIssueCreate, current_user: User = Depends(get_current_user)):
    issue = SiteIssue(**issue_data.model_dump())
    issue_dict = issue.model_dump()
    issue_dict['created_at'] = issue_dict['created_at'].isoformat()
    issue_dict['updated_at'] = issue_dict['updated_at'].isoformat()
    if issue_dict.get('due_date'):
        issue_dict['due_date'] = issue_dict['due_date'].isoformat()
    await db.site_issues.insert_one(issue_dict)
    return issue
# Include the router in the main app
# ==================== TASK MANAGEMENT & DASHBOARD ====================

@api_router.get("/dashboard/weekly-progress/{user_id}")
async def get_weekly_progress(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get weekly task progress for a team member
    - Calculates progress based on drawing complexity (Simple=1, Medium=2, Complex=3)
    - Excludes blocked drawings
    - Separates ad-hoc tasks
    """
    try:
        # Only owner can view others' progress, users can view their own
        if current_user.id != user_id and current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Access denied")
        
        from datetime import datetime, timedelta
        
        # Get current week start (Monday)
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())  # Monday
        week_start = week_start.replace(hour=0, minute=1, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        
        # Get current ISO week
        current_week = week_start.strftime("%Y-W%W")
        
        # Find all projects where user is assigned as team leader
        projects = await db.projects.find(
            {
                "lead_architect_id": user_id,
                "deleted_at": None
            },
            {"_id": 0}
        ).to_list(100)
        
        project_ids = [p["id"] for p in projects]
        
        # Get all pending drawings for these projects (not issued, not blocked)
        drawings = await db.project_drawings.find(
            {
                "project_id": {"$in": project_ids},
                "is_issued": False,
                "is_blocked": False,
                "deleted_at": None
            },
            {"_id": 0}
        ).to_list(1000)
        
        # Get all ad-hoc tasks assigned this week
        ad_hoc_tasks = await db.tasks.find(
            {
                "assigned_to_id": user_id,
                "is_ad_hoc": True,
                "week_assigned": current_week,
                "status": {"$nin": ["Closed", "Resolved"]},
                "deleted_at": None
            },
            {"_id": 0}
        ).to_list(100)
        
        # Calculate drawing points
        complexity_points = {"Simple": 1, "Medium": 2, "Complex": 3}
        
        total_points = 0
        completed_points = 0
        
        projects_progress = []
        
        for project in projects:
            project_drawings = [d for d in drawings if d["project_id"] == project["id"]]
            
            if not project_drawings:
                continue
            
            project_total = 0
            project_completed = 0
            drawing_details = []
            
            for drawing in project_drawings:
                points = complexity_points.get(drawing.get("complexity", "Medium"), 2)
                project_total += points
                total_points += points
                
                if drawing.get("is_issued") or drawing.get("is_approved"):
                    project_completed += points
                    completed_points += points
                    status = "✅ Completed"
                elif drawing.get("under_review"):
                    status = "🟡 Under Review"
                elif drawing.get("file_url"):
                    status = "🟢 Uploaded"
                else:
                    status = "🔴 Pending"
                
                drawing_details.append({
                    "id": drawing["id"],
                    "name": drawing["name"],
                    "category": drawing["category"],
                    "complexity": drawing.get("complexity", "Medium"),
                    "points": points,
                    "status": status,
                    "due_date": drawing.get("due_date"),
                    "is_completed": drawing.get("is_issued") or drawing.get("is_approved")
                })
            
            project_progress = (project_completed / project_total * 100) if project_total > 0 else 0
            
            projects_progress.append({
                "project_id": project["id"],
                "project_title": project["title"],
                "project_code": project["code"],
                "client_name": project.get("client_name"),
                "total_points": project_total,
                "completed_points": project_completed,
                "progress_percentage": round(project_progress, 1),
                "drawings": drawing_details
            })
        
        # Calculate overall progress
        overall_progress = (completed_points / total_points * 100) if total_points > 0 else 0
        
        # Process ad-hoc tasks
        ad_hoc_completed = len([t for t in ad_hoc_tasks if t.get("status") in ["Closed", "Resolved"]])
        ad_hoc_total = len(ad_hoc_tasks)
        ad_hoc_progress = (ad_hoc_completed / ad_hoc_total * 100) if ad_hoc_total > 0 else 0
        
        ad_hoc_details = []
        for task in ad_hoc_tasks:
            # Calculate urgency
            due = task.get("due_date_time")
            urgency = "🔴 URGENT"
            if due:
                due_dt = datetime.fromisoformat(due) if isinstance(due, str) else due
                hours_until_due = (due_dt - now).total_seconds() / 3600
                if hours_until_due > 48:
                    urgency = "📌 NORMAL"
                elif hours_until_due > 24:
                    urgency = "🟡 SOON"
                elif hours_until_due > 2:
                    urgency = "🟠 TODAY"
                else:
                    urgency = "🔴 URGENT"
            
            ad_hoc_details.append({
                "id": task["id"],
                "title": task["title"],
                "description": task.get("description"),
                "priority": task.get("priority"),
                "status": task.get("status"),
                "due_date_time": task.get("due_date_time"),
                "urgency": urgency,
                "is_completed": task.get("status") in ["Closed", "Resolved"],
                "project_id": task.get("project_id"),
                "is_ad_hoc": task.get("is_ad_hoc", True)
            })
        
        return {
            "user_id": user_id,
            "week_start": week_start.isoformat(),
            "week_end": week_end.isoformat(),
            "current_week": current_week,
            "overall": {
                "total_points": total_points,
                "completed_points": completed_points,
                "progress_percentage": round(overall_progress, 1),
                "projects_count": len(projects_progress)
            },
            "projects": projects_progress,
            "ad_hoc_tasks": {
                "total": ad_hoc_total,
                "completed": ad_hoc_completed,
                "progress_percentage": round(ad_hoc_progress, 1),
                "tasks": ad_hoc_details
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get weekly progress error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/tasks/ad-hoc")
async def create_ad_hoc_task(
    task: TaskCreate,
    current_user: User = Depends(get_current_user)
):
    """Create an ad-hoc task (owner only)"""
    try:
        # Only owner can create ad-hoc tasks
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Only owner can create ad-hoc tasks")
        
        from datetime import datetime
        
        # Get current ISO week
        now = datetime.now(timezone.utc)
        week_start = now - timedelta(days=now.weekday())
        current_week = week_start.strftime("%Y-W%W")
        
        # Get assigned user info
        assigned_user = await db.users.find_one(
            {"id": task.assigned_to_id},
            {"_id": 0, "name": 1, "email": 1, "mobile": 1}
        )
        
        if not assigned_user:
            raise HTTPException(status_code=404, detail="Assigned user not found")
        
        # Create task
        task_dict = task.model_dump()
        task_dict["id"] = str(uuid.uuid4())
        task_dict["created_by_id"] = current_user.id
        task_dict["created_by_name"] = current_user.name
        task_dict["assigned_to_name"] = assigned_user.get("name")
        task_dict["is_ad_hoc"] = True
        task_dict["week_assigned"] = current_week
        task_dict["created_at"] = datetime.now(timezone.utc).isoformat()
        task_dict["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.tasks.insert_one(task_dict)
        
        # Create in-app notification
        try:
            notification = {
                "id": str(uuid.uuid4()),
                "user_id": task.assigned_to_id,
                "type": "task_assigned",
                "title": "New Task Assigned",
                "message": f"{current_user.name} assigned you a task: {task.title}",
                "related_id": task_dict["id"],
                "related_type": "task",
                "project_id": task.project_id,
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by_id": current_user.id,
                "created_by_name": current_user.name
            }
            await db.notifications.insert_one(notification)
        except Exception as e:
            logger.warning(f"Failed to create in-app notification: {e}")
        
        # Send WhatsApp notification
        try:
            from notification_triggers import notify_task_assigned
            await notify_task_assigned(
                task_dict["id"],
                assigned_user.get("name"),
                task.title,
                task.due_date_time
            )
        except Exception as e:
            logger.warning(f"Failed to send WhatsApp notification: {e}")
        
        # Return clean response without MongoDB ObjectId
        response_dict = {
            "id": task_dict["id"],
            "title": task_dict["title"],
            "description": task_dict.get("description"),
            "assigned_to_id": task_dict["assigned_to_id"],
            "assigned_to_name": task_dict["assigned_to_name"],
            "due_date_time": task_dict["due_date_time"],
            "priority": task_dict["priority"],
            "category": task_dict.get("category"),
            "status": task_dict["status"],
            "is_ad_hoc": task_dict["is_ad_hoc"],
            "week_assigned": task_dict["week_assigned"],
            "created_by_id": task_dict["created_by_id"],
            "created_by_name": task_dict["created_by_name"],
            "created_at": task_dict["created_at"],
            "updated_at": task_dict["updated_at"]
        }
        
        return response_dict
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create ad-hoc task error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/tasks/{task_id}/complete")
async def mark_task_complete(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a task as complete"""
    try:
        task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Only assigned user or owner can complete
        if task["assigned_to_id"] != current_user.id and current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Access denied")
        
        await db.tasks.update_one(
            {"id": task_id},
            {"$set": {
                "status": "Resolved",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"success": True, "message": "Task marked as complete"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark task complete error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== IN-APP NOTIFICATION ENDPOINTS ====================

@api_router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user),
    unread_only: bool = False
):
    """Get notifications for the current user"""
    try:
        query = {"user_id": current_user.id}
        if unread_only:
            query["is_read"] = False
        
        notifications = await db.notifications.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).limit(50).to_list(50)
        
        return notifications
    
    except Exception as e:
        logger.error(f"Get notifications error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read"""
    try:
        result = await db.notifications.update_one(
            {"id": notification_id, "user_id": current_user.id},
            {"$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Mark notification read error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/notifications/mark-all-read")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user)
):
    """Mark all notifications as read for current user"""
    try:
        await db.notifications.update_many(
            {"user_id": current_user.id, "is_read": False},
            {"$set": {
                "is_read": True,
                "read_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"success": True}
    
    except Exception as e:
        logger.error(f"Mark all notifications read error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/notifications/unread-count")
async def get_unread_count(
    user_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Get count of unread notifications"""
    try:
        # Use provided user_id or current_user.id
        target_user_id = user_id if user_id else current_user.id
        
        count = await db.notifications.count_documents({
            "user_id": target_user_id,
            "read": False
        })
        
        return {"unread_count": count, "count": count}  # Return both for compatibility
    
    except Exception as e:
        logger.error(f"Get unread count error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))



@api_router.put("/drawings/{drawing_id}/block")
async def block_drawing(
    drawing_id: str,
    data: dict,
    current_user: User = Depends(get_current_user)
):
    """Block a drawing (exclude from progress tracking)"""
    try:
        # Only owner or team leader can block
        if current_user.role not in ["owner", "team_leader"]:
            raise HTTPException(status_code=403, detail="Access denied")
        
        await db.project_drawings.update_one(
            {"id": drawing_id},
            {"$set": {
                "is_blocked": data.get("is_blocked", True),
                "blocked_reason": data.get("blocked_reason"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        return {"success": True}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Block drawing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ACCOUNTING ENDPOINTS (Moved to routes/accounting.py) ====================


@api_router.get("/dashboard/team-overview")
async def get_team_overview(
    current_user: User = Depends(get_current_user)
):
    """Get overview of all team members' progress (owner only)"""
    try:
        # Only owner can view team overview
        if current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get all approved users excluding owner, client, contractor, consultant, vendor
        # This includes all team member roles (architects, designers, drafters, etc.)
        team_members = await db.users.find(
            {
                "role": {"$nin": ["owner", "client", "contractor", "consultant", "vendor"]},
                "approval_status": "approved",
                "is_owner": {"$ne": True}
            },
            {"_id": 0, "id": 1, "name": 1, "role": 1, "email": 1}
        ).to_list(100)
        
        team_progress = []
        
        for member in team_members:
            # Get their weekly progress
            progress_data = await get_weekly_progress(member["id"], current_user)
            
            team_progress.append({
                "user_id": member["id"],
                "name": member["name"],
                "role": member["role"],
                "email": member["email"],
                "overall_progress": progress_data["overall"]["progress_percentage"],
                "total_points": progress_data["overall"]["total_points"],
                "completed_points": progress_data["overall"]["completed_points"],
                "projects_count": progress_data["overall"]["projects_count"],
                "ad_hoc_tasks": progress_data["ad_hoc_tasks"]["total"],
                "status": "🟢 On Track" if progress_data["overall"]["progress_percentage"] >= 75 else 
                         "🟡 Needs Attention" if progress_data["overall"]["progress_percentage"] >= 50 else 
                         "🔴 Behind Schedule"
            })
        
        # Sort by progress percentage
        team_progress.sort(key=lambda x: x["overall_progress"], reverse=True)
        
        return {
            "team_members": team_progress,
            "total_team_size": len(team_progress),
            "avg_progress": sum([t["overall_progress"] for t in team_progress]) / len(team_progress) if team_progress else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get team overview error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/dashboard/historical/{user_id}")
async def get_historical_progress(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get 4 weeks + monthly + yearly progress history"""
    try:
        # Only owner can view others' history, users can view their own
        if current_user.id != user_id and current_user.role != "owner":
            raise HTTPException(status_code=403, detail="Access denied")
        
        from datetime import datetime, timedelta
        
        # This would require storing weekly snapshots
        # For now, return placeholder structure
        # TODO: Implement weekly snapshot storage in weekly reset job
        
        now = datetime.now(timezone.utc)
        
        # Last 4 weeks
        weekly_history = []
        for i in range(4):
            week_start = now - timedelta(weeks=i+1, days=now.weekday())
            weekly_history.append({
                "week": week_start.strftime("%Y-W%W"),
                "week_start": week_start.isoformat(),
                "progress_percentage": 0,  # TODO: Fetch from snapshots
                "total_points": 0,
                "completed_points": 0
            })
        
        # Monthly data (current financial year)
        # Financial year: April to March
        current_month = now.month
        if current_month >= 4:
            fy_start_year = now.year
        else:
            fy_start_year = now.year - 1
        
        monthly_history = []
        for month_offset in range(12):
            month_date = datetime(fy_start_year, 4, 1) + timedelta(days=30*month_offset)
            if month_date > now:
                break
            monthly_history.append({
                "month": month_date.strftime("%B %Y"),
                "progress_percentage": 0,  # TODO: Implement
                "drawings_completed": 0,
                "projects_handled": 0
            })
        
        # Yearly summary
        yearly_summary = {
            "financial_year": f"{fy_start_year}-{fy_start_year+1}",
            "total_drawings_completed": 0,  # TODO: Calculate
            "total_projects": 0,
            "avg_completion_rate": 0,
            "consistency_score": 0
        }
        
        return {"status": "placeholder"}
    except Exception as e:
        logger.error(f"Get notification stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ===============================
# CO-CLIENTS / ASSOCIATE CLIENTS
# ===============================

@api_router.post("/projects/{project_id}/co-clients")
async def add_co_client(
    project_id: str,
    co_client: CoClientCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a co-client/associate client to a project"""
    try:
        # Verify project exists and user has access
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Only owner or main client can add co-clients
        if not current_user.is_owner and current_user.id != project.get('client_id'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Create co-client record
        co_client_id = str(uuid.uuid4())
        co_client_data = {
            "id": co_client_id,
            "project_id": project_id,
            "main_client_id": project.get('client_id'),
            "name": co_client.name,
            "email": co_client.email,
            "phone": co_client.phone,
            "relationship": co_client.relationship,
            "notes": co_client.notes,
            "created_at": datetime.now(timezone.utc),
            "created_by": current_user.id
        }
        
        await db.co_clients.insert_one(co_client_data)
        
        # Fetch the inserted document without _id
        inserted_co_client = await db.co_clients.find_one({"id": co_client_id}, {"_id": 0})
        
        # Convert datetime to ISO string for JSON serialization
        if inserted_co_client and inserted_co_client.get('created_at'):
            inserted_co_client['created_at'] = inserted_co_client['created_at'].isoformat()
        
        return {"message": "Co-client added successfully", "co_client": inserted_co_client}
        
    except Exception as e:
        logger.error(f"Add co-client error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/projects/{project_id}/co-clients")
async def get_project_co_clients(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all co-clients for a project"""
    try:
        # Verify project access
        project = await db.projects.find_one({"id": project_id}, {"_id": 0})
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get co-clients
        co_clients = await db.co_clients.find(
            {"project_id": project_id},
            {"_id": 0}
        ).to_list(100)
        
        return co_clients
        
    except Exception as e:
        logger.error(f"Get co-clients error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.delete("/co-clients/{co_client_id}")
async def remove_co_client(
    co_client_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove a co-client"""
    try:
        # Get co-client
        co_client = await db.co_clients.find_one({"id": co_client_id}, {"_id": 0})
        if not co_client:
            raise HTTPException(status_code=404, detail="Co-client not found")
        
        # Only owner or main client can remove
        project = await db.projects.find_one({"id": co_client.get('project_id')}, {"_id": 0})
        if not current_user.is_owner and current_user.id != project.get('client_id'):
            raise HTTPException(status_code=403, detail="Access denied")
        
        await db.co_clients.delete_one({"id": co_client_id})
        
        return {"message": "Co-client removed successfully"}
        
    except Exception as e:
        logger.error(f"Remove co-client error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get historical progress error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 3D IMAGES MODULE ====================

# Preset categories for 3D images (expandable with custom)
PROJECT_3D_IMAGE_CATEGORIES = [
    "Living Room",
    "Kitchen",
    "Master Bedroom",
    "Bedroom 2",
    "Bedroom 3",
    "Bedroom 4",
    "Bathroom 1",
    "Bathroom 2",
    "Bathroom 3",
    "Dining Room",
    "Study Room",
    "Home Office",
    "Balcony",
    "Terrace",
    "Entrance",
    "Foyer",
    "Staircase",
    "Puja Room",
    "Store Room",
    "Garage",
    "Garden",
    "Pool Area",
    "Exterior Front",
    "Exterior Back",
    "Exterior Side",
    "Night View",
    "Bird Eye View",
    "Other"
]


class Image3DCreate(BaseModel):
    """Model for creating a 3D image entry"""
    category: str
    title: Optional[str] = None
    description: Optional[str] = None


@api_router.get("/3d-image-categories")
async def get_3d_image_categories():
    """Get preset 3D image categories"""
    return {
        "categories": PROJECT_3D_IMAGE_CATEGORIES,
        "allow_custom": True
    }


@api_router.get("/projects/{project_id}/3d-images")
async def get_project_3d_images(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all 3D images for a project, grouped by category"""
    # Verify project exists
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all images for this project
    images = await db.project_3d_images.find(
        {"project_id": project_id, "deleted_at": None},
        {"_id": 0}
    ).sort("created_at", -1).to_list(500)
    
    # Group by category
    grouped = {}
    for img in images:
        category = img.get("category", "Other")
        if category not in grouped:
            grouped[category] = []
        grouped[category].append(img)
    
    # Sort categories - preset first, then custom, then Other
    sorted_categories = []
    for cat in PROJECT_3D_IMAGE_CATEGORIES:
        if cat in grouped:
            sorted_categories.append({"category": cat, "images": grouped[cat]})
    
    # Add any custom categories
    for cat in grouped:
        if cat not in PROJECT_3D_IMAGE_CATEGORIES:
            sorted_categories.append({"category": cat, "images": grouped[cat]})
    
    return {
        "project_id": project_id,
        "total_images": len(images),
        "categories": sorted_categories,
        "preset_categories": PROJECT_3D_IMAGE_CATEGORIES
    }


@api_router.post("/projects/{project_id}/3d-images")
async def upload_3d_images(
    project_id: str,
    category: str = Form(...),
    title: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload 3D images for a project - Owner or Team Leader only"""
    # Verify project exists
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Permission check - only owner or team leader can upload
    is_team_leader = project.get("team_leader_id") == current_user.id
    if not current_user.is_owner and not is_team_leader:
        raise HTTPException(
            status_code=403, 
            detail="Only owner or team leader can upload 3D images"
        )
    
    # Create upload directory
    images_dir = UPLOAD_DIR / "3d_images" / project_id
    images_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_images = []
    
    for file in files:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            continue  # Skip non-image files
        
        # Generate unique filename
        file_ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
        if file_ext not in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            file_ext = ".jpg"
        
        unique_filename = f"{uuid.uuid4()}{file_ext}"
        file_path = images_dir / unique_filename
        
        # Save file
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Create database record
        image_record = {
            "id": str(uuid.uuid4()),
            "project_id": project_id,
            "category": category,
            "title": title or file.filename,
            "original_filename": file.filename,
            "file_path": str(file_path),
            "file_url": f"/api/uploads/3d_images/{project_id}/{unique_filename}",
            "file_size": len(content),
            "mime_type": file.content_type,
            "uploaded_by_id": current_user.id,
            "uploaded_by_name": current_user.name,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "deleted_at": None
        }
        
        # Create response record before inserting (to avoid _id being added)
        response_record = {k: v for k, v in image_record.items() if k != "file_path"}
        
        await db.project_3d_images.insert_one(image_record)
        uploaded_images.append(response_record)
    
    # Send notification to client about new images
    if uploaded_images:
        try:
            from template_notification_service import template_notification_service
            
            # Get client info
            if project.get("client_id"):
                client = await db.clients.find_one({"id": project["client_id"]}, {"_id": 0})
                if client and client.get("phone"):
                    await template_notification_service.notify_3d_images_uploaded(
                        phone_number=client["phone"],
                        client_name=client.get("name", "Client"),
                        project_name=project.get("title", "Your Project"),
                        category=category,
                        count=len(uploaded_images),
                        client_id=client.get("user_id"),
                        project_id=project_id
                    )
        except Exception as e:
            logger.warning(f"Failed to send 3D images notification: {str(e)}")
    
    return {
        "success": True,
        "uploaded_count": len(uploaded_images),
        "images": uploaded_images
    }


@api_router.delete("/projects/{project_id}/3d-images/{image_id}")
async def delete_3d_image(
    project_id: str,
    image_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a 3D image - Owner or Team Leader only"""
    # Verify project exists
    project = await db.projects.find_one({"id": project_id, "deleted_at": None}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get the image
    image = await db.project_3d_images.find_one({
        "id": image_id, 
        "project_id": project_id,
        "deleted_at": None
    }, {"_id": 0})
    
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Permission check - only owner or team leader can delete
    is_team_leader = project.get("team_leader_id") == current_user.id
    if not current_user.is_owner and not is_team_leader:
        raise HTTPException(
            status_code=403, 
            detail="Only owner or team leader can delete 3D images"
        )
    
    # Soft delete
    await db.project_3d_images.update_one(
        {"id": image_id},
        {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat(),
            "deleted_by_id": current_user.id
        }}
    )
    
    return {"success": True, "message": "Image deleted successfully"}


@api_router.get("/uploads/3d_images/{project_id}/{filename}")
async def serve_3d_image(project_id: str, filename: str):
    """Serve 3D image files"""
    file_path = UPLOAD_DIR / "3d_images" / project_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    
    return FileResponse(file_path)


# Include modular routers
from routes import auth, dashboard, notifications as notif_routes, projects, drawings
from routes import resources as resources_routes
from routes import whatsapp_webhook
from routes import ops as ops_routes
from routes import drawing_whatsapp
from routes import users as users_routes
from routes import accounting as accounting_routes
from routes import comments as comments_routes
from routes import external_parties as external_parties_routes
from routes import api_v2

# Include the new modular routers under /api
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(notif_routes.router)
api_router.include_router(projects.router)
api_router.include_router(drawings.router)
api_router.include_router(users_routes.router)
api_router.include_router(accounting_routes.router)
api_router.include_router(comments_routes.router)
api_router.include_router(api_v2.router)  # v2 endpoints for mobile

# Include drawing WhatsApp routes
drawing_whatsapp.set_auth_dependency(get_current_user)
api_router.include_router(drawing_whatsapp.router)
api_router.include_router(resources_routes.router)
api_router.include_router(whatsapp_webhook.router)

# Include operations routes (health, status, logs)
app.include_router(ops_routes.router)

# Note: clients, contractors, consultants routers exist but need updating to use new auth utils
# They will be fully integrated in Phase 1B

# Include the main api router
app.include_router(api_router)

# Include notifications and payments router
from api_notifications_payments import notifications_payments_router
app.include_router(notifications_payments_router, prefix="/api")

# Include aggregated APIs for performance
try:
    from aggregated_apis import aggregated_router, set_auth_dependency
    set_auth_dependency(get_current_user)
    app.include_router(aggregated_router)
    logger.info("Aggregated APIs router included")
except Exception as e:
    logger.warning(f"Failed to include aggregated APIs: {e}")

# Mount uploads directory for serving static files
# Using /api/uploads prefix to ensure Kubernetes ingress routes to backend
from pathlib import Path
uploads_path = Path(__file__).parent / "uploads"
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/api/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Background task reference
_reminder_task = None

@app.on_event("startup")
async def startup_event():
    """Start background tasks on app startup"""
    global _reminder_task
    try:
        from drawing_approval_reminders import reminder_scheduler
        _reminder_task = asyncio.create_task(reminder_scheduler())
        logger.info("Drawing approval reminder scheduler started")
    except Exception as e:
        logger.error(f"Failed to start reminder scheduler: {str(e)}")
    
    # Start async notification worker
    try:
        from async_notifications import async_notification_service
        await async_notification_service.start_worker()
        logger.info("Async notification worker started")
    except Exception as e:
        logger.error(f"Failed to start async notification worker: {str(e)}")
    
    # Start cache cleanup
    try:
        from cache_service import cache
        await cache.start_cleanup()
        logger.info("Cache cleanup task started")
    except Exception as e:
        logger.error(f"Failed to start cache cleanup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_db_client():
    global _reminder_task
    if _reminder_task:
        _reminder_task.cancel()
        try:
            await _reminder_task
        except asyncio.CancelledError:
            pass
    
    # Stop async notification worker
    try:
        from async_notifications import async_notification_service
        await async_notification_service.stop_worker()
    except Exception:
        pass
    
    # Stop cache cleanup
    try:
        from cache_service import cache
        await cache.stop_cleanup()
    except Exception:
        pass
    
    client.close()

# ==================== WHATSAPP NOTIFICATION ENDPOINTS ====================

@api_router.post("/whatsapp/test")
async def test_whatsapp_notification(
    phone_number: str = Query(..., description="Phone number to send test message"),
    current_user: dict = Depends(get_current_user)
):
    """
    Test WhatsApp notification - send a test message
    Only owner can test
    """
    try:
        if not current_user.get('is_owner'):
            raise HTTPException(status_code=403, detail="Only owner can send test messages")
        
        from whatsapp_service import whatsapp_service
        
        message = (
            "🎉 *Test Message from 4th Dimension*\n\n"
            "This is a test WhatsApp notification.\n\n"
            "If you received this, WhatsApp alerts are working correctly!"
        )
        
        result = whatsapp_service.send_message(phone_number, message)
        
        if result["success"]:
            return {
                "success": True,
                "message": "Test WhatsApp notification sent successfully",
                "details": result
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to send message"))
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test WhatsApp error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/whatsapp/settings")
async def get_whatsapp_settings(current_user: dict = Depends(get_current_user)):
    """Get user's WhatsApp notification settings"""
    try:
        settings = await db.whatsapp_settings.find_one({"user_id": current_user["id"]}, {"_id": 0})
        
        if not settings:
            # Return default settings
            return {
                "user_id": current_user["id"],
                "enabled": True,
                "notify_user_registered": True,
                "notify_drawing_uploaded": True,
                "notify_new_comment": True,
                "notify_task_assigned": True,
                "notify_task_deadline": True,
                "notify_milestone_completed": True,
                "notify_payment": True,
                "notify_site_visit": True,
                "notify_daily_report": True,
                "quiet_hours_start": None,
                "quiet_hours_end": None
            }
        
        return settings
    
    except Exception as e:
        logger.error(f"Get WhatsApp settings error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.put("/whatsapp/settings")
async def update_whatsapp_settings(
    settings: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update user's WhatsApp notification settings"""
    try:
        settings["user_id"] = current_user["id"]
        settings["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Upsert settings
        await db.whatsapp_settings.update_one(
            {"user_id": current_user["id"]},
            {"$set": settings},
            upsert=True
        )
        
        return {
            "success": True,
            "message": "WhatsApp notification settings updated successfully"
        }
    
    except Exception as e:
        logger.error(f"Update WhatsApp settings error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/whatsapp/notifications/history")
async def get_notification_history(
    limit: int = Query(50, le=200),
    current_user: dict = Depends(get_current_user)
):
    """Get user's WhatsApp notification history"""
    try:
        notifications = await db.whatsapp_notifications.find(
            {"user_id": current_user["id"]},
            {"_id": 0}
        ).sort("sent_at", -1).limit(limit).to_list(limit)
        
        return {
            "total": len(notifications),
            "notifications": notifications
        }
    
    except Exception as e:
        logger.error(f"Get notification history error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/whatsapp/notifications/stats")
async def get_notification_stats(current_user: dict = Depends(get_current_user)):
    """Get WhatsApp notification statistics (Owner only)"""
    try:
        if not current_user.get('is_owner'):
            raise HTTPException(status_code=403, detail="Only owner can view stats")
        
        # Count total notifications
        total = await db.whatsapp_notifications.count_documents({})
        
        # Count by status
        sent_count = await db.whatsapp_notifications.count_documents({"delivery_status": "sent"})
        delivered_count = await db.whatsapp_notifications.count_documents({"delivery_status": "delivered"})
        failed_count = await db.whatsapp_notifications.count_documents({"delivery_status": "failed"})
        
        # Count by type
        pipeline = [
            {"$group": {"_id": "$message_type", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        
        type_counts = await db.whatsapp_notifications.aggregate(pipeline).to_list(100)
        
        return {
            "total_notifications": total,
            "by_status": {
                "sent": sent_count,
                "delivered": delivered_count,
                "failed": failed_count
            },
            "by_type": type_counts
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get notification stats error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

