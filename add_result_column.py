import sqlite3

# Connect to the database
conn = sqlite3.connect('ai_video_tool.db')
cursor = conn.cursor()

try:
    # Check if the column already exists
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'result' not in columns:
        # Add the result column
        cursor.execute("ALTER TABLE jobs ADD COLUMN result TEXT")
        conn.commit()
        print("Successfully added 'result' column to jobs table")
    else:
        print("'result' column already exists in jobs table")
        
    # Also add job_type column if it doesn't exist
    if 'job_type' not in columns:
        cursor.execute("ALTER TABLE jobs ADD COLUMN job_type TEXT")
        conn.commit()
        print("Successfully added 'job_type' column to jobs table")
    else:
        print("'job_type' column already exists in jobs table")

except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()