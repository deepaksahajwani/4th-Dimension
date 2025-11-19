from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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
    ProjectType, ProjectStatus, DrawingStatus, TaskCategory, TaskStatus, 
    Priority, IssueStatus, ConsultantType, NotificationChannel,
    Consultant, ConsultantCreate, ProjectDrawing, ProjectDrawingCreate,
    DrawingRevision, Task, TaskCreate, SiteVisit, SiteVisitCreate,
    SiteIssue, SiteIssueCreate, Notification, NotificationCreate,
    ChecklistPreset, DrawingType, ClientUpdate,
    Client as NewClient, ClientCreate as NewClientCreate,
    Project as NewProject, ProjectCreate as NewProjectCreate, ProjectUpdate as NewProjectUpdate,
    ContactInfo, BrandCategory, BrandCategoryMaster, BrandCategoryMasterCreate, BrandCategoryMasterUpdate,
    ContactTypeMaster, ContactTypeMasterCreate, ContactTypeMasterUpdate,
    ProjectDrawingCreate, ProjectDrawingUpdate,
    WeeklyTarget, DailyTask, WeeklyRating, WeeklyTargetCreate, DailyTaskCreate, DailyTaskUpdate,
    DrawingComment, DrawingCommentCreate, DrawingCommentUpdate,
    TeamMemberVerification, VerifyEmailRequest, VerifyPhoneRequest, ResendOTPRequest,
    Contractor, ContractorCreate, ContractorType,
    Vendor, VendorCreate, VendorUpdate, VendorType
)
from drawing_templates import get_template_drawings

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

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

# Create the main app without a prefix
app = FastAPI(title="Architecture Firm Management System")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


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
    project_id: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"

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
        # Check if user already exists
        existing_user = await db.users.find_one({"email": registration_data.email}, {"_id": 0})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
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
        sender_email = os.getenv('SENDER_EMAIL')
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
            from_email=sender_email,
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
        
        # Verify Phone OTP using Twilio Verify service
        verify_service_sid = os.getenv('TWILIO_VERIFY_SERVICE_SID')
        phone_verified = False
        
        if verify_service_sid:
            # Use Twilio Verify to check the phone OTP
            try:
                from twilio.rest import Client
                twilio_client = Client(
                    os.getenv('TWILIO_ACCOUNT_SID'),
                    os.getenv('TWILIO_AUTH_TOKEN')
                )
                
                verification_check = twilio_client.verify \
                    .v2 \
                    .services(verify_service_sid) \
                    .verification_checks \
                    .create(to=pending_reg['mobile'], code=otp_data.phone_otp)
                
                if verification_check.status == 'approved':
                    phone_verified = True
                else:
                    raise HTTPException(status_code=400, detail="Invalid phone OTP")
                    
            except Exception as twilio_error:
                print(f"Twilio verification error: {str(twilio_error)}")
                raise HTTPException(status_code=400, detail="Invalid phone OTP or verification failed")
        else:
            # Fallback: compare with stored OTP
            if pending_reg['phone_otp'] != otp_data.phone_otp:
                raise HTTPException(status_code=400, detail="Invalid phone OTP")
            phone_verified = True
        
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
        
        # Delete pending registration
        await db.pending_registrations.delete_one({"email": password_data.email})
        
        # Send approval request email to owner
        owner = await db.users.find_one({"is_owner": True}, {"_id": 0})
        if owner:
            await send_approval_request_email(owner['email'], user_dict)
        
        # Send welcome email to user
        await send_registration_complete_email(user_dict)
        
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
        sender_email = os.getenv('SENDER_EMAIL')
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
                    
                    <!-- Button section using table for better email client support -->
                    <table width="100%" cellpadding="0" cellspacing="0" border="0" style="margin: 30px 0;">
                        <tr>
                            <td align="center">
                                <table cellpadding="0" cellspacing="0" border="0">
                                    <tr>
                                        <td style="padding: 0 10px;">
                                            <a href="{approval_link}" 
                                               style="display: inline-block; 
                                                      background-color: #10B981; 
                                                      color: #ffffff !important; 
                                                      padding: 15px 45px; 
                                                      text-decoration: none; 
                                                      border-radius: 6px; 
                                                      font-weight: bold; 
                                                      font-size: 16px;
                                                      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                                      mso-line-height-rule: exactly;">
                                                ✓ Approve
                                            </a>
                                        </td>
                                        <td style="padding: 0 10px;">
                                            <a href="{reject_link}" 
                                               style="display: inline-block; 
                                                      background-color: #EF4444; 
                                                      color: #ffffff !important; 
                                                      padding: 15px 45px; 
                                                      text-decoration: none; 
                                                      border-radius: 6px; 
                                                      font-weight: bold; 
                                                      font-size: 16px;
                                                      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                                                      mso-line-height-rule: exactly;">
                                                ✕ Reject
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                    
                    <p style="color: #666; font-size: 12px; text-align: center; margin-top: 30px;">
                        You can also approve/reject from your dashboard at:<br>
                        <a href="{backend_url}/pending-registrations" style="color: #4F46E5; text-decoration: none;">
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
            from_email=sender_email,
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
        sender_email = os.getenv('SENDER_EMAIL')
        
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
                            Contact: {sender_email}
                        </p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=sender_email,
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

