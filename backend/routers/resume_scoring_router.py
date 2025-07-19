from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException, Form, File
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime
import uuid

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
        content = await file.read()
        file_data_list.append({
            "filename": file.filename,
            "content": content
        })

    task_id = str(uuid.uuid4())

    processing_tasks[task_id] = {
        "status": "processing",
        "total_files": len(files),
        "processed": 0,
        "estimated_time": f"{len(files) * 15 / 60:.1f} minutes",
        "started_at": datetime.now().isoformat()
    }

    print("✅ Ready to start background task")

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
    """Get final results for completed task"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = processing_tasks[task_id]
    if task["status"] not in ["completed", "failed"]:
        raise HTTPException(
            status_code=400,
            detail=f"Processing not complete. Current status: {task['status']}"
        )

    return task

@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Check processing status"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    return processing_tasks[task_id]

@router.get("/list-tasks")
async def list_all_tasks():
    """List all processing tasks (for debugging)"""
    return {"tasks": processing_tasks}


# Background Task Logic
async def process_batch_background(task_id: str, job_description: str, file_data_list: List[Dict]):
    print(f"🚀 process_batch_background started for task: {task_id}")

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
