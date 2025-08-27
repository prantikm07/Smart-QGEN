from fastapi import FastAPI, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session
import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Import our modules
from .database.database import get_db, create_tables, Paper, Question, SyllabusData, FileUpload, ExtractedText, StructuredSyllabus, GeneratedQuestions
from .modules.text_extractor import TextExtractor
from .modules.question_generator import QuestionGenerator
from .modules.nep_validator import NEPValidator
from .modules.pdf_creator import PDFCreator

# Create FastAPI app
app = FastAPI(title="AI Question Paper Generator", version="1.0.0")

# Create database tables
create_tables()

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

def chr_filter(value):
    """Custom filter to convert number to character"""
    return chr(int(value))

# Register the filter
templates.env.filters['chr'] = chr_filter

# Initialize modules
text_extractor = TextExtractor()
question_generator = QuestionGenerator()
nep_validator = NEPValidator()
pdf_creator = PDFCreator()

# Constants
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.png', '.jpg', '.jpeg'}

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page - file upload interface"""
    return templates.TemplateResponse("upload.html", {"request": request})

@app.post("/upload")
async def upload_files(
    request: Request,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Handle file upload, text extraction, and AI syllabus structuring"""
    
    session_id = str(uuid.uuid4())
    extracted_texts_list = [] # List to hold extracted text content
    processed_files_summary = [] # List to hold summary for response
    
    try:
        print(f"📁 Starting upload process for session: {session_id}")
        print(f"📄 Files to process: {[f.filename for f in files]}")
        
        # Create session directory
        session_dir = UPLOAD_DIR / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate and process each file
        for file in files:
            print(f"📄 Processing file: {file.filename}")
            
            # Validate file
            if not file.filename:
                continue
                
            file_extension = Path(file.filename).suffix.lower()
            if file_extension not in ALLOWED_EXTENSIONS:
                print(f"⚠️ Skipping unsupported file type: {file.filename}")
                continue
            
            # Read and validate file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                print(f"⚠️ File too large: {file.filename} ({len(content)} bytes)")
                continue
            
            if len(content) == 0:
                print(f"⚠️ Empty file: {file.filename}")
                continue
            
            # Save original file
            file_path = session_dir / file.filename
            with open(file_path, "wb") as buffer:
                buffer.write(content)
            
            print(f"💾 Saved file: {file_path}")

            # Save FileUpload entry
            file_upload_entry = FileUpload(
                session_id=session_id,
                original_filename=file.filename,
                file_path=str(file_path),
                file_type=file_extension.lstrip('.'),
                file_size=len(content)
            )
            db.add(file_upload_entry)
            db.flush() # Flush to get file_upload_entry.id
            
            # Extract text based on file type
            extracted_text_content = ""
            extraction_method = ""
            
            try:
                if file_extension == '.pdf':
                    extracted_text_content = text_extractor.extract_from_pdf(str(file_path))
                    extraction_method = "pdf_extraction"
                elif file_extension in {'.png', '.jpg', '.jpeg'}:
                    extracted_text_content = text_extractor.extract_from_image(str(file_path))
                    extraction_method = "ocr_extraction"
                elif file_extension == '.txt':
                    extracted_text_content = text_extractor.extract_from_text(str(file_path))
                    extraction_method = "direct_text"
                
                if extracted_text_content and len(extracted_text_content.strip()) > 0:
                    extracted_texts_list.append(extracted_text_content)
                    
                    # Save ExtractedText entry
                    extracted_text_entry = ExtractedText(
                        session_id=session_id,
                        file_id=file_upload_entry.id,
                        extracted_content=extracted_text_content,
                        extraction_method=extraction_method,
                        character_count=len(extracted_text_content)
                    )
                    db.add(extracted_text_entry)

                    processed_files_summary.append({
                        "filename": file.filename,
                        "size": len(content),
                        "type": file_extension,
                        "extraction_method": extraction_method,
                        "text_length": len(extracted_text_content)
                    })
                    print(f"✅ Extracted {len(extracted_text_content)} characters from {file.filename}")
                else:
                    print(f"⚠️ No text extracted from {file.filename}")
                    
            except Exception as e:
                print(f"❌ Error extracting text from {file.filename}: {e}")
                continue
        
        # Validate that we extracted some text
        if not extracted_texts_list:
            raise HTTPException(
                status_code=400, 
                detail="No text could be extracted from the uploaded files. Please check file formats and content."
            )
        
        # Combine all extracted texts
        combined_text = "\n\n=== FILE SEPARATOR ===\n\n".join(extracted_texts_list)
        print(f"📝 Combined text length: {len(combined_text)} characters")
        
        # Use AI to structure the syllabus
        print("🤖 Using AI to analyze and structure syllabus...")
        
        # Capture prompt and raw response for StructuredSyllabus
        prompt_for_ai = combined_text # Assuming combined_text is the primary input to the AI
        structured_data, raw_ai_response = await question_generator.structure_syllabus_with_raw_response(combined_text)
        
        # Validate structured data
        if not structured_data or not isinstance(structured_data, dict):
            raise HTTPException(status_code=500, detail="Failed to structure syllabus data")
        
        # Save to database using StructuredSyllabus
        structured_syllabus_entry = StructuredSyllabus(
            session_id=session_id,
            raw_syllabus_text=combined_text,
            gemini_prompt=prompt_for_ai,
            gemini_response=raw_ai_response,
            structured_json=json.dumps(structured_data, indent=2),
            processing_status="success"
        )
        db.add(structured_syllabus_entry)
        db.commit() # Commit all changes for this session
        
        print(f"💾 Session data saved: {session_id}")
        print(f"📚 Detected subject: {structured_data.get('subject', 'Unknown')}")
        print(f"🎯 Topics found: {len(structured_data.get('topics', []))}")
        
        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "redirect": f"/configure/{session_id}",
            "summary": {
                "files_processed": len(processed_files_summary),
                "total_text_length": len(combined_text),
                "subject_detected": structured_data.get("subject", "Unknown"),
                "topics_found": len(structured_data.get("topics", [])),
                "files_details": processed_files_summary
            }
        })
        
    except HTTPException:
        db.rollback() # Rollback on HTTPException
        raise
    except Exception as e:
        db.rollback() # Rollback on any other exception
        print(f"❌ Upload processing error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {str(e)}")

