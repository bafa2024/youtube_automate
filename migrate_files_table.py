import sqlite3

con = sqlite3.connect('ai_video_tool.db')
cur = con.cursor()

# 1. Rename the old table
cur.execute("ALTER TABLE files RENAME TO files_old;")

# 2. Create the new table (user_id is nullable, no foreign key)
cur.execute("""
CREATE TABLE files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    file_id TEXT,
    filename TEXT,
    file_type TEXT,
    file_path TEXT,
    size INTEGER,
    upload_time TEXT
);
""")

# 3. Copy data from old table to new table
cur.execute("""
INSERT INTO files (id, user_id, file_id, filename, file_type, file_path, size, upload_time)
SELECT id, user_id, file_id, filename, file_type, file_path, size, upload_time FROM files_old;
""")

# 4. Drop the old table
cur.execute("DROP TABLE files_old;")

con.commit()
con.close()
print("Migration complete: files table now allows user_id to be NULL.") 