@api_router.post("/team/invite")
async def invite_team_member(
    invite_data: InviteTeamMember,
    current_user: User = Depends(require_owner)
):
    """
    Owner invites team member - sends verification email and SMS
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
    Redirects to dashboard with success message
    """
    from fastapi.responses import RedirectResponse
    
    try:
        frontend_url = os.getenv('REACT_APP_BACKEND_URL')
        
        if action not in ['approve', 'reject']:
            return RedirectResponse(url=f"{frontend_url}/pending-registrations?error=invalid_action")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            return RedirectResponse(url=f"{frontend_url}/pending-registrations?error=user_not_found")
        
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
            
            # Redirect to pending registrations page with success message
            user_name_encoded = __import__('urllib.parse').quote(user['name'])
            return RedirectResponse(url=f"{frontend_url}/pending-registrations?success=approved&user={user_name_encoded}")
        else:
            await db.users.update_one(
                {"id": user_id},
                {"$set": {
                    "approval_status": "rejected"
                }}
            )
            
            # Send rejection notification to user
            await send_approval_notification(user, approved=False)
            
            # Redirect to pending registrations page with rejection message
            user_name_encoded = __import__('urllib.parse').quote(user['name'])
            return RedirectResponse(url=f"{frontend_url}/pending-registrations?success=rejected&user={user_name_encoded}")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Approval error: {str(e)}")
        return RedirectResponse(url=f"{frontend_url}/pending-registrations?error=unknown")

@api_router.post("/auth/approve-user-dashboard")
async def approve_user_from_dashboard(
    user_id: str = Query(...),
    action: str = Query(...),
    current_user: User = Depends(require_owner)
):
    """
    Approve or reject user from owner dashboard
    """
    return await approve_reject_user(user_id, action)

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
    """Send approval/rejection notification to user"""
    try:
        sender_email = os.getenv('SENDER_EMAIL')
        
        if approved:
            subject = "Your 4th Dimension Account Has Been Approved!"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h1 style="color: #10B981;">🎉 Account Approved!</h1>
                        </div>
                        
                        <h2>Dear {user['name']},</h2>
                        
                        <p>Great news! Your 4th Dimension account has been approved. You can now log in and start using the platform.</p>
                        
                        <div style="background: #D1FAE5; padding: 20px; border-radius: 8px; margin: 20px 0; text-align: center;">
                            <p style="margin: 0 0 15px 0;"><strong>Your Login Credentials:</strong></p>
                            <p><strong>Email:</strong> {user['email']}</p>
                            {'<p><strong>Password:</strong> As set during registration</p>' if user.get('registered_via') == 'email' else '<p><strong>Login:</strong> Use your Google account</p>'}
                            
                            <a href="{os.getenv('REACT_APP_BACKEND_URL')}" style="display: inline-block; background: #10B981; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin-top: 15px; font-weight: bold;">
                                Login Now
                            </a>
                        </div>
                        
                        <p>Welcome to the 4th Dimension family! We're excited to work with you.</p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                            <p><strong>4th Dimension - Architecture & Design</strong></p>
                        </div>
                    </div>
                </body>
            </html>
            """
        else:
            subject = "4th Dimension Registration Update"
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                        <h2>Dear {user['name']},</h2>
                        
                        <p>Thank you for your interest in joining 4th Dimension.</p>
                        
                        <p>After careful review, we regret to inform you that we are unable to approve your registration at this time.</p>
                        
                        <p>If you believe this is an error or have any questions, please contact us at {sender_email}.</p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #666; font-size: 12px;">
                            <p><strong>4th Dimension - Architecture & Design</strong></p>
                        </div>
                    </div>
                </body>
            </html>
            """
        
        from sendgrid import SendGridAPIClient
        from sendgrid.helpers.mail import Mail
        
        message = Mail(
            from_email=sender_email,
            to_emails=user['email'],
            subject=subject,
            html_content=html_content
        )
        
        sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
        sendgrid_client.send(message)
        
    except Exception as e:
        print(f"Failed to send approval notification: {str(e)}")


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



