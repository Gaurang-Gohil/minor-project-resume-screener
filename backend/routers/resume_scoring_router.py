from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Form, File
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import uuid
import logging
logger = logging.getLogger(__name__)

# Import services
from services.pdf_processor import PDFProcessor
from services.resume_parser import ResumeParser
from services.resume_scoring_service import RateLimitedResumeScorer

router = APIRouter(prefix="/api/scoring", tags=["Resume Scoring"])

# In-memory task store (use Redis in production)
processing_tasks = {}

class ScoringRequest(BaseModel):
    job_description: str

@router.post("/process-batch")
async def process_resume_batch(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload multiple resumes and process with rate limiting (4 resumes/minute)"""

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    # Read file contents into memory (UploadFile gets closed after the request ends)
    file_data_list = []

    for file in files:
        try:
            # Read content
            content = await file.read()

            if not content or len(content) < 100:  
                raise ValueError("File is empty or too short")

            # Validate PDF header
            if not content.startswith(b"%PDF"):
                raise ValueError("Not a valid PDF file")

            file_data_list.append({
                "filename": file.filename,
                "content": content
            })

        except Exception as e:
            logger.error(f"Error processing file {file.filename}: {str(e)}")
            continue

    task_id = str(uuid.uuid4())

    processing_tasks[task_id] = {
        "status": "processing",
        "total_files": len(files),
        "processed": 0,
        "estimated_time": f"{len(files) * 15 / 60:.1f} minutes",
        "started_at": datetime.now().isoformat()
    }

    logger.info("Ready to start background task")

    background_tasks.add_task(
        process_batch_background,
        task_id,
        job_description,
        file_data_list
    )

    return {
        "task_id": task_id,
        "status": "processing_started",
        "total_resumes": len(files),
        "estimated_completion_time": f"{len(files) * 15 / 60:.1f} minutes",
        "processing_rate": "4 resumes per minute"
    }

@router.get("/results/{task_id}")
async def get_results(task_id: str):
    """Get final scoring results after processing is complete"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]

    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Results not available. Current status: {task['status']}"
        )

    return {
        "task_id": task_id,
        "results": task.get("results", {})
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


@router.get("/list-tasks")
async def list_all_tasks():
    """List all processing tasks (for debugging)"""
    return {"tasks": processing_tasks}


# Background Task Logic
async def process_batch_background(task_id: str, job_description: str, file_data_list: List[Dict]):
    logger.info(" process_batch_background started for task: {task_id}")

    try:
        processing_tasks[task_id]["status"] = "extracting_text"

        # Stage 1: Extract text
        pdf_processor = PDFProcessor()
        extracted_data = pdf_processor.extract_from_memory(file_data_list)

        processing_tasks[task_id]["status"] = "parsing_resumes"

        # Stage 2: Parse resumes
        resume_parser = ResumeParser()
        parsed_resumes = resume_parser.parse_multiple_resumes(extracted_data)

        processing_tasks[task_id]["status"] = "scoring_candidates"

        # Stage 3: Score resumes
        scorer = RateLimitedResumeScorer()
        results = await scorer.score_resume_batch(job_description, parsed_resumes)

        processing_tasks[task_id].update({
            "status": "completed",
            "completed_at": datetime.now().isoformat(),
            "processed": len(results["results"]),  # ✅ FIXED LINE
            "results": results
        })

    except Exception as e:
        processing_tasks[task_id].update({
            "status": "failed",
            "error": str(e),
            "failed_at": datetime.now().isoformat()
        })
