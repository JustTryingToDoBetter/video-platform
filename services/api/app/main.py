from fastapi import FastAPI
import os
from sqlalchemy import text
from app.db import engine

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

