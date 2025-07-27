import asyncio
import aiosqlite
import os

async def debug_files():
    """Debug uploaded files in the database"""
    async with aiosqlite.connect('ai_video_tool.db') as db:
        db.row_factory = aiosqlite.Row
        
        print("=== All Files in Database ===")
        async with db.execute("SELECT * FROM files ORDER BY upload_time DESC LIMIT 10") as cursor:
            rows = await cursor.fetchall()
            for row in rows:
                file_data = dict(row)
                print(f"\nFile ID: {file_data['file_id']}")
                print(f"Filename: {file_data['filename']}")
                print(f"Type: {file_data['file_type']}")
                print(f"Path: {file_data['file_path']}")
                print(f"Size: {file_data['size']} bytes")
                print(f"Upload Time: {file_data['upload_time']}")
                
                # Check if file exists
                if file_data['file_path']:
                    exists = os.path.exists(file_data['file_path'])
                    print(f"File exists on disk: {exists}")
                    if exists and file_data['file_type'] == 'script':
                        try:
                            with open(file_data['file_path'], 'r', encoding='utf-8') as f:
                                content = f.read()
                                print(f"Content preview: {content[:100]}...")
                        except Exception as e:
                            print(f"Error reading file: {e}")
                else:
                    print("File path is None!")
                
                print("-" * 50)

if __name__ == "__main__":
    asyncio.run(debug_files())