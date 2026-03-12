from app.celery_app import celery_app
import json
from pathlib import Path
from app.db import SessionLocal
from app.models import Job, JobStatus

@celery_app.task(name="app.process_hello_job")
def process_hello_job(job_id: int, name: str) -> str:
    db = SessionLocal()

    try:
        job = db.get(Job, job_id)
        if not job:
            raise ValueError(f"Job with ID {job_id} not found")
        
        job.status = JobStatus.PROGRESS
        db.commit()

        result = f"hello, {name}!"

        job.status = JobStatus.SUCCESS
        job.result_payload = json.dumps({"result": result})
        job.error_message = None
        db.commit()

        return result
    except Exception as e:
        job = db.get(Job, job_id)
        if job:
            job.status = JobStatus.FAILURE
            job.result_payload = None
            job.error_message = str(e)
            db.commit()
        raise
    finally:
        db.close()



@celery_app.task(name="app.tasks.process_uploaded_video_job")
def process_uploaded_video_job(job_id: int) -> str:
    db = SessionLocal()

    try:
        job = db.get(Job, job_id) ## Fetch the job from the database using the provided job_id
        if job is None:
            raise ValueError(f"Job {job_id} not found")

        job.status = JobStatus.PROCESSING ## Update the job status to "processing"
        db.commit()

        if not job.file_path:
            raise ValueError("Job file_path is missing")

        file_path = Path(job.file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Uploaded file not found at {file_path}")

        file_metadata = {
            "original_filename": job.original_filename,
            "stored_filename": job.stored_filename,
            "file_path": str(file_path),
            "file_size_bytes": file_path.stat().st_size,
            "content_type": job.content_type,
            "exists": True,
        }

        job.status = JobStatus.COMPLETED
        job.result_payload = json.dumps(file_metadata)
        job.error_message = None
        db.commit()

        return f"Processed uploaded file for job {job_id}"

    except Exception as exc:
        job = db.get(Job, job_id)
        if job is not None:
            job.status = JobStatus.FAILED
            job.error_message = str(exc)
            db.commit()
        raise

    finally:
        db.close()