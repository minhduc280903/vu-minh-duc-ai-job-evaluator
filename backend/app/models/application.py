from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, func
from app.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(Text, ForeignKey("jobs.id"), nullable=False)
    status = Column(Text, nullable=False, default="saved")
    applied_at = Column(DateTime)
    notes = Column(Text)
    interview_date = Column(DateTime)
    interview_notes = Column(Text)
    salary_offered = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
