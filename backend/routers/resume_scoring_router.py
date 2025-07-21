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

load_dotenv()
router = APIRouter(prefix="/api/scoring", tags=["Resume Scoring"])

# In-memory task store (use Redis in production)
processing_tasks = {}

class ScoringRequest(BaseModel):
    job_description: str


@router.post("/process-batch")
async def process_resume_batch(
    job_description: str = Form(...),
    files: List[UploadFile] = File(...),

):
    """Upload multiple resumes and process with rate limiting (4 resumes/minute)"""

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    uploader = S3Uploader()

    # Testing the connection with S3 bucket
    print("🔧 Testing S3 connection before processing files...")
    if not uploader.test_s3_connection():
        raise RuntimeError("S3 connection test failed. Check your configuration.")
    else:
        print("✅ S3 connection test passed. Proceeding with file uploads...\n")

    # Generate folder name for this batch
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
            
            # Create S3 key with folder prefix
            s3_key = f"{folder_name}/{filename}"
            
            # Upload to S3 with folder structure
            url = uploader.upload_file(BytesIO(content), s3_key)
            
            # Store result
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
        "job_description": job_description[:100] + "..." if len(job_description) > 100 else job_description
    }

    logger.info("Ready to start background task")


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



