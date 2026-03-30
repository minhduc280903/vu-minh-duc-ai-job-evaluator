from app.schemas.job import JobResponse, JobDetailResponse, JobListResponse
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.schemas.scraper import ScraperStartRequest, ScraperRunResponse, ScraperStatusResponse
from app.schemas.evaluator import EvalStatusResponse, EvalResult
from app.schemas.stats import DashboardStats, TierThresholds
from app.schemas.settings import (
    ProfileResponse, ProfileUpdate,
    NotificationSettingsResponse, NotificationSettingsUpdate,
    SchedulerConfigResponse, SchedulerConfigUpdate,
)
