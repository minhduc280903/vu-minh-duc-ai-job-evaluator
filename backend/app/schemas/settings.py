from pydantic import BaseModel
from typing import Optional, Dict, Any


class ProfileResponse(BaseModel):
    data: Dict[str, Any]


class ProfileUpdate(BaseModel):
    data: Dict[str, Any]


class NotificationSettingsResponse(BaseModel):
    id: int
    channel: str
    enabled: bool
    config: Optional[Dict[str, str]] = None
    min_tier: str = "A"
    daily_digest: bool = True

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    config: Optional[Dict[str, str]] = None
    min_tier: Optional[str] = None
    daily_digest: Optional[bool] = None


class SchedulerConfigResponse(BaseModel):
    id: int
    task_name: str
    enabled: bool
    cron_expression: str
    last_run: Optional[str] = None
    next_run: Optional[str] = None

    class Config:
        from_attributes = True


class SchedulerConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
