import json
import os

from celery.result import AsyncResult
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.db import engine, get_db
from app.models import Base, Job, JobStatus
from app.redis_client import redis_client
from app.tasks import process_hello_job
from app.storage import ensure_upload_dir

app = FastAPI(
    title=os.getenv("APP_NAME", "Video Platform API"),
    version="0.1.0",
)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    if ensure_upload_dir:
        ensure_upload_dir()


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "api",
        "environment": os.getenv("APP_ENV", "development"),
    }


@app.get("/health/db")
def database_healthcheck() -> dict[str, str]:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "service": "api", "database": "connected"}
    except Exception as exc:
        return {
            "status": "error",
            "service": "api",
            "database": "disconnected",
            "detail": str(exc),
        }


@app.get("/health/redis")
def redis_healthcheck() -> dict[str, str]:
    try:
        redis_client.ping()
        return {"status": "ok", "service": "api", "redis": "connected"}
    except Exception as exc:
        return {
            "status": "error",
            "service": "api",
            "redis": "disconnected",
            "detail": str(exc),
        }


@app.post("/jobs/hello")
def create_hello_job(name: str = "Jevonte", db: Session = Depends(get_db)) -> dict:
    input_payload = {"name": name}

    job = Job(
        job_type="hello",
        status=JobStatus.QUEUED,
        input_payload=json.dumps(input_payload),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    task = process_hello_job.delay(job.id, name)

    job.task_id = task.id
    db.commit()
    db.refresh(job)

    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "status": job.status.value,
    }


@app.get("/jobs/{job_id}")
def get_job(job_id: int, db: Session = Depends(get_db)) -> dict:
    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "task_id": job.task_id,
        "job_type": job.job_type,
        "status": job.status.value,
        "input_payload": job.input_payload,
        "result_payload": job.result_payload,
        "error_message": job.error_message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
    }


@app.get("/tasks/{task_id}")
def get_task_status(task_id: str) -> dict[str, str | None]:
    task_result = AsyncResult(task_id, app=celery_app)

    response: dict[str, str | None] = {
        "task_id": task_id,
        "status": task_result.status,
        "result": None,
    }

    if task_result.successful():
        response["result"] = str(task_result.result)

    return response