# ==================== USER ROUTES ====================

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if user.get('date_of_joining') and isinstance(user['date_of_joining'], str):
            user['date_of_joining'] = datetime.fromisoformat(user['date_of_joining'])
    return users

@api_router.get("/users/pending")
async def get_pending_users(current_user: User = Depends(require_admin)):
    """Get all users pending validation"""
    users = await db.users.find({"is_validated": False, "registration_completed": True}, {"_id": 0, "password_hash": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        if user.get('date_of_birth') and isinstance(user['date_of_birth'], str):
            user['date_of_birth'] = datetime.fromisoformat(user['date_of_birth'])
    return users

@api_router.post("/users/{user_id}/validate")
async def validate_user(user_id: str, current_user: User = Depends(require_admin)):
    """Approve a pending user (owner or admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['is_validated']:
        raise HTTPException(status_code=400, detail="User already validated")
    
    # Update user
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_validated": True}}
    )
    
    return {"message": "User validated successfully"}

@api_router.post("/users/{user_id}/reject")
async def reject_user(user_id: str, current_user: User = Depends(require_admin)):
    """Reject a pending user (owner or admin only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user['is_validated']:
        raise HTTPException(status_code=400, detail="User already validated")
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    return {"message": "User rejected and removed"}

@api_router.post("/users/{user_id}/toggle-admin")
async def toggle_admin_rights(user_id: str, current_user: User = Depends(require_owner)):
    """Toggle administrator rights (owner only)"""
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.get('is_owner'):
        raise HTTPException(status_code=400, detail="Cannot change admin rights for owner")
    
    # Toggle admin status
    new_status = not user.get('is_admin', False)
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_admin": new_status}}
    )
    
    action = "granted" if new_status else "revoked"
    return {"message": f"Administrator rights {action} successfully", "is_admin": new_status}

@api_router.post("/users/generate-otp")
async def generate_otp(request: OTPRequest, current_user: User = Depends(require_owner)):
    """Generate OTP for sensitive operations (add/delete team members)"""
    # Generate 6-digit OTP
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # Store OTP in database
    otp = OTP(
        user_id=current_user.id,
        otp_code=otp_code,
        action=request.action,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=5)
    )
    
    otp_dict = otp.model_dump()
    otp_dict['created_at'] = otp_dict['created_at'].isoformat()
    otp_dict['expires_at'] = otp_dict['expires_at'].isoformat()
    
    await db.otps.insert_one(otp_dict)
    
    # In production, send OTP via email/SMS
    # For now, return it in response for demo purposes
    return {
        "message": "OTP generated successfully",
        "otp_code": otp_code,  # Remove this in production
        "expires_in": 300  # 5 minutes
    }

@api_router.post("/users/verify-otp")
async def verify_otp(request: OTPVerify, current_user: User = Depends(require_owner)):
    """Verify OTP for sensitive operations"""
    otp_doc = await db.otps.find_one({
        "user_id": current_user.id,
        "otp_code": request.otp_code,
        "action": request.action,
        "used": False
    })
    
    if not otp_doc:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    
    # Check expiry
    expires_at = datetime.fromisoformat(otp_doc['expires_at']) if isinstance(otp_doc['expires_at'], str) else otp_doc['expires_at']
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="OTP has expired")
    
    # Mark OTP as used
    await db.otps.update_one(
        {"id": otp_doc['id']},
        {"$set": {"used": True}}
    )
    
    return {
        "message": "OTP verified successfully",
        "verified": True
    }

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: User = Depends(require_owner)):
    """Delete a team member (Owner only)"""
    
    # Don't allow deleting yourself
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user email for cleanup
    user_email = user.get('email')
    
    # Delete user
    await db.users.delete_one({"id": user_id})
    
    # Delete user's sessions
    await db.user_sessions.delete_many({"user_id": user_id})
    
    # Delete any pending registrations
    if user_email:
        await db.pending_registrations.delete_many({"email": user_email})
        await db.team_verifications.delete_many({"email": user_email})
    
    return {"message": "Team member deleted successfully"}

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UpdateTeamMember, current_user: User = Depends(require_owner)):
    """Update a team member's information (Owner only)"""
    
    # Check if user exists
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user profile
    dob = datetime.fromisoformat(user_data.date_of_birth) if user_data.date_of_birth else None
    doj = datetime.fromisoformat(user_data.date_of_joining) if user_data.date_of_joining else None
    
    await db.users.update_one(
        {"id": user_id},
        {"$set": {
            "name": user_data.full_name,
            "address_line_1": user_data.address_line_1,
            "address_line_2": user_data.address_line_2,
            "landmark": user_data.landmark,
            "city": user_data.city,
            "state": user_data.state,
            "pin_code": user_data.pin_code,
            "mobile": user_data.mobile,
            "date_of_birth": dob.isoformat() if dob else None,
            "date_of_joining": doj.isoformat() if doj else None,
            "gender": user_data.gender,
            "marital_status": user_data.marital_status,
            "role": user_data.role,
            "salary": user_data.salary,
            "writeup": user_data.writeup,
            "passions": user_data.passions,
            "contribution": user_data.contribution
        }}
    )
    
    return {"message": "User updated successfully"}


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
    
    # Add project count for each client
    for client in clients:
        if isinstance(client.get('created_at'), str):
            client['created_at'] = datetime.fromisoformat(client['created_at'])
        if isinstance(client.get('updated_at'), str):
            client['updated_at'] = datetime.fromisoformat(client['updated_at'])
        
        # Count projects for this client
        project_count = await db.projects.count_documents({"client_id": client["id"], "deleted_at": None})
        client['total_projects'] = project_count
    
    return clients

