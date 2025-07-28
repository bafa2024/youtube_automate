import sqlite3
import json
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_PATH = "ai_video_tool.db"

def dict_factory(cursor, row):
    """Convert SQLite rows to dictionaries"""
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# Synchronous versions of database functions for background tasks

def get_file_by_id_sync(file_id: str) -> Optional[Dict[str, Any]]:
    """Synchronous version of get_file_by_id"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM files WHERE file_id = ?", (file_id,))
        return cursor.fetchone()

def get_job_by_id_sync(job_id: str) -> Optional[Dict[str, Any]]:
    """Synchronous version of get_job_by_id"""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = dict_factory
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        return cursor.fetchone()

def update_job_status_sync(job_id: str, status: str, message: str = None, progress: int = None, result_path: str = None, result: Dict[str, Any] = None):
    """Synchronous version of update_job_status"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if result:
            query = "UPDATE jobs SET status = ?, message = COALESCE(?, message), progress = COALESCE(?, progress), result_path = COALESCE(?, result_path), result = ? WHERE job_id = ?"
            cursor.execute(query, (status, message, progress, result_path, json.dumps(result), job_id))
        else:
            query = "UPDATE jobs SET status = ?, message = COALESCE(?, message), progress = COALESCE(?, progress), result_path = COALESCE(?, result_path) WHERE job_id = ?"
            cursor.execute(query, (status, message, progress, result_path, job_id))
        conn.commit()

def create_job_sync(job_id: str, status: str, message: str, created_at: str, progress: int, result_path: str = None, job_type: str = None) -> int:
    """Synchronous version of create_job"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO jobs (job_id, status, message, created_at, progress, result_path, job_type) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (job_id, status, message, created_at, progress, result_path, job_type)
        )
        conn.commit()
        return cursor.lastrowid