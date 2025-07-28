#!/usr/bin/env python3
"""
Migration script to convert multi-user database to single-user system
Run this script once to migrate your existing database
"""

import sqlite3
import os
import sys
from datetime import datetime

DB_PATH = "ai_video_tool.db"
BACKUP_PATH = f"ai_video_tool_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

def migrate_database():
    """Migrate database from multi-user to single-user system"""
    
    # Check if database exists
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Nothing to migrate.")
        return
    
    # Create backup
    print(f"Creating backup at {BACKUP_PATH}...")
    import shutil
    shutil.copy2(DB_PATH, BACKUP_PATH)
    print("Backup created successfully.")
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if migration is needed
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        users_table = cursor.fetchone()
        
        if not users_table:
            print("Database already migrated or fresh install. No migration needed.")
            return
        
        print("Starting migration...")
        
        # Create new settings table
        print("Creating settings table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            encrypted_api_key TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Migrate API key from first user if exists
        cursor.execute("SELECT encrypted_api_key FROM users WHERE encrypted_api_key IS NOT NULL LIMIT 1")
        api_key_row = cursor.fetchone()
        if api_key_row and api_key_row[0]:
            print("Migrating API key to settings table...")
            cursor.execute("""
                INSERT INTO settings (id, encrypted_api_key, created_at, updated_at) 
                VALUES (1, ?, ?, ?)
            """, (api_key_row[0], datetime.now().isoformat(), datetime.now().isoformat()))
        
        # Create new tables without user_id
        print("Creating new files table...")
        cursor.execute("""
        CREATE TABLE files_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT,
            filename TEXT,
            file_type TEXT,
            file_path TEXT,
            size INTEGER,
            upload_time TEXT
        )""")
        
        # Migrate files data
        print("Migrating files data...")
        cursor.execute("""
        INSERT INTO files_new (id, file_id, filename, file_type, file_path, size, upload_time)
        SELECT id, file_id, filename, file_type, file_path, size, upload_time FROM files
        """)
        
        # Create new jobs table
        print("Creating new jobs table...")
        cursor.execute("""
        CREATE TABLE jobs_new (
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
        
        # Migrate jobs data
        print("Migrating jobs data...")
        cursor.execute("""
        INSERT INTO jobs_new (id, job_id, status, message, created_at, progress, result_path, job_type, result)
        SELECT id, job_id, status, message, created_at, progress, result_path, job_type, result FROM jobs
        """)
        
        # Drop old tables and rename new ones
        print("Replacing old tables...")
        cursor.execute("DROP TABLE files")
        cursor.execute("DROP TABLE jobs")
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE files_new RENAME TO files")
        cursor.execute("ALTER TABLE jobs_new RENAME TO jobs")
        
        # Commit changes
        conn.commit()
        print("Migration completed successfully!")
        
        # Show statistics
        cursor.execute("SELECT COUNT(*) FROM files")
        file_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        
        print(f"\nMigration statistics:")
        print(f"- Files migrated: {file_count}")
        print(f"- Jobs migrated: {job_count}")
        print(f"- Backup saved at: {BACKUP_PATH}")
        
    except Exception as e:
        print(f"Error during migration: {e}")
        print("Rolling back changes...")
        conn.rollback()
        print(f"Migration failed. Your original database is intact.")
        print(f"A backup was created at: {BACKUP_PATH}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== Database Migration: Multi-user to Single-user ===")
    print("This script will migrate your database to a single-user system.")
    print("A backup will be created before any changes are made.")
    print("")
    
    response = input("Do you want to continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        sys.exit(0)
    
    migrate_database()