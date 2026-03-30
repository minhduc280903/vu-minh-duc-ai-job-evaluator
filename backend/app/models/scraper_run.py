from sqlalchemy import Column, Integer, Text, DateTime, func
from app.database import Base


class ScraperRun(Base):
    __tablename__ = "scraper_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="running")
    started_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime)
    jobs_found = Column(Integer, default=0)
    jobs_new = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    error_message = Column(Text)
    triggered_by = Column(Text, default="manual")