@app.get("/configure/{session_id}", response_class=HTMLResponse)
async def configure_paper(
    request: Request,
    session_id: str,
    db: Session = Depends(get_db)
):
    """Configuration page for paper settings"""
    
    try:
        print(f"📋 Loading configuration for session: {session_id}")
        
        # Get structured syllabus data
        structured_syllabus_entry = db.query(StructuredSyllabus).filter(
            StructuredSyllabus.session_id == session_id
        ).first()
        
        if not structured_syllabus_entry:
            print(f"❌ Structured syllabus data not found for session: {session_id}")
            raise HTTPException(status_code=404, detail="Session data not found or expired. Please re-upload your files.")
        
        # Parse structured data
        try:
            structured_data = json.loads(str(structured_syllabus_entry.structured_json))
        except json.JSONDecodeError as e:
            print(f"❌ Invalid structured JSON data for session {session_id}: {e}")
            raise HTTPException(status_code=500, detail="Invalid structured syllabus data in database.")
        
        # Validate structured data
        if not isinstance(structured_data, dict):
            raise HTTPException(status_code=500, detail="Invalid syllabus structure")
        
        topics = structured_data.get("topics", [])
        suggested_patterns = structured_data.get("question_patterns", [])
        subject = structured_data.get("subject", "Unknown Subject")
        
        print(f"📚 Subject: {subject}")
        print(f"🎯 Topics: {len(topics)}")
        print(f"📝 Suggested patterns: {len(suggested_patterns)}")
        
        return templates.TemplateResponse("configure.html", {
            "request": request,
            "session_id": session_id,
            "subject": subject,
            "topics": topics,
            "suggested_patterns": suggested_patterns,
            "learning_objectives": structured_data.get("learning_objectives", []),
            "key_concepts": structured_data.get("key_concepts", [])
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

@app.post("/generate/{session_id}")
async def generate_paper(
    session_id: str,
    title: str = Form(...),
    subject: str = Form(...),
    total_marks: int = Form(...),
    difficulty: int = Form(...),
    question_config: str = Form(...),
    priority_topics: str = Form(""),
    instructions: str = Form(""),
    db: Session = Depends(get_db)
):
    """Generate question paper using AI based on syllabus and configuration"""
    
    try:
        print(f"🚀 Starting question generation for session: {session_id}")
        print(f"📄 Paper: {title} | Subject: {subject} | Marks: {total_marks} | Difficulty: {difficulty}")
        
        # Get structured syllabus data
        structured_syllabus_entry = db.query(StructuredSyllabus).filter(
            StructuredSyllabus.session_id == session_id
        ).first()
        
        if not structured_syllabus_entry:
            raise HTTPException(status_code=404, detail="Structured syllabus data not found or expired. Please re-upload your files.")
        
        # Parse configuration
        try:
            config = json.loads(question_config)
            print(f"📋 Question configuration: {config}")
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=400, detail=f"Invalid question configuration: {e}")
        
        # Parse structured syllabus from the entry
        try:
            structured_syllabus = json.loads(str(structured_syllabus_entry.structured_json))
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=500, detail=f"Invalid structured syllabus data in database: {e}")
        
        # Validate configuration
        question_sets = config.get("question_sets", [])
        if not question_sets:
            raise HTTPException(status_code=400, detail="No question sets configured")
        
        # Process priority topics
        priority_topics_list = []
        if priority_topics:
            priority_topics_list = [topic.strip() for topic in priority_topics.split(",") if topic.strip()]
        
        print(f"🎯 Priority topics: {priority_topics_list}")
        print(f"📝 Instructions: {instructions}")
        
        # Generate questions using AI
        print("🤖 Generating questions with AI...")
        questions = await question_generator.generate_questions(
            syllabus=structured_syllabus,
            config=config,
            difficulty=difficulty,
            priority_topics=priority_topics_list,
            instructions=instructions
        )
        
        # Validate generated questions
        if not questions or len(questions) == 0:
            raise HTTPException(status_code=500, detail="No questions were generated")
        
        print(f"✅ Generated {len(questions)} questions")
        
        # Debug: Log first few questions
        for i, q in enumerate(questions[:3]):
            print(f"   Q{i+1}: {q.get('text', 'NO TEXT')[:80]}...")
        
        # Validate against NEP 2020
        try:
            nep_score = nep_validator.validate_paper(questions, config)
            print(f"📊 NEP 2020 compliance score: {nep_score.get('overall_score', 0)}")
        except Exception as e:
            print(f"⚠️ NEP validation failed: {e}")
            nep_score = {"overall_score": 0, "compliance_percentage": 0}
        
        # Save paper to database
        paper = Paper(
            title=title,
            subject=subject,
            total_marks=total_marks,
            difficulty_level=difficulty,
            paper_data=json.dumps(questions, indent=2)
        )
        db.add(paper)
        db.flush() # Flush to get paper.id before committing
        db.refresh(paper)
        
        # Save individual questions and GeneratedQuestions entry
        saved_questions = 0
        for i, q in enumerate(questions):
            try:
                question_obj = Question(
                    paper_id=paper.id,
                    question_text=q.get("text", "Question text missing"),
                    question_type=q.get("type", "unknown"),
                    marks=q.get("marks", 0),
                    difficulty=q.get("difficulty", difficulty),
                    topic=q.get("topic", "Unknown"),
                    answer=q.get("answer", ""),
                    options=json.dumps(q.get("options", []))
                )
                db.add(question_obj)
                saved_questions += 1
            except Exception as e:
                print(f"⚠️ Error saving question {i+1}: {e}")
                continue
        
        # Save GeneratedQuestions entry
        generated_questions_entry = GeneratedQuestions(
            paper_id=paper.id,
            session_id=session_id,
            question_data=json.dumps(questions, indent=2),
            generation_method="ai"
        )
        db.add(generated_questions_entry)

        db.commit()
        
        print(f"💾 Paper saved with ID: {paper.id}")
        print(f"💾 Saved {saved_questions}/{len(questions)} questions to database")
        
        return JSONResponse({
            "status": "success",
            "paper_id": paper.id,
            "questions": questions,
            "nep_score": nep_score,
            "redirect": f"/preview/{paper.id}",
            "summary": {
                "total_questions": len(questions),
                "questions_saved": saved_questions,
                "total_marks": total_marks,
                "nep_compliance": nep_score.get("compliance_percentage", 0)
            }
        })
        
    except HTTPException:
        db.rollback() # Rollback on HTTPException
        raise
    except Exception as e:
        db.rollback() # Rollback on any other exception
        print(f"❌ Question generation error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Question generation failed: {str(e)}")

