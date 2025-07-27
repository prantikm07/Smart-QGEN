from fastapi import FastAPI, Request, Depends, UploadFile, File, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session
import os
import json
import uuid
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Constants
UPLOAD_DIR = Path("uploads")
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt', '.png', '.jpg', '.jpeg'}

# Import our modules
from .database.database import get_db, create_tables, Paper, Question, SyllabusData
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


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})


@app.post("/upload")
async def upload_files(
        request: Request,
        files: List[UploadFile] = File(...),
        db: Session = Depends(get_db)
):
    session_id = str(uuid.uuid4())
    extracted_texts = []

    try:
        # Create upload directory if it doesn't exist
        UPLOAD_DIR.mkdir(exist_ok=True)

        for file in files:
            if not file.filename:
                continue
                
            # Validate file extension
            file_ext = Path(file.filename).suffix.lower()
            if file_ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"File type {file_ext} not allowed"
                )

            # Create safe filename and path
            safe_filename = Path(session_id + "_" + Path(file.filename).name)
            file_path = UPLOAD_DIR / safe_filename

            # Read and validate file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File {file.filename} is too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
                )

            # Save file
            with open(file_path, "wb") as buffer:
                buffer.write(content)

            try:
                # Extract text based on file type
                if file_ext == '.pdf':
                    text = text_extractor.extract_from_pdf(str(file_path))
                elif file_ext in {'.png', '.jpg', '.jpeg'}:
                    text = text_extractor.extract_from_image(str(file_path))
                else:
                    text = text_extractor.extract_from_text(str(file_path))

                extracted_texts.append(text)
            finally:
                # Clean up uploaded file
                file_path.unlink(missing_ok=True)

        # Combine all texts
        combined_text = "\n\n".join(extracted_texts)

        # Structure the syllabus data using AI
        structured_data = await question_generator.structure_syllabus(combined_text)

        # Save to database
        syllabus_entry = SyllabusData(
            session_id=session_id,
            extracted_text=combined_text,
            structured_data=json.dumps(structured_data)
        )
        db.add(syllabus_entry)
        db.commit()

        return JSONResponse({
            "status": "success",
            "session_id": session_id,
            "redirect": f"/configure/{session_id}"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

 
@app.get("/configure/{session_id}", response_class=HTMLResponse)
async def configure_paper(
    request: Request,
    session_id: str,  # Make sure this parameter exists
    db: Session = Depends(get_db)
):
    
    # Get syllabus data
    syllabus_data = db.query(SyllabusData).filter(
        SyllabusData.session_id == session_id
    ).first()

    if not syllabus_data:
        raise HTTPException(status_code=404, detail="Session not found")

    structured_data = json.loads(str(syllabus_data.structured_data))


    return templates.TemplateResponse("configure.html", {
        "request": request,
        "session_id": session_id,  # Make sure this is passed
        "topics": structured_data.get("topics", []),
        "suggested_patterns": structured_data.get("question_patterns", [])
    })

@app.post("/generate/{session_id}")
async def generate_paper(
        session_id: str,
        title: str = Form(...),
        subject: str = Form(...),
        total_marks: int = Form(...),
        difficulty: int = Form(...),
        question_config: str = Form(...),  # JSON string
        priority_topics: str = Form(""),
        instructions: str = Form(""),
        db: Session = Depends(get_db)
):
    try:
        # Get syllabus data
        syllabus_data = db.query(SyllabusData).filter(
            SyllabusData.session_id == session_id
        ).first()

        if not syllabus_data:
            raise HTTPException(status_code=404, detail="Session not found")

        # Parse configuration
        config = json.loads(question_config)
        structured_syllabus = json.loads(str(syllabus_data.structured_data))


        print("About to generate questions...")
        print(f"Config: {config}")
        print(f"Syllabus keys: {list(structured_syllabus.keys())}")

        # Generate questions
        questions = await question_generator.generate_questions(
            syllabus=structured_syllabus,
            config=config,
            difficulty=difficulty,
            priority_topics=priority_topics.split(",") if priority_topics else [],
            instructions=instructions
        )
        print("=== DEBUG: Generated Questions ===")
        for i, q in enumerate(questions):
            print(f"Question {i+1}:")
            print(f"  Text: {q.get('text', 'NO TEXT')}")
            print(f"  Type: {q.get('type', 'NO TYPE')}")
            print(f"  Marks: {q.get('marks', 'NO MARKS')}")
            print("---")

        # Validate against NEP 2020
        nep_score = nep_validator.validate_paper(questions, config)

        # Save paper to database
        paper = Paper(
            title=title,
            subject=subject,
            total_marks=total_marks,
            difficulty_level=difficulty,
            paper_data=json.dumps(questions)
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

        # Save individual questions
        for i, q in enumerate(questions):
            question_obj = Question(
                paper_id=paper.id,
                question_text=q["text"],
                question_type=q["type"],
                marks=q["marks"],
                difficulty=q["difficulty"],
                topic=q.get("topic", ""),
                answer=q.get("answer", ""),
                options=json.dumps(q.get("options", []))
            )
            db.add(question_obj)

        db.commit()

        return JSONResponse({
            "status": "success",
            "paper_id": paper.id,
            "questions": questions,
            "nep_score": nep_score,
            "redirect": f"/preview/{paper.id}"
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/preview/{paper_id}", response_class=HTMLResponse)
async def preview_paper(
        request: Request,
        paper_id: int,
        db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    questions = json.loads(str(paper.paper_data))
    # Add this in preview_paper function, right before returning the template
    print("\n🖼️ DEBUG: Preview Template Data")
    print(f"Paper ID: {paper.id}")
    print(f"Paper Title: {paper.title}")
    print(f"Questions count: {len(questions)}")
    print("First few questions:")
    for i, q in enumerate(questions[:3], 1):
        print(f"  Q{i}: {q.get('text', 'NO TEXT')[:100]}...")


    return templates.TemplateResponse("preview.html", {
        "request": request,
        "paper": paper,
        "questions": questions
    })


@app.post("/download/{paper_id}")
async def download_paper(
        paper_id: int,
        format: str = Form("pdf"),
        db: Session = Depends(get_db)
):
    paper = db.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")

    questions = json.loads(str(paper.paper_data))

    if format == "pdf":
        file_path = pdf_creator.create_pdf(paper, questions)
        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=f"{paper.title.replace(' ', '_')}.pdf"
        )
    elif format == "docx":
        file_path = pdf_creator.create_docx(paper, questions)
        return FileResponse(
            file_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=f"{paper.title.replace(' ', '_')}.docx"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
