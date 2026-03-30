from sqlalchemy import Column, Integer, Text, DateTime, func
from app.database import Base


class NotificationSettings(Base):
    __tablename__ = "notification_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    channel = Column(Text, nullable=False)
    enabled = Column(Integer, default=0)
    config = Column(Text)  # JSON
    min_tier = Column(Text, default="A")
    daily_digest = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