@app.get("/preview/{paper_id}", response_class=HTMLResponse)
async def preview_paper(
    request: Request,
    paper_id: int,
    db: Session = Depends(get_db)
):
    """Preview generated question paper"""
    
    try:
        print(f"🖼️ Loading preview for paper ID: {paper_id}")
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Parse questions
        try:
            questions = json.loads(str(paper.paper_data))
        except json.JSONDecodeError as e:
            print(f"❌ Invalid paper data for paper {paper_id}: {e}")
            questions = []
        
        print(f"📄 Paper: {paper.title}")
        print(f"📚 Subject: {paper.subject}")
        print(f"📝 Questions: {len(questions)}")
        
        # Debug first few questions
        for i, q in enumerate(questions[:3]):
            print(f"   Q{i+1}: {q.get('text', 'NO TEXT')[:60]}...")
        
        return templates.TemplateResponse("preview.html", {
            "request": request,
            "paper": paper,
            "questions": questions
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Preview error: {e}")
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")

@app.post("/download/{paper_id}")
async def download_paper(
    paper_id: int,
    format: str = Form("pdf"),
    db: Session = Depends(get_db)
):
    """Download paper in specified format"""
    
    try:
        print(f"📥 Download request for paper {paper_id} in {format} format")
        
        paper = db.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        
        # Parse questions
        try:
            questions = json.loads(str(paper.paper_data))
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Invalid paper data")
        
        if not questions:
            raise HTTPException(status_code=500, detail="No questions found in paper")
        
        # Ensure download directory exists
        download_dir = Path("generated_papers")
        download_dir.mkdir(exist_ok=True)
        
        # Generate file based on format
        filename_base = f"{paper.title}_{paper.id}".replace(" ", "_")
        
        if format.lower() == "pdf":
            file_path = pdf_creator.create_pdf(paper, questions)
            media_type = "application/pdf"
            filename = f"{filename_base}.pdf"
        elif format.lower() == "docx":
            file_path = pdf_creator.create_docx(paper, questions)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{filename_base}.docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'pdf' or 'docx'")
        
        # Verify file was created
        if not os.path.exists(file_path):
            raise HTTPException(status_code=500, detail="File generation failed")
        
        print(f"✅ Generated {format} file: {file_path}")
        
        return FileResponse(
            file_path,
            media_type=media_type,
            filename=filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Download error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "error": "Page not found. Redirected to home page."
    }, status_code=404)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
