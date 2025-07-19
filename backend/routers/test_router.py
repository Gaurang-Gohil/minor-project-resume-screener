from fastapi import APIRouter, UploadFile, File, Form
from services.gemini_client import GeminiClient
from services.pdf_processor import PDFProcessor
from services.resume_parser import ResumeParser
import os

router = APIRouter(prefix="/api/test", tags=["Testing"])

@router.get("/gemini")
def test_gemini():
    """Test Gemini API connection"""
    gemini = GeminiClient()
    result = gemini.test_connection()
    return {"response": result}

@router.post("/extract-pdf")
async def extract_pdf_text(file: UploadFile = File(...)):
    """Extract text from single PDF file"""
    contents = await file.read()
    
    # Save temporary file
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as f:
        f.write(contents)
    
    try:
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(temp_filename)
        return {"filename": file.filename, "extracted_text": text}
    finally:
        # Clean up temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@router.post("/parse-resume")
async def parse_single_resume(resume_text: str = Form(...)):
    """Parse single resume text to structured JSON"""
    parser = ResumeParser()
    result = parser.parse_resume(resume_text)
    return {"parsed": result}

@router.post("/parse-resume-file")
async def parse_resume_from_file(file: UploadFile = File(...)):
    """Extract text from PDF and parse to structured JSON"""
    contents = await file.read()
    
    # Save temporary file
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as f:
        f.write(contents)
    
    try:
        # Extract text
        pdf_processor = PDFProcessor()
        text = pdf_processor.extract_text(temp_filename)
        
        # Parse resume
        parser = ResumeParser()
        result = parser.parse_resume(text)
        
        return {
            "filename": file.filename,
            "extracted_text_length": len(text),
            "parsed_data": result
        }
    finally:
        # Clean up temp file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)
