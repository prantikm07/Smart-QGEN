import sqlite3
import json
import os

def debug_complete_pipeline():
    """Debug the complete data processing pipeline"""
    
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ai_question_generator.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get latest session
        cursor.execute("SELECT session_id FROM syllabus_data ORDER BY created_at DESC LIMIT 1")
        result = cursor.fetchone()
        
        if not result:
            print("❌ No sessions found")
            return
            
        session_id = result[0]
        print(f"🔍 Debugging Session: {session_id}")
        print("="*80)
        
        # 1. Check uploaded files
        cursor.execute("SELECT * FROM file_uploads WHERE session_id = ?", (session_id,))
        files = cursor.fetchall()
        
        print(f"📁 UPLOADED FILES ({len(files)}):")
        for file_data in files:
            print(f"   • {file_data[2]} ({file_data[4]}) - {file_data[5]} bytes")
            print(f"     Stored at: {file_data[3]}")
            
        # 2. Check extracted texts
        cursor.execute("SELECT * FROM extracted_texts WHERE session_id = ?", (session_id,))
        texts = cursor.fetchall()
        
        print(f"\n📝 EXTRACTED TEXTS ({len(texts)}):")
        for text_data in texts:
            print(f"   • Method: {text_data[4]}")
            print(f"   • Length: {text_data[5]} characters")
            print(f"   • Preview: {text_data[3][:200]}...")
            
        # 3. Check structured syllabus
        cursor.execute("SELECT * FROM structured_syllabus WHERE session_id = ?", (session_id,))
        structured = cursor.fetchone()
        
        if structured:
            print(f"\n🏗️ STRUCTURED SYLLABUS:")
            print(f"   • Status: {structured[6]}")
            print(f"   • AI Response Length: {len(structured[4])} chars")
            structured_json = json.loads(structured[5])
            print(f"   • Subject: {structured_json.get('subject', 'Unknown')}")
            print(f"   • Topics: {[t['name'] for t in structured_json.get('topics', [])]}")
            
        # 4. Check generated questions
        cursor.execute("SELECT * FROM papers WHERE id IN (SELECT paper_id FROM generated_questions WHERE session_id = ?)", (session_id,))
        papers = cursor.fetchall()
        
        print(f"\n📋 GENERATED PAPERS ({len(papers)}):")
        for paper in papers:
            questions = json.loads(paper[5])  # paper_data
            print(f"   • Paper: {paper[1]} ({paper[2]})")
            print(f"   • Questions: {len(questions)}")
            print(f"   • Sample: {questions[0]['text'][:100] if questions else 'No questions'}...")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Debug error: {e}")

if __name__ == "__main__":
    debug_complete_pipeline()
