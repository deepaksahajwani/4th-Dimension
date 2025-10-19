from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
import boto3
from botocore.exceptions import ClientError
import httpx
from emergentintegrations.llm.chat import LlmChat, UserMessage, FileContentWithMimeType

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
    role: str  # owner, architect, interior_designer, visualizer, office_boy
    password_hash: Optional[str] = None
    picture: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    role: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserSession(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    contact: Optional[str] = None
    email: Optional[str] = None
    referred_by: Optional[str] = None  # Client ID
    first_call_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientCreate(BaseModel):
    name: str
    contact: Optional[str] = None
    email: Optional[str] = None
    referred_by: Optional[str] = None
    first_call_date: str

class Project(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    project_type: str  # architectural, interior, both
    name: str
    plot_dimensions: Optional[str] = None
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
    plot_dimensions: Optional[str] = None
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
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owner can perform this action")
    return current_user


# ==================== AUTH ROUTES ====================

@api_router.post("/auth/register")
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        password_hash=get_password_hash(user_data.password)
    )
    
    user_dict = user.model_dump()
    user_dict['created_at'] = user_dict['created_at'].isoformat()
    
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
            "role": user.role
        }
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
            "role": user_doc['role']
        }
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
        user_doc = await db.users.find_one({"email": session_data['email']})
        
        if not user_doc:
            # Create new user
            user = User(
                email=session_data['email'],
                name=session_data['name'],
                role="architect",  # Default role
                picture=session_data.get('picture')
            )
            user_dict = user.model_dump()
            user_dict['created_at'] = user_dict['created_at'].isoformat()
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
                "role": user_doc['role'],
                "picture": user_doc.get('picture')
            }
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


# ==================== USER ROUTES ====================

@api_router.get("/users", response_model=List[User])
async def get_users(current_user: User = Depends(get_current_user)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users


# ==================== CLIENT ROUTES ====================

@api_router.post("/clients", response_model=Client)
async def create_client(client_data: ClientCreate, current_user: User = Depends(get_current_user)):
    client = Client(
        name=client_data.name,
        contact=client_data.contact,
        email=client_data.email,
        referred_by=client_data.referred_by,
        first_call_date=datetime.fromisoformat(client_data.first_call_date)
    )
    
    client_dict = client.model_dump()
    client_dict['first_call_date'] = client_dict['first_call_date'].isoformat()
    client_dict['created_at'] = client_dict['created_at'].isoformat()
    
    await db.clients.insert_one(client_dict)
    return client

@api_router.get("/clients", response_model=List[Client])
async def get_clients(current_user: User = Depends(get_current_user)):
    clients = await db.clients.find({}, {"_id": 0}).to_list(1000)
    for client in clients:
        if isinstance(client.get('first_call_date'), str):
            client['first_call_date'] = datetime.fromisoformat(client['first_call_date'])
        if isinstance(client.get('created_at'), str):
            client['created_at'] = datetime.fromisoformat(client['created_at'])
    return clients

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str, current_user: User = Depends(get_current_user)):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if isinstance(client.get('first_call_date'), str):
        client['first_call_date'] = datetime.fromisoformat(client['first_call_date'])
    if isinstance(client.get('created_at'), str):
        client['created_at'] = datetime.fromisoformat(client['created_at'])
    return Client(**client)


# ==================== PROJECT ROUTES ====================

@api_router.post("/projects", response_model=Project)
async def create_project(project_data: ProjectCreate, current_user: User = Depends(get_current_user)):
    project = Project(
        client_id=project_data.client_id,
        project_type=project_data.project_type,
        name=project_data.name,
        plot_dimensions=project_data.plot_dimensions,
        assigned_to=project_data.assigned_to or [],
        status="consultation"
    )
    
    project_dict = project.model_dump()
    project_dict['created_at'] = project_dict['created_at'].isoformat()
    
    await db.projects.insert_one(project_dict)
    
    # Create standardized drawing list
    templates = await db.drawing_templates.find(
        {"project_type": {"$in": [project_data.project_type, "both"]}},
        {"_id": 0}
    ).to_list(1000)
    
    for template in templates:
        drawing = Drawing(
            project_id=project.id,
            category=template['category'],
            name=template['name'],
            description=template.get('description'),
            order=template['order'],
            status="pending"
        )
        drawing_dict = drawing.model_dump()
        drawing_dict['created_at'] = drawing_dict['created_at'].isoformat()
        await db.drawings.insert_one(drawing_dict)
    
    return project

@api_router.get("/projects", response_model=List[Project])
async def get_projects(current_user: User = Depends(get_current_user)):
    projects = await db.projects.find({}, {"_id": 0}).to_list(1000)
    for project in projects:
        if isinstance(project.get('created_at'), str):
            project['created_at'] = datetime.fromisoformat(project['created_at'])
    return projects

@api_router.get("/projects/{project_id}", response_model=Project)
async def get_project(project_id: str, current_user: User = Depends(get_current_user)):
    project = await db.projects.find_one({"id": project_id}, {"_id": 0})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if isinstance(project.get('created_at'), str):
        project['created_at'] = datetime.fromisoformat(project['created_at'])
    return Project(**project)

@api_router.patch("/projects/{project_id}")
async def update_project(project_id: str, updates: dict, current_user: User = Depends(get_current_user)):
    result = await db.projects.update_one({"id": project_id}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"message": "Project updated successfully"}


# ==================== DRAWING ROUTES ====================

@api_router.get("/projects/{project_id}/drawings", response_model=List[Drawing])
async def get_project_drawings(project_id: str, current_user: User = Depends(get_current_user)):
    drawings = await db.drawings.find({"project_id": project_id}, {"_id": 0}).sort("order", 1).to_list(1000)
    for drawing in drawings:
        if isinstance(drawing.get('created_at'), str):
            drawing['created_at'] = datetime.fromisoformat(drawing['created_at'])
        if drawing.get('issue_date') and isinstance(drawing['issue_date'], str):
            drawing['issue_date'] = datetime.fromisoformat(drawing['issue_date'])
    return drawings

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
    total_projects = await db.projects.count_documents({})
    active_projects = await db.projects.count_documents({"status": {"$nin": ["completed"]}})
    total_clients = await db.clients.count_documents({})
    pending_tasks = await db.tasks.count_documents({"status": {"$in": ["open", "in_progress"]}})
    red_flags = await db.tasks.count_documents({"priority": "red_flag", "status": {"$ne": "closed"}})
    
    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_clients": total_clients,
        "pending_tasks": pending_tasks,
        "red_flags": red_flags
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
        file_key = f"files/{category}/{project_id or 'general'}/{timestamp}_{file.filename}"
        
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET_NAME,
            file_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        return {
            "message": "File uploaded successfully",
            "file_key": file_key,
            "size": file_size
        }
    
    except ClientError as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/files/download/{file_key:path}")
async def download_file(file_key: str, current_user: User = Depends(get_current_user)):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': S3_BUCKET_NAME, 'Key': file_key},
            ExpiresIn=3600
        )
        return {"url": url}
    except ClientError as e:
        raise HTTPException(status_code=404, detail="File not found")


# Include the router in the main app
app.include_router(api_router)

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