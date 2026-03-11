import os

from celery.result import AsyncResult
from fastapi import FastAPI
from sqlalchemy import text

from app.celery_app import celery_app
from app.db import engine
from app.redis_client import redis_client
from app.tasks import say_hello


app = FastAPI(title=os.getenv('APP_NAME', 'Video Platform API'), version='1.0.0')

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