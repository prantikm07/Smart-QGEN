from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
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
    file_path = Column(String)  # Path to generated PDF


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    paper_id = Column(Integer)
    question_text = Column(Text)
    question_type = Column(String)  # mcq, short, long
    marks = Column(Integer)
    difficulty = Column(Integer)
    topic = Column(String)
    answer = Column(Text, nullable=True)
    options = Column(Text, nullable=True)  # JSON for MCQ options


class SyllabusData(Base):
    __tablename__ = "syllabus_data"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    extracted_text = Column(Text)
    structured_data = Column(Text)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
