import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from shared.schemas.schemas import JobRequest, JobResponse, JobStatus
from celery_app import celery_app
import logging

app = FastAPI(title="Story-to-Cartoon API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS_DIR = os.getenv("JOBS_DIR", "/jobs")

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure jobs directory exists
os.makedirs(JOBS_DIR, exist_ok=True)

@app.post("/generate", response_model=JobResponse)
async def generate_video(request: JobRequest):
    job_id = str(uuid.uuid4())
    job_dir = os.path.join(JOBS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    os.makedirs(os.path.join(job_dir, "scenes"), exist_ok=True)
    os.makedirs(os.path.join(job_dir, "final"), exist_ok=True)

    # Save inputs
    with open(os.path.join(job_dir, "input.json"), "w") as f:
        f.write(request.model_dump_json())
    
    with open(os.path.join(job_dir, "story.txt"), "w") as f:
        f.write(request.story)

    # Trigger Celery Task
    task = celery_app.send_task("tasks.process_story", args=[job_id, request.model_dump()])
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    # Check if job exists on disk
    job_dir = os.path.join(JOBS_DIR, job_id)
    if not os.path.exists(job_dir):
         raise HTTPException(status_code=404, detail="Job not found")

    # In a real app we'd check DB/Redis. For MVP, we might infer or retrieve from a status file.
    # For now, let's just return a placeholder. We will implement status tracking via Redis/File later.
    status_file = os.path.join(job_dir, "status.json")
    if os.path.exists(status_file):
        with open(status_file, "r") as f:
             # This file is written by the worker
             import json
             return json.load(f)
             
    return {"job_id": job_id, "status": "queued", "progress_current": 0, "progress_total": 0, "message": "Job queued"}

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    final_path = os.path.join(JOBS_DIR, job_id, "final", "final.mp4")
    if not os.path.exists(final_path):
        raise HTTPException(status_code=404, detail="Video not ready")
        
    from fastapi.responses import FileResponse
    return FileResponse(final_path, media_type="video/mp4", filename=f"cartoon_{job_id}.mp4")

@app.get("/")
def read_root():
    return {"message": "Story-to-Cartoon API is running"}
