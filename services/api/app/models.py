from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase

class Base(DeclarativeBase):
    pass


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"

class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True) ## Auto-incrementing primary key
    task_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True) ## Celery task ID
    job_type: Mapped[str] = mapped_column(String(50), nullable=False) ## Type
    status: Mapped[JobStatus] = mapped_column(
        SQLEnum(JobStatus, name="job_status"), 
        nullable=False, 
        default=JobStatus.QUEUED
    ) ## Job status

    input_payload: Mapped[str | None] = mapped_column(Text, nullable=True) ## Input data for the job
    result_payload: Mapped[str | None] = mapped_column(Text, nullable=True) ## Result data from the job
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True) ## Error message if job failed

    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True) ## Original filename for file processing jobs
    stored_filename: Mapped[str | None] = mapped_column(Text, nullable=True) ## Stored filename for file processing jobs
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True) ## File path for file processing jobs
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True) ## File size in bytes for file processing jobs
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True) ## MIME type for file processing jobs

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow) ## Timestamp when the job was created
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow) ## Timestamp when the job was last updated