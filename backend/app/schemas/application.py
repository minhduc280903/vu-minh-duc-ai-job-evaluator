from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ApplicationCreate(BaseModel):
    job_id: str
    status: str = "saved"
    notes: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_notes: Optional[str] = None
    salary_offered: Optional[str] = None
    applied_at: Optional[datetime] = None


class ApplicationResponse(BaseModel):
    id: int
    job_id: str
    status: str
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    interview_date: Optional[datetime] = None
    interview_notes: Optional[str] = None
    salary_offered: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Joined job info
    job_title: Optional[str] = None
    job_company: Optional[str] = None
    job_platform: Optional[str] = None
    job_tier: Optional[str] = None
    job_score: Optional[int] = None
    job_url: Optional[str] = None

    class Config:
        from_attributes = True
