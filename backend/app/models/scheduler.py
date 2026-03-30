from sqlalchemy import Column, Integer, Text, DateTime, func
from app.database import Base


class SchedulerConfig(Base):
    __tablename__ = "scheduler_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_name = Column(Text, nullable=False, unique=True)
    enabled = Column(Integer, default=0)
    cron_expression = Column(Text, nullable=False)
    last_run = Column(DateTime)
    next_run = Column(DateTime)
    config = Column(Text)  # JSON
