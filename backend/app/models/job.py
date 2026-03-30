from sqlalchemy import Column, Text, Integer, DateTime, func
from app.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Text, primary_key=True)
    platform = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    company = Column(Text)
    url = Column(Text)
    summary = Column(Text)
    deadline = Column(Text)
    views = Column(Integer, default=0)
    published_at = Column(Text)
    salary = Column(Text)
    domain = Column(Text)
    level = Column(Text)
    location = Column(Text)
    skills = Column(Text)
    requirements = Column(Text)
    benefits = Column(Text)
    description = Column(Text)
    raw_data = Column(Text)
    relevance_score = Column(Integer, default=-1)
    evaluation_reason = Column(Text)
    keyword_score = Column(Integer, default=-1)
    llm_score = Column(Integer, default=-1)
    final_score = Column(Integer, default=-1)
    llm_rationale = Column(Text)
    llm_pros = Column(Text)
    llm_cons = Column(Text)
    scraped_at = Column(DateTime, server_default=func.now())
