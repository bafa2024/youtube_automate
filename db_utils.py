import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = "ai_video_tool.db"

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            is_superuser INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            encrypted_api_key TEXT
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            file_id TEXT,
            filename TEXT,
            file_type TEXT,
            file_path TEXT,
            size INTEGER,
            upload_time TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        await db.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT,
            user_id INTEGER,
            status TEXT,
            message TEXT,
            created_at TEXT,
            progress INTEGER,
            result_path TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        await db.commit()

# User CRUD
async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE username = ?", (username,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE email = ?", (email,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def create_user(username: str, email: str, hashed_password: str, is_superuser: int = 0) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO users (username, email, hashed_password, is_superuser) VALUES (?, ?, ?, ?)",
            (username, email, hashed_password, is_superuser)
        )
        await db.commit()
        async with db.execute("SELECT last_insert_rowid()") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None

async def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

async def verify_user_password(username: str, password: str, verify_func) -> Optional[Dict[str, Any]]:
    user = await get_user_by_username(username)
    if user and verify_func(password, user['hashed_password']):
        return user
    return None

# FILE CRUD
async def create_file(user_id: int, file_id: str, filename: str, file_type: str, file_path: str, size: int, upload_time: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO files (user_id, file_id, filename, file_type, file_path, size, upload_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, file_id, filename, file_type, file_path, size, upload_time)
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

# JOB CRUD
async def create_job(job_id: str, user_id: int, status: str, message: str, created_at: str, progress: int, result_path: str = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO jobs (job_id, user_id, status, message, created_at, progress, result_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, user_id, status, message, created_at, progress, result_path)
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

async def update_job_status(job_id: str, status: str, message: str = None, progress: int = None, result_path: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        query = "UPDATE jobs SET status = ?, message = COALESCE(?, message), progress = COALESCE(?, progress), result_path = COALESCE(?, result_path) WHERE job_id = ?"
        await db.execute(query, (status, message, progress, result_path, job_id))
        await db.commit() 