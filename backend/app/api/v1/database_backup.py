"""Database Backup API endpoints."""

import os
import subprocess
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import UserRole
from app.core.config import settings

router = APIRouter()

# Backup directory
BACKUP_DIR = Path("backups")
BACKUP_DIR.mkdir(exist_ok=True)

def check_admin_access(request: Request):
    """Check if user has admin access."""
    # In production, get from session/token
    # For now, check header
    user_role = request.headers.get("X-User-Role", "viewer")
    if user_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return True

def get_db_connection_string():
    """Get database connection string for pg_dump."""
    # Parse the DATABASE_URL from settings
    # Format: postgresql+asyncpg://user:password@host:port/database
    db_url = str(settings.DATABASE_URL)
    
    # Replace asyncpg with postgresql for pg_dump
    if "asyncpg" in db_url:
        db_url = db_url.replace("+asyncpg", "")
    
    return db_url

@router.post("/create", response_model=Dict[str, Any])
async def create_backup(
    *,
    request: Request,
    background_tasks: BackgroundTasks,
    description: Optional[str] = None,
    _: bool = Depends(check_admin_access)
) -> Dict[str, Any]:
    """
    Create a new database backup (admin only).
    
    The backup is created asynchronously in the background.
    """
    try:
        # Generate backup filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pearl_backup_{timestamp}.sql"
        backup_path = BACKUP_DIR / backup_filename
        
        # Get database connection details
        db_url = get_db_connection_string()
        
        # Create backup metadata
        metadata = {
            "filename": backup_filename,
            "created_at": datetime.utcnow().isoformat(),
            "description": description or f"Manual backup created at {timestamp}",
            "status": "pending",
            "size_bytes": None,
            "error": None
        }
        
        # Save initial metadata
        metadata_path = BACKUP_DIR / f"{backup_filename}.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        
        # Schedule backup in background
        background_tasks.add_task(
            perform_backup,
            db_url,
            backup_path,
            metadata_path,
            metadata
        )
        
        return {
            "message": "Backup initiated successfully",
            "filename": backup_filename,
            "status": "pending",
            "description": metadata["description"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate backup: {str(e)}"
        )

async def perform_backup(db_url: str, backup_path: Path, metadata_path: Path, metadata: dict):
    """Perform the actual database backup."""
    try:
        # Run pg_dump
        result = subprocess.run(
            ["pg_dump", db_url, "-f", str(backup_path)],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            # Get file size
            file_size = backup_path.stat().st_size
            
            # Update metadata
            metadata["status"] = "completed"
            metadata["size_bytes"] = file_size
            metadata["completed_at"] = datetime.utcnow().isoformat()
        else:
            # Backup failed
            metadata["status"] = "failed"
            metadata["error"] = result.stderr or "Unknown error"
        
    except subprocess.TimeoutExpired:
        metadata["status"] = "failed"
        metadata["error"] = "Backup timed out after 5 minutes"
    except Exception as e:
        metadata["status"] = "failed"
        metadata["error"] = str(e)
    
    # Save updated metadata
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

@router.get("/list", response_model=List[Dict[str, Any]])
async def list_backups(
    *,
    request: Request,
    _: bool = Depends(check_admin_access)
) -> List[Dict[str, Any]]:
    """
    List all available backups (admin only).
    """
    try:
        backups = []
        
        # List all .json metadata files
        for metadata_file in BACKUP_DIR.glob("*.json"):
            try:
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                    
                # Check if backup file exists
                backup_file = BACKUP_DIR / metadata["filename"]
                metadata["file_exists"] = backup_file.exists()
                
                if metadata["file_exists"] and metadata["size_bytes"] is None:
                    # Update size if not set
                    metadata["size_bytes"] = backup_file.stat().st_size
                
                backups.append(metadata)
            except Exception as e:
                print(f"Error reading metadata file {metadata_file}: {e}")
                continue
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return backups
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list backups: {str(e)}"
        )

@router.get("/download/{filename}")
async def download_backup(
    *,
    request: Request,
    filename: str,
    _: bool = Depends(check_admin_access)
):
    """
    Download a specific backup file (admin only).
    """
    try:
        # Validate filename (prevent path traversal)
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check if file exists
        backup_path = BACKUP_DIR / filename
        if not backup_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        # Return file
        return FileResponse(
            path=str(backup_path),
            filename=filename,
            media_type="application/sql"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download backup: {str(e)}"
        )

@router.delete("/delete/{filename}")
async def delete_backup(
    *,
    request: Request,
    filename: str,
    _: bool = Depends(check_admin_access)
) -> Dict[str, str]:
    """
    Delete a specific backup file (admin only).
    """
    try:
        # Validate filename (prevent path traversal)
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Delete backup file
        backup_path = BACKUP_DIR / filename
        if backup_path.exists():
            backup_path.unlink()
        
        # Delete metadata file
        metadata_path = BACKUP_DIR / f"{filename}.json"
        if metadata_path.exists():
            metadata_path.unlink()
        
        return {"message": f"Backup {filename} deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete backup: {str(e)}"
        )

@router.post("/restore/{filename}")
async def restore_backup(
    *,
    request: Request,
    background_tasks: BackgroundTasks,
    filename: str,
    _: bool = Depends(check_admin_access)
) -> Dict[str, Any]:
    """
    Restore database from a backup file (admin only).
    
    WARNING: This will replace the current database!
    The restore is performed asynchronously in the background.
    """
    try:
        # Validate filename
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
        
        # Check if file exists
        backup_path = BACKUP_DIR / filename
        if not backup_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        # Get database connection details
        db_url = get_db_connection_string()
        
        # Schedule restore in background
        background_tasks.add_task(
            perform_restore,
            db_url,
            backup_path
        )
        
        return {
            "message": "Database restore initiated",
            "filename": filename,
            "warning": "The database is being restored. The application may be unavailable during this process."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initiate restore: {str(e)}"
        )

async def perform_restore(db_url: str, backup_path: Path):
    """Perform the actual database restore."""
    try:
        # Run psql to restore
        result = subprocess.run(
            ["psql", db_url, "-f", str(backup_path)],
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            print(f"Restore error: {result.stderr}")
        else:
            print(f"Database restored successfully from {backup_path}")
            
    except subprocess.TimeoutExpired:
        print("Database restore timed out after 10 minutes")
    except Exception as e:
        print(f"Database restore failed: {e}")

@router.get("/status", response_model=Dict[str, Any])
async def get_backup_status(
    *,
    request: Request,
    _: bool = Depends(check_admin_access)
) -> Dict[str, Any]:
    """
    Get backup system status and statistics (admin only).
    """
    try:
        # Count backups
        total_backups = len(list(BACKUP_DIR.glob("*.sql")))
        
        # Calculate total size
        total_size = sum(f.stat().st_size for f in BACKUP_DIR.glob("*.sql"))
        
        # Get latest backup
        latest_backup = None
        for metadata_file in sorted(BACKUP_DIR.glob("*.json"), reverse=True):
            try:
                with open(metadata_file, "r") as f:
                    latest_backup = json.load(f)
                    break
            except:
                continue
        
        return {
            "backup_directory": str(BACKUP_DIR.absolute()),
            "total_backups": total_backups,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "latest_backup": latest_backup,
            "pg_dump_available": subprocess.run(
                ["which", "pg_dump"],
                capture_output=True
            ).returncode == 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get backup status: {str(e)}"
        )