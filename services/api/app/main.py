import os

from celery.result import AsyncResult
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.celery_app import celery_app
from app.db import engine
from app.redis_client import redis_client
from app.tasks import say_hello
from app.db import get_db
from app.models import Base, Job, JobStatus





app = FastAPI(title=os.getenv('APP_NAME', 'Video Platform API'), version='1.0.0')

@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get('/health')
def health_check() -> dict[str, str]:
    return {"status": "ok", "services": "api", "environment": os.getenv('APP_ENV', 'development')}

@app.get('/health/db')
def db_healthcheck() -> dict[str, str]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "services": "api", "database": "connected"}
    except Exception as e:
        return {"status": "error", "services": "api", "database": "disconnected", "error": str(e)}


@app.get('/health/redis')
def redis_healthcheck() -> dict[str, str]:
    try:
        redis_client.ping() ## This will raise an exception if Redis is not available
        return {"status": "ok", "services": "api", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "services": "api", "redis": "disconnected", "error": str(e)}


@app.post("/tasks/hello")
def create_hello_task(name: str = "Jevonte") -> dict[str, str]:
    task = say_hello.delay(name)
    return {
        "task_id": task.id,
        "status": "queued",
    }


@app.get("/tasks/{task_id}")
def get_task_status(task_id: str) -> dict[str, str]:
    task_result = AsyncResult(task_id, app=celery_app)

    response: dict[str, str | None] = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None
    }
    
    if task_result.status == "SUCCESS":
        response["result"] = str(task_result.result)
    
    return response

@app.post("/jobs/hello")
def create_hello_job(name: str = "Jevonte", db: Session = Depends(get_db)) -> dict[str, str]:
    input_payload = f'{{"name": "{name}"}}'
    job = Job(
        job_type="hello",
        status=JobStatus.QUEUED,
        input_payload=json.dumps(input_payload),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "status": job.status,
    }

@app.get("/jobs/{job_id}")
def get_job(job_id:int, db: Session = Depends(get_db)) -> dict:
    job = db.get(Job, job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "job_type": job.job_type,
        "status": job.status,
        "input_payload": job.input_payload,
        "result_payload": job.result_payload,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }