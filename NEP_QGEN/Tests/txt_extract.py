import sqlite3
import json
import os

def check_extraction():
    try:
        # Get the correct path to the database file
        # Go up one directory from tests/ to reach the root where the db file is located
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai_question_generator.db')
        
        # Check if database exists
        if not os.path.exists(db_path):
            print(f"❌ Database not found at: {db_path}")
            print("Available files in root directory:")
            root_dir = os.path.dirname(os.path.dirname(__file__))
            if os.path.exists(root_dir):
                for file in os.listdir(root_dir):
                    print(f"  - {file}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # First, let's check what tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📊 Available tables: {[table[0] for table in tables]}")
        
        # Get the most recent syllabus data
        cursor.execute("""
            SELECT session_id, extracted_text, structured_data, created_at 
            FROM syllabus_data 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        
        if result:
            session_id, extracted_text, structured_data, created_at = result
            
            print("\n📄 EXTRACTED TEXT FROM YOUR PDF:")
            print("="*60)
            print(f"Session ID: {session_id}")
            print(f"Created: {created_at}")
            print(f"Text Length: {len(extracted_text)} characters")
            print("="*60)
            print("EXTRACTED CONTENT:")
            print(extracted_text[:1000] + "..." if len(extracted_text) > 1000 else extracted_text)
            print("\n" + "="*60)
            
            print("\n🏗️ STRUCTURED DATA (What Gemini Should Have Created):")
            print("="*60)
            if structured_data:
                try:
                    structured = json.loads(structured_data)
                    print(json.dumps(structured, indent=2))
                except json.JSONDecodeError as je:
                    print(f"❌ JSON decode error: {je}")
                    print(f"Raw structured_data: {structured_data}")
            else:
                print("No structured data found")
            
        else:
            print("❌ No syllabus data found")
            
            # Let's check if there's any data in the table at all
            cursor.execute("SELECT COUNT(*) FROM syllabus_data")
            count = cursor.fetchone()[0]
            print(f"Total records in syllabus_data: {count}")
        
        conn.close()
        
    except sqlite3.Error as db_error:
        print(f"❌ Database Error: {db_error}")
    except Exception as e:
        print(f"❌ General Error: {e}")

if __name__ == "__main__":
    check_extraction()
