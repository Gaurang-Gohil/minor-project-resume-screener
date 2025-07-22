from fastapi import APIRouter, UploadFile, HTTPException, Form, File
from pydantic import BaseModel
from typing import List
from datetime import datetime
import uuid
import logging
logger = logging.getLogger(__name__)
from io import BytesIO
from dotenv import load_dotenv
from services.s3_service import S3Uploader
from fastapi import BackgroundTasks

from services.pdf_processor import PDFProcessor
from services.resume_parser import ResumeParser
from services.resume_scoring_service import RateLimitedResumeScorer


from services.gemini_client import GeminiClient
gemini = GeminiClient()
result = []

load_dotenv()
router = APIRouter(prefix="/api/scoring", tags=["Resume Scoring"])

# In-memory task store (use Redis in production)
processing_tasks = {}

class ScoringRequest(BaseModel):
    job_description: str


@router.post("/process-batch")
async def process_resume_batch(
    background_tasks: BackgroundTasks,
    job_description: str = Form(...),
    files: List[UploadFile] = File(...),
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    uploader = S3Uploader()

    print("🔧 Testing S3 connection before processing files...")
    if not uploader.test_s3_connection():
        raise RuntimeError("S3 connection test failed. Check your configuration.")
    else:
        print("✅ S3 connection test passed. Proceeding with file uploads...\n")

    folder_name = S3Uploader.generate_folder_name(job_description)
    print(f"📁 Creating folder: {folder_name}")

    file_data_list = []

    for file in files:
        filename = file.filename or f"resume_{uuid.uuid4()}.pdf"

        try:
            content = await file.read()
            if len(content) < 100 or not content.startswith(b"%PDF"):
                logger.warning("Skip %s – file is empty or too small", filename)
                continue

            s3_key = f"{folder_name}/{filename}"
            url = uploader.upload_file(BytesIO(content), s3_key)

            file_data_list.append({
                "filename": filename,
                "content": content,
                "s3_url": url,
                "s3_key": s3_key,
                "folder": folder_name
            })
            logger.info("Uploaded %s → %s", filename, url)

        except Exception as exc:
            logger.error("Failed processing %s: %s", filename, exc)
            continue

    task_id = str(uuid.uuid4())

    processing_tasks[task_id] = {
        "status": "processing",
        "total_files": len(file_data_list),
        "processed": 0,
        "estimated_time": f"{len(file_data_list) * 15 / 60:.1f} minutes",
        "started_at": datetime.now().isoformat(),
        "folder_name": folder_name,
        "job_description": job_description[:100] + "..." if len(job_description) > 100 else job_description,
        "results": []
    }

    logger.info("Starting background processing task...")

    background_tasks.add_task(
        process_in_background,
        task_id,
        job_description,
        file_data_list
    )

    return {
        "task_id": task_id,
        "status": "processing_started",
        "total_resumes": len(file_data_list),
        "estimated_completion_time": f"{len(file_data_list) * 15 / 60:.1f} minutes",
        "processing_rate": "4 resumes per minute",
        "folder_name": folder_name,
        "s3_organization": f"Files organized in: {folder_name}/"
    }

@router.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get final scoring results with candidate rankings"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]

    if task["status"] == "failed":
        return {
            "task_id": task_id,
            "status": "failed",
            "error": task.get("error"),
            "failed_at": task.get("failed_at")
        }

    if task["status"] != "completed":
        return {
            "task_id": task_id,
            "status": task["status"],
            "message": f"Processing in progress. Current stage: {task['status']}",
            "progress": f"{task.get('processed', 0)}/{task.get('total_files', 0)} files"
        }

    # Return complete results with candidate scores
    return {
        "task_id": task_id,
        "status": "completed",
        "completed_at": task.get("completed_at"),
        "folder_name": task.get("folder_name"),
        "processing_summary": {
            "total_uploaded": task["total_files"],
            "successfully_processed": task.get("processed", 0),
            "processing_rate": "4 resumes per minute"
        },
        "candidates": task["results"]["results"] if task.get("results") else []
    }


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Check processing status and progress (no full results)"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]
    
    # Only return metadata, not full results
    return {
        "task_id": task_id,
        "status": task["status"],
        "total_files": task.get("total_files", 0),
        "processed": task.get("processed", 0),
        "estimated_time": task.get("estimated_time", ""),
        "started_at": task.get("started_at", ""),
        "completed_at": task.get("completed_at", None),
        "error": task.get("error", None)
    }

async def process_in_background(task_id: str, job_description: str, file_data_list: List[dict]):
    """Fixed background processing with proper AI pipeline integration"""
    try:
        logger.info(f"Starting background processing for task {task_id}")
        
        # Update status to extracting text
        processing_tasks[task_id]["status"] = "extracting_text"
        
        # 1. Initialize services (INSTANCE METHODS, not class methods)
        pdf_processor = PDFProcessor()
        resume_parser = ResumeParser()
        scorer = RateLimitedResumeScorer()
        
        # 2. Extract text from PDF contents (not UploadFile objects)
        logger.info("Starting PDF text extraction...")
        extracted_data = pdf_processor.extract_from_file_contents(file_data_list)
        
        successful_extractions = [r for r in extracted_data if r.get("extraction_success")]
        logger.info(f"Text extraction: {len(successful_extractions)}/{len(extracted_data)} successful")
        
        if not successful_extractions:
            processing_tasks[task_id]["status"] = "failed"
            processing_tasks[task_id]["error"] = "No PDFs were successfully extracted for text."
            return
        
        # 3. Parse resumes to structured JSON using Gemini API
        processing_tasks[task_id]["status"] = "parsing_resumes"
        logger.info("Starting resume parsing with Gemini API...")
        
        parsed_resumes = resume_parser.parse_multiple_resumes(successful_extractions)
        
        successful_parses = [r for r in parsed_resumes if r.get("parsing_success")]
        logger.info(f"Resume parsing: {len(successful_parses)}/{len(parsed_resumes)} successful")
        
        if not successful_parses:
            processing_tasks[task_id]["status"] = "failed"
            processing_tasks[task_id]["error"] = "No resumes could be parsed by Gemini API."
            return
        
        # 4. Score resumes against job description with rate limiting
        processing_tasks[task_id]["status"] = "scoring_candidates"
        logger.info("Starting candidate scoring with Gemini API...")
        
        results = await scorer.score_resume_batch(job_description, successful_parses)
        
        # 5. Save complete results
        processing_tasks[task_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processed": len(successful_parses),
            "results": results  # This contains the full scoring results
        })
        
        logger.info(f"Background processing completed successfully for task {task_id}")
        logger.info(f"Final results: {results['total_processed']} candidates processed and scored")
        
    except Exception as e:
        logger.error(f"Background processing error for task {task_id}: {str(e)}")
        processing_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })

