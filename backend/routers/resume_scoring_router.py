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

async def process_in_background(task_id: str, job_description: str, file_data_list: List[dict]):
    try:
        scorer = RateLimitedResumeScorer()

        # 1. Convert file_data_list to UploadFile objects
        upload_files = [
            UploadFile(filename=data["filename"], file=BytesIO(data["content"]))
            for data in file_data_list
        ]

        # 2. Extract text from PDFs
        extracted = await PDFProcessor.extract_from_upload_files(upload_files)

        successful_extractions = [r for r in extracted if r.get("extraction_success")]

        if not successful_extractions:
            processing_tasks[task_id]["status"] = "failed"
            processing_tasks[task_id]["error"] = "No resumes were successfully extracted."
            return

        # 3. Parse resumes (batch mode)
        
        parsed_data = ResumeParser.parse_multiple_resumes([
            r["text_content"] for r in successful_extractions
        ])

        parsed_resumes = []
        for i, parsed in enumerate(parsed_data):
            parsed_resumes.append({
                "filename": successful_extractions[i]["filename"],
                "parsed_data": parsed,
                "parsing_success": True
            })

        # 4. Score resumes
        results = await scorer.score_resume_batch(job_description, parsed_resumes)

        # 5. Save to in-memory task storage
        processing_tasks[task_id]["results"] = results["results"]
        processing_tasks[task_id]["status"] = "completed"
        processing_tasks[task_id]["completed_at"] = datetime.now().isoformat()

    except Exception as e:
        processing_tasks[task_id]["status"] = "failed"
        processing_tasks[task_id]["error"] = str(e)


# from fastapi import APIRouter, UploadFile, BackgroundTasks, HTTPException
# from fastapi import Form
# from pydantic import BaseModel
# from typing import List
# import uuid
# from datetime import datetime
# import logging

# # Import your services
# from services.pdf_processor import PDFProcessor
# from services.resume_parser import ResumeParser
# from services.resume_scoring_service import RateLimitedResumeScorer

# # Setup logging
# logger = logging.getLogger(__name__)

# router = APIRouter(prefix="/api/scoring", tags=["Resume Scoring"])

# # Task storage (use Redis in production)
# processing_tasks = {}

# class ScoringRequest(BaseModel):
#     job_description: str

# @router.post("/process-batch")
# async def process_resume_batch(
#     job_description: str = Form(...),
#     files: List[UploadFile] = None,
#     background_tasks: BackgroundTasks = None
# ):
#     """Upload multiple PDF resumes and process with rate limiting (4 resumes/minute)"""
    
#     if not files:
#         raise HTTPException(status_code=400, detail="No files uploaded")
    
#     # Validate file types - PDF only
#     for file in files:
#         if not file.filename.lower().endswith('.pdf'):
#             raise HTTPException(
#                 status_code=400, 
#                 detail=f"Unsupported file type: {file.filename}. Only PDF files are supported."
#             )
    
#     task_id = str(uuid.uuid4())
    
#     processing_tasks[task_id] = {
#         "status": "processing",
#         "total_files": len(files),
#         "processed": 0,
#         "estimated_time": f"{len(files) * 15 / 60:.1f} minutes",
#         "started_at": datetime.now().isoformat(),
#         "error": None,
#         "results": None
#     }
    
#     background_tasks.add_task(
#         process_batch_background, 
#         task_id, 
#         job_description, 
#         files
#     )
    
#     return {
#         "task_id": task_id,
#         "status": "processing_started",
#         "total_resumes": len(files),
#         "estimated_completion_time": f"{len(files) * 15 / 60:.1f} minutes",
#         "processing_rate": "4 resumes per minute"
#     }

# @router.get("/results/{task_id}")
# async def get_results(task_id: str):
#     """Get final results for completed task with successful JSON response"""
#     if task_id not in processing_tasks:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     task = processing_tasks[task_id]
    
#     # Return current status if not completed
#     if task["status"] not in ["completed", "failed"]:
#         return {
#             "task_id": task_id,
#             "status": task["status"],
#             "processed": task.get("processed", 0),
#             "total_files": task["total_files"],
#             "progress_percentage": round((task.get("processed", 0) / task["total_files"]) * 100, 1),
#             "message": "Processing in progress. Check back later for results."
#         }
    
#     # Return error details if failed
#     if task["status"] == "failed":
#         return {
#             "task_id": task_id,
#             "status": "failed",
#             "error": task.get("error", "Unknown error occurred"),
#             "failed_at": task.get("failed_at"),
#             "total_files": task["total_files"]
#         }
    
#     # Return successful results
#     if task["status"] == "completed" and task.get("results"):
#         return {
#             "task_id": task_id,
#             "status": "completed",
#             "completed_at": task.get("completed_at"),
#             "processing_summary": {
#                 "total_uploaded": task["total_files"],
#                 "successfully_processed": task["results"]["total_processed"],
#                 "processing_rate": task["results"]["processing_rate"],
#                 "processing_time": task.get("processing_time", "N/A")
#             },
#             "candidates": task["results"]["results"]
#         }
    
#     # Handle edge case - completed but no results
#     return {
#         "task_id": task_id,
#         "status": "completed",
#         "error": "No results generated - all files may have failed processing",
#         "completed_at": task.get("completed_at"),
#         "total_files": task["total_files"]
#     }

# @router.get("/status/{task_id}")
# async def get_task_status(task_id: str):
#     """Check processing status with detailed progress information"""
#     if task_id not in processing_tasks:
#         raise HTTPException(status_code=404, detail="Task not found")
    
#     task = processing_tasks[task_id]
    
