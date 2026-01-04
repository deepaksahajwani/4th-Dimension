from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pathlib import Path
from datetime import datetime
from typing import Optional
import os

# Import from parent directory
import sys
sys.path.append(str(Path(__file__).parent.parent))

from models_projects import *

# File storage settings
MAX_FILE_SIZE = int(os.environ.get('MAX_FILE_SIZE', 524288000))
UPLOAD_DIR = Path("/app/uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

router = APIRouter(prefix="/files", tags=["files"])

# Dependency import (will be provided by server.py)
def get_current_user():
    pass

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    category: str = "general",
    current_user = Depends(get_current_user)
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

@router.get("/download/{file_key:path}")
async def download_file(file_key: str, current_user = Depends(get_current_user)):
    try:
        file_path = UPLOAD_DIR / file_key
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        from fastapi.responses import FileResponse
        return FileResponse(file_path)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found")
