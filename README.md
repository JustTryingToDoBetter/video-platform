# Video Platform

Distributed video processing platform built with FastAPI, Docker, and microservices architecture.

## Current Scope
PLAT-001 initializes the monorepo and brings up a minimal API service.

## Run locally

```bash
docker compose up --build
http://localhost:8000/health/db

````



curl -X POST "http://localhost:8000/tasks/hello?name=Jevonte"