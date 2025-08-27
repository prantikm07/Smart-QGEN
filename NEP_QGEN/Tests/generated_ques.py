import sqlite3
import json
from datetime import datetime

def check_questions():
    try:
        # Connect to your database
        conn = sqlite3.connect('ai_question_generator.db')
        cursor = conn.cursor()
        
        # Get the most recent paper
        cursor.execute("""
            SELECT id, title, subject, total_marks, paper_data, created_at 
            FROM papers 
            ORDER BY created_at DESC 
            LIMIT 1
        """)
        
        paper = cursor.fetchone()
        
        if paper:
            paper_id, title, subject, total_marks, paper_data, created_at = paper
            print(f"📄 Most Recent Paper:")
            print(f"   ID: {paper_id}")
            print(f"   Title: {title}")
            print(f"   Subject: {subject}")
            print(f"   Total Marks: {total_marks}")
            print(f"   Created: {created_at}")
            print("\n" + "="*50)
            
            # Parse and display questions
            if paper_data:
                questions = json.loads(paper_data)
                print(f"📝 Questions Found: {len(questions)}")
                print("="*50)
                
                for i, q in enumerate(questions, 1):
                    print(f"\nQ{i}:")
                    print(f"   Text: {q.get('text', 'NO TEXT FOUND')}")
                    print(f"   Type: {q.get('type', 'NO TYPE')}")
                    print(f"   Marks: {q.get('marks', 'NO MARKS')}")
                    print(f"   Topic: {q.get('topic', 'NO TOPIC')}")
                    if q.get('options'):
                        print(f"   Options: {q.get('options')}")
                    print("-" * 30)
            else:
                print("❌ No questions data found in paper_data")
        else:
            print("❌ No papers found in database")
        
        # Also check individual questions table
        cursor.execute("""
            SELECT question_text, question_type, marks, topic
            FROM questions 
            ORDER BY id DESC 
            LIMIT 10
        """)
        
        individual_questions = cursor.fetchall()
        
        if individual_questions:
            print(f"\n🔍 Individual Questions Table (Last 10):")
            print("="*50)
            for i, (text, q_type, marks, topic) in enumerate(individual_questions, 1):
                print(f"{i}. {text} ({q_type}, {marks} marks, {topic})")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_questions()
