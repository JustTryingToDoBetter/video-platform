from app.celery_app import celery_app
import json
from app.db import SessionLocal
from app.models import Job, JobStatus

@celery_app.task(name="app.process_hello_job")
def process_hello_job(job_id:int, name: str) -> str:
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
    