@api_router.get("/clients/{client_id}")
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id, "deleted_at": None}, {"_id": 0})
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
    """Permanently delete client (soft delete) and unlink from projects"""
    # Soft delete the client
    await db.clients.update_one(
        {"id": client_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    # Set client_id to null in related projects (cascade)
    await db.projects.update_many(
        {"client_id": client_id},
        {"$set": {"client_id": None}}
    )
    
    return {"message": "Client deleted and projects unlinked"}



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
    
    # Auto-generate sequential drawings from templates based on project types
    for project_type in project_data.project_types:
        template_drawings = get_template_drawings(project_type)
        if template_drawings:
            for sequence_num, drawing_name in enumerate(template_drawings, start=1):
                # Calculate due date (7 days after project start or today)
                base_date = project.start_date if project.start_date else datetime.now(timezone.utc)
                due_date = base_date + timedelta(days=7 * sequence_num)
                
                drawing = ProjectDrawing(
                    project_id=project.id,
                    category=project_type,
                    name=drawing_name,
                    status=DrawingStatus.PLANNED,
                    due_date=due_date,
                    is_issued=False,
                    revision_count=0,
                    sequence_number=sequence_num,
                    is_active=True if sequence_num == 1 else False  # Only first drawing is active
                )
                drawing_dict = drawing.model_dump()
                # Convert datetimes to ISO strings
                for field in ['created_at', 'updated_at', 'due_date', 'issued_date']:
                    if drawing_dict.get(field):
                        drawing_dict[field] = drawing_dict[field].isoformat() if isinstance(drawing_dict[field], datetime) else drawing_dict[field]
                
                await db.project_drawings.insert_one(drawing_dict)
    
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
    """Get projects based on user role"""
    query = {"deleted_at": None}
    if not include_archived:
        query["archived"] = {"$ne": True}
    
    # Role-based filtering
    if current_user.role == "client":
        # Clients see projects where their client_id matches
        # First find the client record by email
        client = await db.clients.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        if client:
            query["client_id"] = client["id"]
        else:
            # If no client record found, return empty list
            return []
    elif current_user.role in ["contractor", "consultant"]:
        # Contractors/Consultants see projects where they're assigned
        # Find contractor/consultant record by email
        contractor = await db.contractors.find_one({"email": current_user.email}, {"_id": 0, "id": 1})
        if contractor:
            # Find projects that have this contractor assigned
            query["assigned_contractors.contractor_id"] = contractor["id"]
    # Owners and team_members see all projects (no additional filter)
    
    projects = await db.projects.find(query, {"_id": 0}).to_list(1000)
    for project in projects:
        # Convert ISO strings to datetime for proper serialization
        for field in ['created_at', 'updated_at', 'start_date', 'end_date']:
            if isinstance(project.get(field), str) and project.get(field):
                try:
                    project[field] = datetime.fromisoformat(project[field])
                except ValueError:
                    # Handle invalid date strings
                    project[field] = None
            elif project.get(field) == '':
                project[field] = None
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
    
    # Get project drawings count
    drawings_count = await db.project_drawings.count_documents({"project_id": project_id, "deleted_at": None})
    project['drawings_count'] = drawings_count
    
    return project

@api_router.put("/projects/{project_id}")
async def update_project(
    project_id: str, 
    project_data: NewProjectUpdate, 
    current_user: User = Depends(get_current_user)
):
    """Update project details"""
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
    
    return {"message": "Project updated successfully"}

@api_router.delete("/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: User = Depends(require_owner)
):
    """Soft delete project (owner only)"""
    await db.projects.update_one(
        {"id": project_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Project deleted successfully"}


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
    
    # If un-issuing (is_issued changing from True to False)
    if update_dict.get('is_issued') == False and drawing.get('is_issued') == True:
        # Reset to pending state - clear everything
        update_dict['issued_date'] = None
        update_dict['under_review'] = False
        update_dict['is_approved'] = False
        update_dict['approved_date'] = None
        update_dict['file_url'] = None  # Clear the file so Upload button appears
    
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
    
    # If drawing is being issued, activate next drawing in sequence
    if update_dict.get('is_issued') == True and drawing.get('is_issued') == False:
        update_dict['issued_date'] = datetime.now(timezone.utc).isoformat()
        # If re-issuing after revision was resolved, keep has_pending_revision as False
        # This maintains the "R1 Resolved" state while showing as issued
        
        # Find and activate next drawing in sequence
        if drawing.get('sequence_number'):
            next_sequence = drawing.get('sequence_number') + 1
            next_drawing = await db.project_drawings.find_one({
                "project_id": drawing.get('project_id'),
                "category": drawing.get('category'),
                "sequence_number": next_sequence,
                "deleted_at": None
            }, {"_id": 0})
            
            if next_drawing:
                # Activate next drawing
                await db.project_drawings.update_one(
                    {"id": next_drawing['id']},
                    {"$set": {
                        "is_active": True,
                        "updated_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
    
    # Update the drawing
    update_dict['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.project_drawings.update_one(
        {"id": drawing_id},
        {"$set": update_dict}
    )
    
    # Fetch and return updated drawing
    updated_drawing = await db.project_drawings.find_one({"id": drawing_id}, {"_id": 0})
    
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
    file: UploadFile = File(...),
    drawing_id: str = Form(...),
    upload_type: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    """Upload PDF file for drawing"""
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    # Create uploads directory if it doesn't exist
    upload_dir = Path("uploads/drawings")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{drawing_id}_{upload_type}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Return file URL (relative path)
    file_url = f"/uploads/drawings/{unique_filename}"
    
    return {"file_url": file_url, "filename": file.filename}

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


# ==================== DRAWING COMMENTS ROUTES ====================

@api_router.post("/drawings/{drawing_id}/comments")
async def create_drawing_comment(
    drawing_id: str,
    comment_data: DrawingCommentCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a comment on a drawing"""
    from models_projects import DrawingComment
    
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
    from models_projects import DrawingCommentUpdate
    
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
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Upload reference file (image/PDF) for a comment"""
    # Find comment
    comment = await db.drawing_comments.find_one({"id": comment_id, "deleted_at": None}, {"_id": 0})
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user is the author
    if comment['user_id'] != current_user.id:
        raise HTTPException(status_code=403, detail="You can only add files to your own comments")
    
    # Validate file type (images and PDFs only)
    allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif']
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Only PDF and image files are allowed")
    
    # Create uploads directory
    upload_dir = Path("uploads/comment_references")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    unique_filename = f"{comment_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}{file_extension}"
    file_path = upload_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
    
    # Return file URL
    file_url = f"/uploads/comment_references/{unique_filename}"
    
    # Add to comment's reference_files array
    current_files = comment.get('reference_files', [])
    current_files.append(file_url)
    
    await db.drawing_comments.update_one(
        {"id": comment_id},
        {"$set": {"reference_files": current_files}}
    )
    
    return {"file_url": file_url, "filename": file.filename}

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
    """Get all contractors"""
    contractors = await db.contractors.find(
        {"deleted_at": None},
        {"_id": 0}
    ).to_list(1000)
    return contractors

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
    """Soft delete a contractor (Owner only)"""
    result = await db.contractors.update_one(
        {"id": contractor_id},
        {"$set": {
            "deleted_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    return {"message": "Contractor deleted successfully"}

@api_router.get("/contractor-types")
async def get_contractor_types():
    """Get list of predefined contractor types"""
    return [{"value": t.value, "label": t.value} for t in ContractorType]


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
            raise HTTPException(status_code=413, detail=f"File size exceeds maximum allowed size")
        
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


# ==================== ACCOUNTING ROUTES ====================

@api_router.post("/accounting", response_model=Accounting)
async def create_accounting_entry(entry_data: AccountingCreate, current_user: User = Depends(require_owner)):
    entry = Accounting(
        transaction_type=entry_data.transaction_type,
        amount=entry_data.amount,
        project_id=entry_data.project_id,
        user_id=entry_data.user_id,
        description=entry_data.description,
        category=entry_data.category,
        created_by=current_user.id
    )
    
    entry_dict = entry.model_dump()
    entry_dict['date'] = entry_dict['date'].isoformat()
    
    await db.accounting.insert_one(entry_dict)
    return entry

@api_router.get("/accounting", response_model=List[Accounting])
async def get_accounting_entries(current_user: User = Depends(require_owner)):
    entries = await db.accounting.find({}, {"_id": 0}).sort("date", -1).to_list(1000)
    for entry in entries:
        if isinstance(entry.get('date'), str):
            entry['date'] = datetime.fromisoformat(entry['date'])
    return entries

@api_router.get("/accounting/summary")
async def get_accounting_summary(current_user: User = Depends(require_owner)):
    entries = await db.accounting.find({}, {"_id": 0}).to_list(10000)
    
    total_receivables = sum(e['amount'] for e in entries if e['transaction_type'] == 'receivable')
    total_payments = sum(e['amount'] for e in entries if e['transaction_type'] == 'payment')
    total_salaries = sum(e['amount'] for e in entries if e['transaction_type'] == 'salary')
    total_expenses = sum(e['amount'] for e in entries if e['transaction_type'] == 'expense')
    
    return {
        "total_receivables": total_receivables,
        "total_payments": total_payments,
        "total_salaries": total_salaries,
        "total_expenses": total_expenses,
        "net_income": total_receivables - (total_payments + total_salaries + total_expenses)
    }


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
    except Exception as e:
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
    for c in consultants:
        if isinstance(c.get('created_at'), str):
            c['created_at'] = datetime.fromisoformat(c['created_at'])
        if isinstance(c.get('updated_at'), str):
            c['updated_at'] = datetime.fromisoformat(c['updated_at'])
    return consultants

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
    """Soft delete consultant"""
    existing = await db.consultants.find_one({"id": consultant_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Consultant not found")
    
    await db.consultants.update_one(
        {"id": consultant_id},
        {"$set": {"deleted_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"message": "Consultant deleted successfully"}

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

# Notifications
@api_router.get("/notifications")
async def get_notifications(current_user: User = Depends(get_current_user), limit: int = 50):
    notifications = await db.notifications.find({}, {"_id": 0}).sort("sent_at", -1).limit(limit).to_list(limit)
    for n in notifications:
        if isinstance(n.get('sent_at'), str):
            n['sent_at'] = datetime.fromisoformat(n['sent_at'])
    return notifications


# Include the router in the main app
app.include_router(api_router)

# Mount uploads directory for serving static files
from pathlib import Path
uploads_path = Path(__file__).parent / "uploads"
uploads_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_path)), name="uploads")

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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()