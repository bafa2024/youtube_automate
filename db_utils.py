import aiosqlite
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = "ai_video_tool.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Create settings table for single-user API key storage
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            encrypted_api_key TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Create files table without user_id
        await db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            filename TEXT,
            file_type TEXT,
            file_path TEXT,
            size INTEGER,
            upload_time TEXT
        )""")
        
        # Create jobs table without user_id
        await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            status TEXT,
            message TEXT,
            created_at TEXT,
            progress INTEGER,
            result_path TEXT,
            job_type TEXT,
            result TEXT
        )""")
        await db.commit()

# Settings CRUD (for API key storage)
async def get_settings() -> Optional[Dict[str, Any]]:
    """Get the single settings record"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM settings WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_api_key(encrypted_api_key: str) -> bool:
    """Update the API key in settings"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Insert or update the single settings record
        await db.execute("""
            INSERT INTO settings (id, encrypted_api_key, updated_at) 
            VALUES (1, ?, ?) 
            ON CONFLICT(id) DO UPDATE SET 
                encrypted_api_key = excluded.encrypted_api_key,
                updated_at = excluded.updated_at
        """, (encrypted_api_key, datetime.now().isoformat()))
        await db.commit()
        return True

# FILE CRUD
async def create_file(file_id: str, filename: str, file_type: str, file_path: str, size: int, upload_time: str = None, file_metadata: Dict[str, Any] = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        if upload_time is None:
            upload_time = datetime.now().isoformat()
        await db.execute(
            "INSERT INTO files (file_id, filename, file_type, file_path, size, upload_time) VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, filename, file_type, file_path, size, upload_time)
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_file_by_id(file_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM files WHERE file_id = ?", (file_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_all_files(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """Get all files with pagination"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM files ORDER BY upload_time DESC LIMIT ? OFFSET ?",
            (limit, skip)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# JOB CRUD
async def create_job(job_id: str, status: str, message: str, created_at: str, progress: int, result_path: str = None, job_type: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO jobs (job_id, status, message, created_at, progress, result_path, job_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, status, message, created_at, progress, result_path, job_type)
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def update_job_status(job_id: str, status: str, message: str = None, progress: int = None, result_path: str = None, result_data: Dict[str, Any] = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        updates = ["status = ?"]
        params = [status]
        if message is not None:
            updates.append("message = ?")
            params.append(message)
        if progress is not None:
            updates.append("progress = ?")
            params.append(progress)
        if result_path is not None:
            updates.append("result_path = ?")
            params.append(result_path)
        if result_data is not None:
            updates.append("result = ?")
            params.append(json.dumps(result_data))
        params.append(job_id)
        
        await db.execute(
            f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?",
            params
        )
        await db.commit()

async def get_all_jobs(skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """Get all jobs with pagination"""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, skip)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

# Clean up old user-related functions (kept for backward compatibility, but simplified)
async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Deprecated - returns None since we don't have users anymore"""
    return None

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Deprecated - returns None since we don't have users anymore"""
    return None

async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Deprecated - returns None since we don't have users anymore"""
    return None

async def verify_user_password(username: str, password: str, verify_func) -> Optional[Dict[str, Any]]:
    """Deprecated - returns None since we don't have users anymore"""
    return None

async def update_user_password(user_id: int, new_hashed_password: str) -> bool:
    """Deprecated - returns False since we don't have users anymore"""
    return False

async def update_user_api_key(user_id: int, encrypted_api_key: str) -> bool:
    """Deprecated - use update_api_key instead"""
    return await update_api_key(encrypted_api_key)

# Backward compatibility wrapper
async def get_user_jobs(user_id: int, skip: int = 0, limit: int = 10) -> List[Dict[str, Any]]:
    """Get all jobs - user_id parameter is ignored"""
    return await get_all_jobs(skip, limit)