#     return {
#         "task_id": task_id,
#         "status": task["status"],
#         "progress": {
#             "processed": task.get("processed", 0),
#             "total_files": task["total_files"],
#             "percentage": round((task.get("processed", 0) / task["total_files"]) * 100, 1),
#             "remaining": task["total_files"] - task.get("processed", 0)
#         },
#         "timing": {
#             "started_at": task["started_at"],
#             "estimated_completion": task["estimated_time"],
#             "completed_at": task.get("completed_at"),
#             "failed_at": task.get("failed_at")
#         },
#         "error": task.get("error")
#     }

# @router.get("/list-tasks")
# async def list_all_tasks():
#     """List all processing tasks (for debugging and monitoring)"""
#     return {
#         "total_tasks": len(processing_tasks),
#         "tasks": [
#             {
#                 "task_id": task_id,
#                 "status": task["status"],
#                 "total_files": task["total_files"],
#                 "processed": task.get("processed", 0),
#                 "started_at": task["started_at"],
#                 "completed_at": task.get("completed_at"),
#                 "error": task.get("error")
#             }
#             for task_id, task in processing_tasks.items()
#         ]
#     }

# @router.delete("/clear-tasks")
# async def clear_completed_tasks():
#     """Clear completed and failed tasks from memory"""
#     global processing_tasks
    
#     # Keep only processing tasks
#     active_tasks = {
#         task_id: task for task_id, task in processing_tasks.items()
#         if task["status"] not in ["completed", "failed"]
#     }
    
#     cleared_count = len(processing_tasks) - len(active_tasks)
#     processing_tasks = active_tasks
    
#     return {
#         "message": f"Cleared {cleared_count} completed/failed tasks",
#         "remaining_active_tasks": len(processing_tasks),
#         "cleared_tasks": cleared_count
#     }

# @router.get("/health")
# async def health_check():
#     """Health check endpoint for monitoring system status"""
#     return {
#         "status": "healthy",
#         "service": "resume_scoring_service",
#         "timestamp": datetime.now().isoformat(),
#         "active_tasks": len([task for task in processing_tasks.values() if task["status"] == "processing"]),
#         "total_tasks_in_memory": len(processing_tasks)
#     }

# async def process_batch_background(task_id: str, job_description: str, files: List[UploadFile]):
#     """Background task for processing resumes with enhanced error handling and logging"""
#     start_time = datetime.now()
    
#     try:
#         logger.info(f"Starting batch processing for task {task_id} with {len(files)} files")
        
#         # Read file contents immediately to avoid FastAPI UploadFile access issues
#         file_data = []
#         for file in files:
#             try:
#                 content = await file.read()
#                 file_data.append({
#                     "filename": file.filename,
#                     "content": content
#                 })
#                 logger.debug(f"Successfully read file: {file.filename}")
#             except Exception as e:
#                 logger.error(f"Failed to read file {file.filename}: {str(e)}")
#                 continue
        
#         if not file_data:
#             raise Exception("No files could be read from upload")
        
#         logger.info(f"Successfully read {len(file_data)} files for processing")
        
#         # Stage 1: Extract text from PDFs
#         processing_tasks[task_id]["status"] = "extracting_text"
#         logger.info(f"Stage 1: Starting text extraction for {len(file_data)} files")
        
#         pdf_processor = PDFProcessor()
#         extracted_data = pdf_processor.extract_from_file_contents(file_data)
        
#         successful_extractions = [d for d in extracted_data if d.get("extraction_success", False)]
#         logger.info(f"Text extraction completed: {len(successful_extractions)}/{len(extracted_data)} successful")
        
#         if not successful_extractions:
#             raise Exception("No files could be processed - all PDF text extractions failed")
        
#         # Stage 2: Parse resumes to structured JSON
#         processing_tasks[task_id]["status"] = "parsing_resumes"
#         logger.info(f"Stage 2: Starting resume parsing for {len(successful_extractions)} files")
        
#         resume_parser = ResumeParser()
#         parsed_resumes = resume_parser.parse_multiple_resumes(successful_extractions)
        
#         successful_parses = [r for r in parsed_resumes if r.get("parsing_success", False)]
#         logger.info(f"Resume parsing completed: {len(successful_parses)}/{len(parsed_resumes)} successful")
        
#         if not successful_parses:
#             raise Exception("No resumes could be parsed - all parsing attempts failed")
        
#         # Stage 3: Score using structured JSON data with rate limiting
#         processing_tasks[task_id]["status"] = "scoring_candidates"
#         logger.info(f"Stage 3: Starting candidate scoring for {len(successful_parses)} resumes")
        
#         scorer = RateLimitedResumeScorer()
#         results = await scorer.score_resume_batch(job_description, successful_parses)
        
#         # Calculate processing time
#         end_time = datetime.now()
#         processing_time = str(end_time - start_time).split('.')[0]  # Remove microseconds
        
#         # Update task with successful completion
#         processing_tasks[task_id].update({
#             "status": "completed",
#             "completed_at": end_time.isoformat(),
#             "processed": len(successful_parses),
#             "processing_time": processing_time,
#             "results": results
#         })
        
#         logger.info(f"Batch processing completed successfully for task {task_id}")
#         logger.info(f"Final results: {results['total_processed']} candidates processed and ranked")
        
#     except Exception as e:
#         error_msg = str(e)
#         logger.error(f"Background task error for task {task_id}: {error_msg}")
        
#         processing_tasks[task_id].update({
#             "status": "failed",
#             "error": error_msg,
#             "failed_at": datetime.now().isoformat()
#         })
