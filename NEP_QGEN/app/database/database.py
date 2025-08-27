from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL - SQLite for simplicity
DATABASE_URL = "sqlite:///./ai_question_generator.db"

# Create engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database Models
class Paper(Base):
    __tablename__ = "papers"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    subject = Column(String)
    total_marks = Column(Integer)
    difficulty_level = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    paper_data = Column(Text)  # JSON string of questions
    file_path = Column(String, nullable=True)  # Path to generated PDF
    
    # Relationships
    questions = relationship("Question", back_populates="paper")
    generated_questions = relationship("GeneratedQuestions", back_populates="paper")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    question_text = Column(Text)
    question_type = Column(String)  # mcq, short, long
    marks = Column(Integer)
    difficulty = Column(Integer)
    topic = Column(String)
    answer = Column(Text, nullable=True)
    options = Column(Text, nullable=True)  # JSON for MCQ options
    
    # Relationships
    paper = relationship("Paper", back_populates="questions")

class SyllabusData(Base):
    __tablename__ = "syllabus_data"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    extracted_text = Column(Text)
    structured_data = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)

class FileUpload(Base):
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    original_filename = Column(String)
    file_path = Column(String)  # Where file is stored
    file_type = Column(String)  # pdf, txt, image
    file_size = Column(Integer)
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    extracted_texts = relationship("ExtractedText", back_populates="file")

class ExtractedText(Base):
    __tablename__ = "extracted_texts"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    file_id = Column(Integer, ForeignKey("file_uploads.id"))
    extracted_content = Column(Text)  # Raw extracted text
    extraction_method = Column(String)  # pdf, ocr, direct
    character_count = Column(Integer)
    extraction_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    file = relationship("FileUpload", back_populates="extracted_texts")

class StructuredSyllabus(Base):
    __tablename__ = "structured_syllabus"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    raw_syllabus_text = Column(Text)  # Combined extracted text
    gemini_prompt = Column(Text)  # The prompt sent to AI
    gemini_response = Column(Text)  # Raw AI response
    structured_json = Column(Text)  # Final structured JSON
    processing_status = Column(String)  # success, failed, fallback
    processing_timestamp = Column(DateTime, default=datetime.utcnow)

class GeneratedQuestions(Base):
    __tablename__ = "generated_questions"
    
    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer, ForeignKey("papers.id"))
    session_id = Column(String, index=True)
    question_data = Column(Text)  # Full question JSON
    generation_method = Column(String)  # ai, fallback, hybrid
    generation_timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    paper = relationship("Paper", back_populates="generated_questions")

# Create tables
def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")

# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions for database operations
def get_session_data(session_id: str, db_session):
    """Get all data for a session"""
    return {
        "syllabus": db_session.query(SyllabusData).filter(SyllabusData.session_id == session_id).first(),
        "files": db_session.query(FileUpload).filter(FileUpload.session_id == session_id).all(),
        "texts": db_session.query(ExtractedText).filter(ExtractedText.session_id == session_id).all(),
        "structured": db_session.query(StructuredSyllabus).filter(StructuredSyllabus.session_id == session_id).first()
    }

def cleanup_old_sessions(days_old: int = 7):
    """Clean up old session data"""
    from datetime import timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)
    
    db = SessionLocal()
    try:
        # Delete old syllabus data
        db.query(SyllabusData).filter(SyllabusData.created_at < cutoff_date).delete()
        
        # Delete old file uploads
        db.query(FileUpload).filter(FileUpload.upload_timestamp < cutoff_date).delete()
        
        # Delete old extracted texts
        db.query(ExtractedText).filter(ExtractedText.extraction_timestamp < cutoff_date).delete()
        
        # Delete old structured syllabus
        db.query(StructuredSyllabus).filter(StructuredSyllabus.processing_timestamp < cutoff_date).delete()
        
        db.commit()
        print(f"✅ Cleaned up sessions older than {days_old} days")
    except Exception as e:
        print(f"❌ Error cleaning up old sessions: {e}")
        db.rollback()
    finally:
        db.close()
