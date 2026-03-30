# Job Finder v5 Pro — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the CLI-only job finder (v4) into a full-stack web application with FastAPI backend, React dark-themed dashboard, application tracking, auto-scheduling, and Telegram/Email notifications.

**Architecture:** FastAPI REST API + WebSocket backend serving a React SPA. SQLite with SQLAlchemy ORM. Existing 6 scrapers refactored into a BaseScraper pattern. APScheduler for background tasks. Zustand + React Query for frontend state.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy, APScheduler, Ollama | React 18, TypeScript, Vite, TailwindCSS, Recharts, @hello-pangea/dnd

**Spec:** `docs/superpowers/specs/2026-03-14-job-finder-v5-complete-system-design.md`

---

## File Structure

### Backend (`backend/`)

| File | Responsibility |
|------|---------------|
| `backend/app/main.py` | FastAPI app creation, CORS, lifespan (start scheduler), mount routers |
| `backend/app/config.py` | Pydantic Settings loading from `.env` |
| `backend/app/database.py` | SQLAlchemy engine, session maker, Base, get_db dependency |
| `backend/app/models/__init__.py` | Re-export all models |
| `backend/app/models/job.py` | Job ORM model (maps existing jobs table) |
| `backend/app/models/application.py` | Application ORM model |
| `backend/app/models/scraper_run.py` | ScraperRun ORM model |
| `backend/app/models/notification.py` | NotificationSettings ORM model |
| `backend/app/models/scheduler.py` | SchedulerConfig ORM model |
| `backend/app/schemas/job.py` | JobResponse, JobListResponse, JobFilters Pydantic schemas |
| `backend/app/schemas/application.py` | ApplicationCreate, ApplicationUpdate, ApplicationResponse |
| `backend/app/schemas/scraper.py` | ScraperRunResponse, ScraperStartRequest |
| `backend/app/schemas/evaluator.py` | EvalStatus, EvalResult |
| `backend/app/schemas/stats.py` | DashboardStats, TierDistribution, PlatformStats |
| `backend/app/schemas/settings.py` | ProfileSchema, NotificationSettingsSchema, SchedulerConfigSchema |
| `backend/app/api/__init__.py` | Router aggregation |
| `backend/app/api/jobs.py` | GET /api/jobs, GET /api/jobs/{id}, GET /api/jobs/stats |
| `backend/app/api/scrapers.py` | POST /api/scrapers/run, GET /api/scrapers/status, GET /api/scrapers/history, POST /api/scrapers/stop |
| `backend/app/api/evaluator.py` | POST /api/evaluator/keyword, POST /api/evaluator/llm, GET /api/evaluator/status, POST /api/evaluator/reset |
| `backend/app/api/applications.py` | CRUD for applications |
| `backend/app/api/settings.py` | Profile, notification, scheduler settings endpoints |
| `backend/app/api/websocket.py` | WebSocket manager and endpoint |
| `backend/app/services/job_service.py` | Job queries, filtering, pagination, stats |
| `backend/app/services/scraper_service.py` | Orchestrate scraper runs, manage state |
| `backend/app/services/evaluator_service.py` | Keyword scoring + LLM evaluation orchestration |
| `backend/app/services/application_service.py` | Application CRUD operations |
| `backend/app/services/notification_service.py` | Telegram + Email sending |
| `backend/app/services/scheduler_service.py` | APScheduler job management |
| `backend/app/scrapers/__init__.py` | Scraper registry |
| `backend/app/scrapers/base.py` | Abstract BaseScraper class |
| `backend/app/scrapers/ybox.py` | Ybox scraper (refactored from v4) |
| `backend/app/scrapers/vietnamworks.py` | VietnamWorks scraper (refactored from v4) |
| `backend/app/scrapers/topcv.py` | TopCV scraper (refactored from v4) |
| `backend/app/scrapers/itviec.py` | ITviec scraper (refactored from v4) |
| `backend/app/scrapers/careerviet.py` | CareerViet scraper (refactored from v4) |
| `backend/app/scrapers/joboko.py` | Joboko scraper (refactored from v4) |
| `backend/app/core/__init__.py` | Core module init |
| `backend/app/core/scoring.py` | Keyword scoring engine (from v4 ai_evaluator.py) + tier thresholds |
| `backend/app/core/llm.py` | OllamaClient with retry, exponential backoff, JSON validation |
| `backend/app/core/scheduler.py` | APScheduler setup with SQLite job store |
| `backend/requirements.txt` | Python dependencies |
| `backend/.env.example` | Environment variable template |

### Frontend (`frontend/`)

| File | Responsibility |
|------|---------------|
| `frontend/package.json` | Dependencies and scripts |
| `frontend/vite.config.ts` | Vite config with API proxy |
| `frontend/tailwind.config.js` | Tailwind with dark theme colors |
| `frontend/postcss.config.js` | PostCSS for Tailwind |
| `frontend/index.html` | HTML entry point |
| `frontend/src/main.tsx` | React entry, QueryClient, Router |
| `frontend/src/App.tsx` | Route definitions |
| `frontend/src/types/index.ts` | TypeScript interfaces for all data models |
| `frontend/src/api/client.ts` | Axios instance + all API functions |
| `frontend/src/api/websocket.ts` | WebSocket client with auto-reconnect |
| `frontend/src/stores/appStore.ts` | Zustand store for UI state (sidebar, modals) |
| `frontend/src/components/layout/Layout.tsx` | Sidebar + main content wrapper |
| `frontend/src/components/layout/Sidebar.tsx` | Navigation sidebar with scheduler status |
| `frontend/src/components/ui/TierBadge.tsx` | Tier S/A/B/C colored badge |
| `frontend/src/components/ui/StatsCard.tsx` | Stat card with icon, value, label |
| `frontend/src/components/ui/LoadingSpinner.tsx` | Loading indicator |
| `frontend/src/pages/Dashboard.tsx` | Dashboard with stats, charts, top matches |
| `frontend/src/pages/Jobs.tsx` | Job list with filters and detail panel |
| `frontend/src/pages/Applications.tsx` | Kanban board for application tracking |
| `frontend/src/pages/Scrapers.tsx` | Scraper control panel and history |
| `frontend/src/pages/Settings.tsx` | Profile, notifications, scheduler config |
| `frontend/src/index.css` | Global styles, Tailwind imports, dark theme base |

---

## Chunk 1: Backend Foundation

### Task 1: Project scaffold and configuration

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/.env`

- [ ] **Step 1: Create backend directory structure**

```bash
cd C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4
mkdir -p backend/app/{models,schemas,api,services,scrapers,core}
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/api/__init__.py
touch backend/app/services/__init__.py
touch backend/app/scrapers/__init__.py
touch backend/app/core/__init__.py
```

- [ ] **Step 2: Write requirements.txt**

```
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
aiosqlite==0.20.0
pydantic-settings==2.5.0
python-dotenv==1.0.1
aiohttp==3.10.0
beautifulsoup4==4.12.0
apscheduler==3.10.4
openpyxl==3.1.5
httpx==0.27.0
python-multipart==0.0.9
websockets==12.0
```

- [ ] **Step 3: Write .env.example and .env**

```env
# backend/.env.example
DATABASE_URL=sqlite:///./jobs.db
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
LLM_TIMEOUT=120
LLM_THRESHOLD=25
LLM_MAX_RETRIES=3
LLM_BATCH_SIZE=1
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=
SMTP_PASSWORD=
AUTO_SCRAPE_CRON=0 6 * * *
AUTO_EVALUATE_CRON=0 7 * * *
DAILY_REPORT_CRON=0 8 * * *
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:5173
PROFILE_PATH=../user_profile.json
```

Copy to `.env` with same content.

- [ ] **Step 4: Write config.py**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./jobs.db"

    # Ollama LLM
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    llm_timeout: int = 120
    llm_threshold: int = 25
    llm_max_retries: int = 3
    llm_batch_size: int = 1

    # Notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_email: str = ""
    smtp_password: str = ""

    # Scheduler
    auto_scrape_cron: str = "0 6 * * *"
    auto_evaluate_cron: str = "0 7 * * *"
    daily_report_cron: str = "0 8 * * *"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # Profile
    profile_path: str = "../user_profile.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
```

- [ ] **Step 5: Write database.py**

```python
# backend/app/database.py
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


# SQLite needs check_same_thread=False for FastAPI
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_engine(settings.database_url, connect_args=connect_args)

# Enable WAL mode for SQLite (better concurrent reads)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 6: Verify backend loads**

```bash
cd backend
pip install -r requirements.txt
python -c "from app.config import settings; print(settings.database_url)"
```

Expected: `sqlite:///./jobs.db`

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: scaffold backend with config and database setup"
```

---

### Task 2: SQLAlchemy ORM models

**Files:**
- Create: `backend/app/models/job.py`
- Create: `backend/app/models/application.py`
- Create: `backend/app/models/scraper_run.py`
- Create: `backend/app/models/notification.py`
- Create: `backend/app/models/scheduler.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Write Job model (maps existing jobs table)**

```python
# backend/app/models/job.py
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
```

- [ ] **Step 2: Write Application model**

```python
# backend/app/models/application.py
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
```

- [ ] **Step 3: Write ScraperRun model**

```python
# backend/app/models/scraper_run.py
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
```

- [ ] **Step 4: Write NotificationSettings model**

```python
# backend/app/models/notification.py
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
```

- [ ] **Step 5: Write SchedulerConfig model**

```python
# backend/app/models/scheduler.py
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
```

- [ ] **Step 6: Write models __init__.py**

```python
# backend/app/models/__init__.py
from app.models.job import Job
from app.models.application import Application
from app.models.scraper_run import ScraperRun
from app.models.notification import NotificationSettings
from app.models.scheduler import SchedulerConfig

__all__ = ["Job", "Application", "ScraperRun", "NotificationSettings", "SchedulerConfig"]
```

- [ ] **Step 7: Verify models create tables**

```bash
cd backend
python -c "
from app.database import engine, Base
from app.models import *
Base.metadata.create_all(bind=engine)
print('Tables created:', list(Base.metadata.tables.keys()))
"
```

Expected: `Tables created: ['jobs', 'applications', 'scraper_runs', 'notification_settings', 'scheduler_config']`

Note: The `jobs` table already exists from v4. SQLAlchemy's `create_all` will skip it and only create the new tables.

- [ ] **Step 8: Commit**

```bash
git add backend/app/models/
git commit -m "feat: add SQLAlchemy ORM models for all tables"
```

---

### Task 3: Pydantic schemas

**Files:**
- Create: `backend/app/schemas/job.py`
- Create: `backend/app/schemas/application.py`
- Create: `backend/app/schemas/scraper.py`
- Create: `backend/app/schemas/evaluator.py`
- Create: `backend/app/schemas/stats.py`
- Create: `backend/app/schemas/settings.py`
- Modify: `backend/app/schemas/__init__.py`

- [ ] **Step 1: Write job schemas**

```python
# backend/app/schemas/job.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobResponse(BaseModel):
    id: str
    platform: str
    title: str
    company: Optional[str] = None
    url: Optional[str] = None
    salary: Optional[str] = None
    location: Optional[str] = None
    level: Optional[str] = None
    skills: Optional[str] = None
    deadline: Optional[str] = None
    keyword_score: int = -1
    llm_score: int = -1
    final_score: int = -1
    tier: Optional[str] = None
    llm_rationale: Optional[str] = None
    llm_pros: Optional[str] = None
    llm_cons: Optional[str] = None
    scraped_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class JobDetailResponse(JobResponse):
    summary: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    benefits: Optional[str] = None
    domain: Optional[str] = None
    views: int = 0
    published_at: Optional[str] = None


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
```

- [ ] **Step 2: Write application schemas**

```python
# backend/app/schemas/application.py
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
```

- [ ] **Step 3: Write scraper schemas**

```python
# backend/app/schemas/scraper.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ScraperStartRequest(BaseModel):
    platforms: List[str] = ["all"]


class ScraperRunResponse(BaseModel):
    id: int
    platform: str
    status: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    jobs_found: int = 0
    jobs_new: int = 0
    jobs_updated: int = 0
    error_message: Optional[str] = None
    triggered_by: str = "manual"

    class Config:
        from_attributes = True


class ScraperStatusResponse(BaseModel):
    is_running: bool
    current_platforms: List[str] = []
    progress: dict = {}
```

- [ ] **Step 4: Write evaluator schemas**

```python
# backend/app/schemas/evaluator.py
from pydantic import BaseModel


class EvalStatusResponse(BaseModel):
    is_running: bool
    total_jobs: int
    keyword_scored: int
    llm_evaluated: int
    llm_candidates: int
    pending_llm: int


class EvalResult(BaseModel):
    score: int = -1
    rationale: str = ""
    pros: str = "[]"
    cons: str = "[]"
    error: str = ""
```

- [ ] **Step 5: Write stats schemas**

```python
# backend/app/schemas/stats.py
from pydantic import BaseModel
from typing import Dict


class TierThresholds(BaseModel):
    S: int = 75
    A: int = 50
    B: int = 35
    C: int = 1


class DashboardStats(BaseModel):
    total_jobs: int
    tier_s: int
    tier_a: int
    tier_b: int
    tier_c: int
    by_platform: Dict[str, int]
    evaluated: int
    pending_eval: int
    avg_score: float
    new_today: int
    applications_count: int
    interviews_count: int
    thresholds: TierThresholds = TierThresholds()
```

- [ ] **Step 6: Write settings schemas**

```python
# backend/app/schemas/settings.py
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
```

- [ ] **Step 7: Write schemas __init__.py**

```python
# backend/app/schemas/__init__.py
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
```

- [ ] **Step 8: Verify schemas import**

```bash
cd backend
python -c "from app.schemas import *; print('All schemas loaded OK')"
```

- [ ] **Step 9: Commit**

```bash
git add backend/app/schemas/
git commit -m "feat: add Pydantic schemas for all API endpoints"
```

---

### Task 4: Core modules — scoring engine, LLM client, tier constants

**Files:**
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/scoring.py`
- Create: `backend/app/core/llm.py`

- [ ] **Step 1: Write scoring.py — port keyword_score_job from v4**

Port the entire `keyword_score_job()` function from `ai_evaluator.py` (lines 81-248) into `backend/app/core/scoring.py`. Add tier constants and helper.

```python
# backend/app/core/scoring.py
import json
import re

# Tier thresholds — single source of truth (referenced by spec Section 3.0)
TIER_THRESHOLDS = {"S": 75, "A": 50, "B": 35, "C": 1}


def get_tier(score: int) -> str:
    """Return tier letter for a given score."""
    if score >= TIER_THRESHOLDS["S"]:
        return "S"
    elif score >= TIER_THRESHOLDS["A"]:
        return "A"
    elif score >= TIER_THRESHOLDS["B"]:
        return "B"
    elif score >= TIER_THRESHOLDS["C"]:
        return "C"
    return "C"


def load_profile(profile_path: str) -> dict:
    """Load user profile JSON."""
    with open(profile_path, "r", encoding="utf-8") as f:
        return json.load(f)


def keyword_score_job(job: dict, profile: dict) -> int:
    """Score a single job based on keyword matching. Returns 0-100.
    Ported directly from v4 ai_evaluator.py."""
    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()
    desc = (job.get("description") or "").lower()
    reqs = (job.get("requirements") or "").lower()
    skills_field = (job.get("skills") or "").lower()
    benefits = (job.get("benefits") or "").lower()
    location = (job.get("location") or "").lower()
    level = (job.get("level") or "").lower()

    all_text = f"{desc} {reqs} {skills_field} {benefits}"
    title_company = f"{title} {company}"
    score = 0

    # 0. IRRELEVANT TITLE PENALTY (early exit)
    irrelevant_titles = [
        "frontend", "front-end", "react native", "ios dev", "android dev",
        "mobile dev", "flutter", "swift dev", "kotlin dev", "react dev",
        "angular", "vue.js dev", "nextjs",
        "backend", "back-end", "fullstack", "full-stack", "full stack",
        "devops", "sre ", "site reliability", "infrastructure",
        "platform engineer", "cloud engineer", "system admin",
        "network engineer", "security engineer", "penetration tester",
        "ui/ux", "ux designer", "ui designer", "graphic design", "content",
        "marketing", "seo ", "social media", "copywriter",
        "sales", "telesales", "tư vấn bán", "account manager",
        "customer success", "chăm sóc khách", "tư vấn viên",
        "game dev", "game design", "unity dev", "unreal",
        "embedded", "firmware", "hardware",
        "teacher", "giáo viên", "gia sư", "giảng dạy",
        "hr ", "nhân sự", "hành chính", "admin", "receptionist",
        "lễ tân", "thư ký",
        "manual tester", "manual qa", "qa engineer", "qc engineer",
        "qa automation", "quality assurance", "test engineer",
        "qa manager", "tester",
        "project manager", "scrum master", "delivery manager",
        "product owner", "technical lead", "tech lead",
        "java developer", ".net developer", "php developer",
        "c# developer", "c++ developer", "ruby developer",
        "golang developer", "go developer", "rust developer",
        "nodejs developer", "node.js developer",
        "software engineer", "lập trình viên",
    ]
    for kw in irrelevant_titles:
        if kw in title:
            return 0

    # 1. Title Match (max 25)
    title_score = 0
    for tier_name, tier in profile["title_keywords"].items():
        if tier_name.startswith("_"):
            continue
        if not isinstance(tier, dict) or "keywords" not in tier:
            continue
        for kw in tier["keywords"]:
            if kw.lower() in title:
                title_score = max(title_score, tier["score"])
        if title_score > 0:
            break
    score += title_score

    # 2. Skill Match (max 25)
    skill_score = 0
    for lv in ["high_value", "medium_value", "low_value"]:
        group = profile["skill_keywords"][lv]
        for kw in group["keywords"]:
            if kw.lower() in all_text or kw.lower() in skills_field:
                skill_score += group["points_each"]
    score += min(skill_score, 25)

    # 3. Industry Match (max 25)
    industry_score = 0
    for tier_name in ["tier_s_finance", "tier_a_finance_domain", "tier_b_tech"]:
        tier = profile["industry_keywords"][tier_name]
        for kw in tier["keywords"]:
            if kw.lower() in title_company or kw.lower() in all_text:
                industry_score = max(industry_score, tier["points"])
                break
        if industry_score >= 20:
            break
    score += industry_score

    # 4. Work Style (max 15, can go negative)
    style_score = 0
    for kw in profile["work_style"]["positive"]["keywords"]:
        if kw.lower() in all_text:
            style_score += profile["work_style"]["positive"]["points_each"]
    for kw in profile["work_style"]["negative"]["keywords"]:
        if kw.lower() in all_text:
            style_score += profile["work_style"]["negative"]["points_each"]
    score += max(min(style_score, 15), -10)

    # 5. Experience Level (max 10, can go very negative)
    exp_score = 0
    exp_text = f"{title} {reqs} {level}"

    if level:
        year_match = re.search(r'(\d+)\s*[-–]\s*(\d+)', level)
        if year_match:
            min_years = int(year_match.group(1))
        else:
            single_match = re.search(r'(\d+)', level)
            min_years = int(single_match.group(1)) if single_match else 0

        if min_years >= 5:
            exp_score = -25
        elif min_years >= 3:
            exp_score = -15
        elif min_years >= 2:
            exp_score = -5
        elif min_years <= 1:
            exp_score = 10

    if 'giám đốc' in title or 'director' in title or 'head of' in title or 'trưởng phòng' in title:
        exp_score = min(exp_score, -20)
    elif 'senior' in title or 'lead' in title or 'principal' in title or 'staff' in title:
        exp_score = min(exp_score, -10)

    if not level and exp_score == 0:
        for level_name in ["ideal", "acceptable", "stretch"]:
            level_cfg = profile["experience_level"][level_name]
            for kw in level_cfg["keywords"]:
                if kw.lower() in exp_text:
                    exp_score = level_cfg["points"]
                    break
            if exp_score != 0:
                break

    score += exp_score

    # 6. Location Bonus (Hanoi +5)
    hanoi_keywords = ["hà nội", "ha noi", "hanoi", "cầu giấy", "nam từ liêm",
                      "thanh xuân", "đống đa", "hoàn kiếm", "ba đình"]
    for kw in hanoi_keywords:
        if kw in location or kw in title:
            score += 5
            break

    # 7. No relevant title keyword → cap at 15
    if title_score == 0:
        score = min(score, 15)

    return max(0, min(100, score))
```

- [ ] **Step 2: Write llm.py — Ollama client with retry**

```python
# backend/app/core/llm.py
import asyncio
import json
import logging
import aiohttp
from dataclasses import dataclass
from app.config import settings

logger = logging.getLogger(__name__)

LLM_PROMPT_TEMPLATE = """{system_prompt}

JOB POSTING:
Platform: {platform}
Title: {title}
Company: {company}
Skills: {skills}
Location: {location}
Salary: {salary}
Experience Required: {level}

Description:
{description}

Requirements:
{requirements}

Benefits:
{benefits}

---
Evaluate this job for the candidate. Output ONLY valid JSON (no markdown, no codeblocks):
{{"score": <0-100>, "rationale": "<2-3 sentences in Vietnamese>", "pros": ["<point1>", "<point2>"], "cons": ["<point1>", "<point2>"]}}"""


@dataclass
class EvalResult:
    score: int = -1
    rationale: str = ""
    pros: str = "[]"
    cons: str = "[]"
    error: str = ""


class OllamaClient:
    def __init__(
        self,
        url: str = None,
        model: str = None,
        timeout: int = None,
        max_retries: int = None,
    ):
        self.url = url or settings.ollama_url
        self.model = model or settings.ollama_model
        self.timeout = timeout or settings.llm_timeout
        self.max_retries = max_retries or settings.llm_max_retries
        self.api_url = f"{self.url}/api/generate"

    async def check_health(self) -> bool:
        """Check if Ollama is running."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def evaluate_job(self, job: dict, system_prompt: str) -> EvalResult:
        """Evaluate a job with retry logic and JSON validation."""
        prompt = LLM_PROMPT_TEMPLATE.format(
            system_prompt=system_prompt,
            platform=job.get("platform", ""),
            title=job.get("title", ""),
            company=job.get("company", ""),
            skills=job.get("skills", ""),
            location=job.get("location", ""),
            salary=job.get("salary", "N/A"),
            level=job.get("level", "Không rõ"),
            description=(job.get("description") or "")[:2000],
            requirements=(job.get("requirements") or "")[:1500],
            benefits=(job.get("benefits") or "")[:800],
        )

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0.1, "num_predict": 512},
        }

        for attempt in range(self.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        self.api_url, json=payload, timeout=timeout
                    ) as resp:
                        data = await resp.json()
                        result = json.loads(data["response"])

                        score = int(result.get("score", 0))
                        score = max(0, min(100, score))

                        return EvalResult(
                            score=score,
                            rationale=result.get("rationale", ""),
                            pros=json.dumps(result.get("pros", []), ensure_ascii=False),
                            cons=json.dumps(result.get("cons", []), ensure_ascii=False),
                        )

            except asyncio.TimeoutError:
                logger.warning(f"LLM timeout attempt {attempt + 1}/{self.max_retries}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return EvalResult(score=-1, error="Timeout after retries")

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"LLM parse error attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return EvalResult(score=-1, error=f"Parse error: {str(e)[:200]}")

            except Exception as e:
                logger.error(f"LLM error attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                    continue
                return EvalResult(score=-1, error=str(e)[:200])

        return EvalResult(score=-1, error="All retries exhausted")
```

- [ ] **Step 3: Write core __init__.py**

```python
# backend/app/core/__init__.py
from app.core.scoring import keyword_score_job, get_tier, load_profile, TIER_THRESHOLDS
from app.core.llm import OllamaClient, EvalResult
```

- [ ] **Step 4: Verify core modules**

```bash
cd backend
python -c "
from app.core import keyword_score_job, get_tier, TIER_THRESHOLDS, OllamaClient
print('Tier thresholds:', TIER_THRESHOLDS)
print('Score 80 =>', get_tier(80))
print('Score 55 =>', get_tier(55))
print('Score 40 =>', get_tier(40))
print('Score 10 =>', get_tier(10))
"
```

Expected:
```
Tier thresholds: {'S': 75, 'A': 50, 'B': 35, 'C': 1}
Score 80 => S
Score 55 => A
Score 40 => B
Score 10 => C
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/
git commit -m "feat: add scoring engine and Ollama LLM client with retry"
```

---

### Task 5: WebSocket manager

**Files:**
- Create: `backend/app/api/websocket.py`

- [ ] **Step 1: Write WebSocket manager**

```python
# backend/app/api/websocket.py
import json
import logging
from typing import List
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections and broadcast messages."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.active_connections.remove(conn)

    async def send_scraper_progress(self, platform: str, page: int, jobs_found: int, status: str):
        await self.broadcast({
            "type": "scraper_progress",
            "platform": platform,
            "page": page,
            "jobs_found": jobs_found,
            "status": status,
        })

    async def send_scraper_log(self, platform: str, level: str, message: str):
        import time
        await self.broadcast({
            "type": "scraper_log",
            "platform": platform,
            "level": level,
            "message": message,
            "timestamp": time.time(),
        })

    async def send_scraper_complete(self, platform: str, total_new: int, total_updated: int):
        await self.broadcast({
            "type": "scraper_complete",
            "platform": platform,
            "total_new": total_new,
            "total_updated": total_updated,
        })

    async def send_eval_progress(self, evaluated: int, total: int, current_job: str):
        await self.broadcast({
            "type": "eval_progress",
            "evaluated": evaluated,
            "total": total,
            "current_job": current_job,
        })

    async def send_notification_sent(self, channel: str, job_count: int):
        await self.broadcast({
            "type": "notification_sent",
            "channel": channel,
            "job_count": job_count,
        })


# Singleton instance
ws_manager = ConnectionManager()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/api/websocket.py
git commit -m "feat: add WebSocket connection manager"
```

---

### Task 6: Service layer

**Files:**
- Create: `backend/app/services/job_service.py`
- Create: `backend/app/services/application_service.py`
- Create: `backend/app/services/evaluator_service.py`
- Create: `backend/app/services/scraper_service.py`
- Create: `backend/app/services/notification_service.py`
- Create: `backend/app/services/scheduler_service.py`
- Modify: `backend/app/services/__init__.py`

- [ ] **Step 1: Write job_service.py**

```python
# backend/app/services/job_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, or_
from typing import Optional
from datetime import datetime, timedelta
from app.models.job import Job
from app.core.scoring import get_tier, TIER_THRESHOLDS


def get_jobs(
    db: Session,
    page: int = 1,
    per_page: int = 50,
    tier: Optional[str] = None,
    platform: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    location: Optional[str] = None,
    has_salary: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "final_score",
    sort_order: str = "desc",
):
    query = db.query(Job)

    # Determine score column
    score_col = Job.final_score if sort_by in ("final_score",) else Job.keyword_score

    # Filter by tier
    if tier:
        thresholds = TIER_THRESHOLDS
        if tier == "S":
            query = query.filter(score_col >= thresholds["S"])
        elif tier == "A":
            query = query.filter(score_col >= thresholds["A"], score_col < thresholds["S"])
        elif tier == "B":
            query = query.filter(score_col >= thresholds["B"], score_col < thresholds["A"])
        elif tier == "C":
            query = query.filter(score_col >= thresholds["C"], score_col < thresholds["B"])

    if platform:
        query = query.filter(Job.platform == platform)
    if min_score is not None:
        query = query.filter(score_col >= min_score)
    if max_score is not None:
        query = query.filter(score_col <= max_score)
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    if has_salary:
        query = query.filter(Job.salary.isnot(None), Job.salary != "", Job.salary != "Thỏa thuận")
    if search:
        query = query.filter(
            or_(
                Job.title.ilike(f"%{search}%"),
                Job.company.ilike(f"%{search}%"),
                Job.description.ilike(f"%{search}%"),
            )
        )

    # Only show scored jobs (score > 0)
    query = query.filter(score_col > 0)

    total = query.count()

    # Sort
    sort_column = getattr(Job, sort_by, Job.final_score)
    if sort_order == "asc":
        query = query.order_by(asc(sort_column))
    else:
        query = query.order_by(desc(sort_column))

    # Paginate
    offset = (page - 1) * per_page
    jobs = query.offset(offset).limit(per_page).all()

    return jobs, total


def get_job_by_id(db: Session, job_id: str):
    return db.query(Job).filter(Job.id == job_id).first()


def get_dashboard_stats(db: Session):
    total = db.query(func.count(Job.id)).scalar()

    # Use final_score if available, else keyword_score
    has_final = db.query(func.count(Job.id)).filter(Job.final_score > -1).scalar()
    score_col = Job.final_score if has_final > 0 else Job.keyword_score

    tier_s = db.query(func.count(Job.id)).filter(score_col >= 75).scalar()
    tier_a = db.query(func.count(Job.id)).filter(score_col >= 50, score_col < 75).scalar()
    tier_b = db.query(func.count(Job.id)).filter(score_col >= 35, score_col < 50).scalar()
    tier_c = db.query(func.count(Job.id)).filter(score_col >= 1, score_col < 35).scalar()

    # By platform
    platform_counts = (
        db.query(Job.platform, func.count(Job.id))
        .group_by(Job.platform)
        .all()
    )
    by_platform = {p: c for p, c in platform_counts}

    evaluated = db.query(func.count(Job.id)).filter(Job.llm_score > -1).scalar()
    kw_scored = db.query(func.count(Job.id)).filter(Job.keyword_score > -1).scalar()
    pending = db.query(func.count(Job.id)).filter(
        Job.keyword_score >= 25, Job.llm_score == -1
    ).scalar()

    avg = db.query(func.avg(score_col)).filter(score_col > 0).scalar() or 0

    # New today
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    new_today = db.query(func.count(Job.id)).filter(Job.scraped_at >= today).scalar()

    return {
        "total_jobs": total,
        "tier_s": tier_s,
        "tier_a": tier_a,
        "tier_b": tier_b,
        "tier_c": tier_c,
        "by_platform": by_platform,
        "evaluated": evaluated,
        "pending_eval": pending,
        "avg_score": round(avg, 1),
        "new_today": new_today,
    }
```

- [ ] **Step 2: Write application_service.py**

```python
# backend/app/services/application_service.py
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime
from app.models.application import Application
from app.models.job import Job
from app.core.scoring import get_tier


def get_applications(db: Session, status: Optional[str] = None) -> List[dict]:
    query = db.query(Application, Job).join(Job, Application.job_id == Job.id)
    if status:
        query = query.filter(Application.status == status)
    query = query.order_by(Application.updated_at.desc())
    results = query.all()

    apps = []
    for app, job in results:
        score = job.final_score if job.final_score > -1 else job.keyword_score
        apps.append({
            "id": app.id,
            "job_id": app.job_id,
            "status": app.status,
            "applied_at": app.applied_at,
            "notes": app.notes,
            "interview_date": app.interview_date,
            "interview_notes": app.interview_notes,
            "salary_offered": app.salary_offered,
            "created_at": app.created_at,
            "updated_at": app.updated_at,
            "job_title": job.title,
            "job_company": job.company,
            "job_platform": job.platform,
            "job_tier": get_tier(score) if score > 0 else "C",
            "job_score": score,
            "job_url": job.url,
        })
    return apps


def create_application(db: Session, job_id: str, status: str = "saved", notes: str = None):
    app = Application(
        job_id=job_id,
        status=status,
        notes=notes,
        applied_at=datetime.now() if status == "applied" else None,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def update_application(db: Session, app_id: int, **kwargs):
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        return None
    for key, value in kwargs.items():
        if value is not None and hasattr(app, key):
            setattr(app, key, value)
    if kwargs.get("status") == "applied" and not app.applied_at:
        app.applied_at = datetime.now()
    app.updated_at = datetime.now()
    db.commit()
    db.refresh(app)
    return app


def delete_application(db: Session, app_id: int):
    app = db.query(Application).filter(Application.id == app_id).first()
    if app:
        db.delete(app)
        db.commit()
        return True
    return False


def get_application_stats(db: Session):
    stats = (
        db.query(Application.status, func.count(Application.id))
        .group_by(Application.status)
        .all()
    )
    return {s: c for s, c in stats}
```

- [ ] **Step 3: Write evaluator_service.py**

```python
# backend/app/services/evaluator_service.py
import asyncio
import logging
from sqlalchemy.orm import Session
from app.models.job import Job
from app.core.scoring import keyword_score_job, load_profile
from app.core.llm import OllamaClient
from app.config import settings
from app.api.websocket import ws_manager

logger = logging.getLogger(__name__)

# Track evaluation state
_eval_state = {"is_running": False, "evaluated": 0, "total": 0}


def get_eval_status(db: Session) -> dict:
    total = db.query(Job).count()
    kw_scored = db.query(Job).filter(Job.keyword_score > -1).count()
    llm_done = db.query(Job).filter(Job.llm_score > -1).count()
    llm_candidates = db.query(Job).filter(Job.keyword_score >= settings.llm_threshold).count()

    return {
        "is_running": _eval_state["is_running"],
        "total_jobs": total,
        "keyword_scored": kw_scored,
        "llm_evaluated": llm_done,
        "llm_candidates": llm_candidates,
        "pending_llm": llm_candidates - llm_done,
    }


def run_keyword_scoring(db: Session) -> int:
    """Score all jobs with keyword matching."""
    profile = load_profile(settings.profile_path)
    jobs = db.query(Job).all()
    scored = 0

    for job in jobs:
        job_dict = {
            "title": job.title, "company": job.company,
            "description": job.description, "requirements": job.requirements,
            "skills": job.skills, "benefits": job.benefits,
            "location": job.location, "level": job.level,
        }
        ks = keyword_score_job(job_dict, profile)
        job.keyword_score = ks
        scored += 1
        if scored % 500 == 0:
            db.commit()

    db.commit()
    return scored


async def run_llm_evaluation(db: Session) -> int:
    """Evaluate top keyword-scored jobs with Ollama LLM."""
    global _eval_state
    _eval_state["is_running"] = True

    profile = load_profile(settings.profile_path)
    system_prompt = profile.get("llm_evaluation_prompt", "")
    client = OllamaClient()

    if not await client.check_health():
        _eval_state["is_running"] = False
        raise RuntimeError("Ollama is not running")

    jobs = (
        db.query(Job)
        .filter(Job.keyword_score >= settings.llm_threshold, Job.llm_score == -1)
        .order_by(Job.keyword_score.desc())
        .all()
    )

    total = len(jobs)
    _eval_state["total"] = total
    _eval_state["evaluated"] = 0
    evaluated = 0

    for job in jobs:
        job_dict = {
            "platform": job.platform, "title": job.title,
            "company": job.company, "skills": job.skills,
            "location": job.location, "salary": job.salary,
            "level": job.level, "description": job.description,
            "requirements": job.requirements, "benefits": job.benefits,
        }

        result = await client.evaluate_job(job_dict, system_prompt)

        if result.score >= 0:
            job.llm_score = result.score
            job.llm_rationale = result.rationale
            job.llm_pros = result.pros
            job.llm_cons = result.cons
            job.final_score = int(job.keyword_score * 0.4 + result.score * 0.6)
            job.relevance_score = job.final_score
            evaluated += 1
        else:
            logger.warning(f"LLM eval failed for {job.id}: {result.error}")

        _eval_state["evaluated"] = evaluated
        db.commit()

        await ws_manager.send_eval_progress(evaluated, total, job.title[:60])

    _eval_state["is_running"] = False
    return evaluated


def reset_scores(db: Session):
    """Reset all evaluation scores."""
    db.query(Job).update({
        Job.keyword_score: -1,
        Job.llm_score: -1,
        Job.final_score: -1,
        Job.llm_rationale: None,
        Job.llm_pros: None,
        Job.llm_cons: None,
        Job.relevance_score: -1,
        Job.evaluation_reason: None,
    })
    db.commit()
```

- [ ] **Step 4: Write scraper_service.py**

```python
# backend/app/services/scraper_service.py
import asyncio
import logging
import sys
import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.scraper_run import ScraperRun
from app.api.websocket import ws_manager
from app.database import SessionLocal

logger = logging.getLogger(__name__)

# Track running state
_scraper_state = {
    "is_running": False,
    "current_platforms": [],
    "tasks": {},
    "cancelled": False,
}

# Add v4 root to path so we can import existing scrapers
V4_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if V4_ROOT not in sys.path:
    sys.path.insert(0, V4_ROOT)


async def run_scrapers(platforms: List[str] = None, triggered_by: str = "manual"):
    """Run scrapers using existing v4 scraper classes."""
    global _scraper_state
    if _scraper_state["is_running"]:
        raise RuntimeError("Scrapers already running")

    _scraper_state["is_running"] = True
    _scraper_state["cancelled"] = False

    # Import v4 scrapers
    from ybox_scraper import YboxScraper
    from vnw_scraper import VietnamWorksScraper
    from topcv_scraper import TopCVScraper
    from itviec_scraper import ITviecScraper
    from careerviet_scraper import CareerVietScraper
    from joboko_scraper import JobokoScraper

    scraper_map = {
        "ybox": ("Ybox", YboxScraper),
        "vnw": ("VietnamWorks", VietnamWorksScraper),
        "topcv": ("TopCV", TopCVScraper),
        "itviec": ("ITviec", ITviecScraper),
        "careerviet": ("CareerViet", CareerVietScraper),
        "joboko": ("Joboko", JobokoScraper),
    }

    if not platforms or "all" in platforms:
        platforms = list(scraper_map.keys())

    _scraper_state["current_platforms"] = platforms

    for platform_key in platforms:
        if _scraper_state["cancelled"]:
            break

        if platform_key not in scraper_map:
            continue

        name, scraper_class = scraper_map[platform_key]
        db = SessionLocal()

        # Record run
        run = ScraperRun(platform=name, triggered_by=triggered_by)
        db.add(run)
        db.commit()

        try:
            await ws_manager.send_scraper_log(name, "info", f"Starting {name} scraper...")
            scraper = scraper_class()
            jobs = await scraper.scrape()
            jobs_count = len(jobs) if jobs else 0

            run.status = "completed"
            run.completed_at = datetime.now()
            run.jobs_found = jobs_count
            db.commit()

            await ws_manager.send_scraper_complete(name, jobs_count, 0)
            await ws_manager.send_scraper_log(name, "info", f"{name} completed: {jobs_count} jobs")

        except Exception as e:
            logger.error(f"Scraper {name} failed: {e}")
            run.status = "failed"
            run.error_message = str(e)[:500]
            run.completed_at = datetime.now()
            db.commit()
            await ws_manager.send_scraper_log(name, "error", f"{name} failed: {str(e)[:200]}")

        finally:
            db.close()

    _scraper_state["is_running"] = False
    _scraper_state["current_platforms"] = []


def stop_scrapers():
    _scraper_state["cancelled"] = True


def get_scraper_status() -> dict:
    return {
        "is_running": _scraper_state["is_running"],
        "current_platforms": _scraper_state["current_platforms"],
        "progress": {},
    }


def get_scraper_history(db: Session, limit: int = 50):
    return (
        db.query(ScraperRun)
        .order_by(ScraperRun.started_at.desc())
        .limit(limit)
        .all()
    )
```

- [ ] **Step 5: Write notification_service.py**

```python
# backend/app/services/notification_service.py
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)


async def send_telegram(message: str) -> bool:
    """Send message via Telegram bot."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.warning("Telegram not configured")
        return False

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    logger.info("Telegram message sent")
                    return True
                else:
                    text = await resp.text()
                    logger.error(f"Telegram error: {text}")
                    return False
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")
        return False


def send_email(subject: str, html_body: str, to_email: str = None) -> bool:
    """Send email via SMTP."""
    if not settings.smtp_email or not settings.smtp_password:
        logger.warning("Email not configured")
        return False

    to_email = to_email or settings.smtp_email

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_email
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_email, settings.smtp_password)
            server.send_message(msg)
            logger.info(f"Email sent to {to_email}")
            return True
    except Exception as e:
        logger.error(f"Email send failed: {e}")
        return False


def format_job_notification(jobs: list) -> str:
    """Format jobs for Telegram notification."""
    lines = ["🔔 *New Job Matches Found!*\n"]
    for i, job in enumerate(jobs[:10], 1):
        score = job.get("final_score") or job.get("keyword_score", 0)
        tier = "🟢" if score >= 75 else "🔵" if score >= 50 else "🟡"
        lines.append(
            f"{tier} *{job['title']}*\n"
            f"   {job.get('company', 'N/A')} | Score: {score}\n"
            f"   [View]({job.get('url', '')})\n"
        )
    return "\n".join(lines)
```

- [ ] **Step 6: Write scheduler_service.py**

```python
# backend/app/services/scheduler_service.py
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.models.scheduler import SchedulerConfig
from app.config import settings
from app.database import SessionLocal

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


def init_scheduler():
    """Initialize scheduler with saved configs."""
    scheduler.start()
    logger.info("APScheduler started")

    # Load saved configs from DB
    db = SessionLocal()
    try:
        configs = db.query(SchedulerConfig).filter(SchedulerConfig.enabled == 1).all()
        for config in configs:
            add_scheduled_job(config.task_name, config.cron_expression)
    finally:
        db.close()


def add_scheduled_job(task_name: str, cron_expression: str):
    """Add or replace a scheduled job."""
    # Parse cron: "minute hour day month weekday"
    parts = cron_expression.split()
    if len(parts) != 5:
        logger.error(f"Invalid cron: {cron_expression}")
        return

    trigger = CronTrigger(
        minute=parts[0], hour=parts[1], day=parts[2],
        month=parts[3], day_of_week=parts[4],
    )

    job_func = _get_job_func(task_name)
    if not job_func:
        logger.error(f"Unknown task: {task_name}")
        return

    # Remove existing if any
    existing = scheduler.get_job(task_name)
    if existing:
        scheduler.remove_job(task_name)

    scheduler.add_job(job_func, trigger, id=task_name, replace_existing=True)
    logger.info(f"Scheduled job: {task_name} with cron: {cron_expression}")


def remove_scheduled_job(task_name: str):
    existing = scheduler.get_job(task_name)
    if existing:
        scheduler.remove_job(task_name)


def _get_job_func(task_name: str):
    async def auto_scrape():
        from app.services.scraper_service import run_scrapers
        logger.info("Auto-scrape triggered by scheduler")
        await run_scrapers(triggered_by="scheduler")

    async def auto_evaluate():
        from app.services.evaluator_service import run_keyword_scoring, run_llm_evaluation
        logger.info("Auto-evaluate triggered by scheduler")
        db = SessionLocal()
        try:
            run_keyword_scoring(db)
            await run_llm_evaluation(db)
        finally:
            db.close()

    async def daily_report():
        from app.services.notification_service import send_telegram, format_job_notification
        from app.services.job_service import get_jobs
        logger.info("Daily report triggered by scheduler")
        db = SessionLocal()
        try:
            jobs, _ = get_jobs(db, page=1, per_page=10, sort_by="final_score")
            if jobs:
                job_dicts = [{"title": j.title, "company": j.company,
                             "final_score": j.final_score, "url": j.url} for j in jobs]
                msg = format_job_notification(job_dicts)
                await send_telegram(msg)
        finally:
            db.close()

    funcs = {
        "auto_scrape": auto_scrape,
        "auto_evaluate": auto_evaluate,
        "daily_report": daily_report,
    }
    return funcs.get(task_name)


def get_scheduler_configs(db: Session):
    return db.query(SchedulerConfig).all()


def update_scheduler_config(db: Session, task_name: str, enabled: bool = None, cron: str = None):
    config = db.query(SchedulerConfig).filter(SchedulerConfig.task_name == task_name).first()
    if not config:
        config = SchedulerConfig(
            task_name=task_name,
            enabled=0,
            cron_expression=cron or "0 6 * * *",
        )
        db.add(config)

    if enabled is not None:
        config.enabled = 1 if enabled else 0
    if cron:
        config.cron_expression = cron

    db.commit()

    if config.enabled:
        add_scheduled_job(task_name, config.cron_expression)
    else:
        remove_scheduled_job(task_name)

    return config


def shutdown_scheduler():
    scheduler.shutdown(wait=False)
```

- [ ] **Step 7: Write services __init__.py**

```python
# backend/app/services/__init__.py
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/
git commit -m "feat: add service layer for jobs, applications, evaluator, scrapers, notifications, scheduler"
```

---

### Task 7: API routes

**Files:**
- Create: `backend/app/api/jobs.py`
- Create: `backend/app/api/scrapers.py`
- Create: `backend/app/api/evaluator.py`
- Create: `backend/app/api/applications.py`
- Create: `backend/app/api/settings.py`
- Modify: `backend/app/api/__init__.py`

- [ ] **Step 1: Write jobs.py routes**

```python
# backend/app/api/jobs.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.schemas.job import JobResponse, JobDetailResponse, JobListResponse
from app.schemas.stats import DashboardStats
from app.services import job_service
from app.core.scoring import get_tier
import math

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=JobListResponse)
def list_jobs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    tier: Optional[str] = None,
    platform: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    location: Optional[str] = None,
    has_salary: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "final_score",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    jobs, total = job_service.get_jobs(
        db, page, per_page, tier, platform, min_score, max_score,
        location, has_salary, search, sort_by, sort_order,
    )
    job_responses = []
    for j in jobs:
        score = j.final_score if j.final_score > -1 else j.keyword_score
        resp = JobResponse.model_validate(j)
        resp.tier = get_tier(score) if score > 0 else None
        job_responses.append(resp)

    return JobListResponse(
        jobs=job_responses,
        total=total,
        page=page,
        per_page=per_page,
        total_pages=math.ceil(total / per_page) if total > 0 else 0,
    )


@router.get("/stats", response_model=DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    from app.services.application_service import get_application_stats
    stats = job_service.get_dashboard_stats(db)
    app_stats = get_application_stats(db)
    stats["applications_count"] = sum(app_stats.values())
    stats["interviews_count"] = app_stats.get("interview", 0)
    return DashboardStats(**stats)


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str, db: Session = Depends(get_db)):
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    score = job.final_score if job.final_score > -1 else job.keyword_score
    resp = JobDetailResponse.model_validate(job)
    resp.tier = get_tier(score) if score > 0 else None
    return resp
```

- [ ] **Step 2: Write scrapers.py routes**

```python
# backend/app/api/scrapers.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.scraper import ScraperStartRequest, ScraperRunResponse, ScraperStatusResponse
from app.services import scraper_service

router = APIRouter(prefix="/api/scrapers", tags=["scrapers"])


@router.post("/run")
async def start_scraping(req: ScraperStartRequest, background_tasks: BackgroundTasks):
    if scraper_service.get_scraper_status()["is_running"]:
        return {"error": "Scrapers already running"}
    background_tasks.add_task(scraper_service.run_scrapers, req.platforms)
    return {"status": "started", "platforms": req.platforms}


@router.get("/status", response_model=ScraperStatusResponse)
def get_status():
    return scraper_service.get_scraper_status()


@router.get("/history", response_model=List[ScraperRunResponse])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    return scraper_service.get_scraper_history(db, limit)


@router.post("/stop")
def stop_scraping():
    scraper_service.stop_scrapers()
    return {"status": "stopping"}
```

- [ ] **Step 3: Write evaluator.py routes**

```python
# backend/app/api/evaluator.py
from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.evaluator import EvalStatusResponse
from app.services import evaluator_service

router = APIRouter(prefix="/api/evaluator", tags=["evaluator"])


@router.post("/keyword")
def run_keyword(db: Session = Depends(get_db)):
    # Keyword scoring is fast (~2s for 7500 jobs) so runs synchronously
    scored = evaluator_service.run_keyword_scoring(db)
    return {"status": "completed", "scored": scored}


@router.post("/llm")
async def run_llm(background_tasks: BackgroundTasks):
    # LLM evaluation is slow; use background task with its own DB session
    async def _run():
        from app.database import SessionLocal
        db = SessionLocal()
        try:
            await evaluator_service.run_llm_evaluation(db)
        finally:
            db.close()
    background_tasks.add_task(_run)
    return {"status": "started"}


@router.get("/status", response_model=EvalStatusResponse)
def get_status(db: Session = Depends(get_db)):
    return evaluator_service.get_eval_status(db)


@router.post("/reset")
def reset(db: Session = Depends(get_db)):
    evaluator_service.reset_scores(db)
    return {"status": "reset_complete"}
```

- [ ] **Step 4: Write applications.py routes**

```python
# backend/app/api/applications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from app.database import get_db
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.services import application_service

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=List[ApplicationResponse])
def list_applications(status: Optional[str] = None, db: Session = Depends(get_db)):
    return application_service.get_applications(db, status)


@router.post("", response_model=ApplicationResponse)
def create_application(data: ApplicationCreate, db: Session = Depends(get_db)):
    app = application_service.create_application(db, data.job_id, data.status, data.notes)
    # Return with joined job info
    apps = application_service.get_applications(db)
    return next((a for a in apps if a["id"] == app.id), app)


@router.patch("/{app_id}", response_model=ApplicationResponse)
def update_application(app_id: int, data: ApplicationUpdate, db: Session = Depends(get_db)):
    update_data = data.model_dump(exclude_unset=True)
    app = application_service.update_application(db, app_id, **update_data)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    apps = application_service.get_applications(db)
    return next((a for a in apps if a["id"] == app.id), app)


@router.delete("/{app_id}")
def delete_application(app_id: int, db: Session = Depends(get_db)):
    if not application_service.delete_application(db, app_id):
        raise HTTPException(status_code=404, detail="Application not found")
    return {"status": "deleted"}


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    return application_service.get_application_stats(db)
```

- [ ] **Step 5: Write settings.py routes**

```python
# backend/app/api/settings.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.core.scoring import load_profile
from app.schemas.settings import (
    ProfileResponse, ProfileUpdate,
    NotificationSettingsResponse, NotificationSettingsUpdate,
    SchedulerConfigResponse, SchedulerConfigUpdate,
)
from app.models.notification import NotificationSettings
from app.services import scheduler_service, notification_service

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("/profile", response_model=ProfileResponse)
def get_profile():
    try:
        profile = load_profile(settings.profile_path)
        return ProfileResponse(data=profile)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Profile not found")


@router.put("/profile")
def update_profile(data: ProfileUpdate):
    with open(settings.profile_path, "w", encoding="utf-8") as f:
        json.dump(data.data, f, ensure_ascii=False, indent=4)
    return {"status": "updated"}


@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    items = db.query(NotificationSettings).all()
    if not items:
        # Create defaults
        for channel in ["telegram", "email"]:
            ns = NotificationSettings(channel=channel, enabled=0, config="{}")
            db.add(ns)
        db.commit()
        items = db.query(NotificationSettings).all()
    result = []
    for item in items:
        config = json.loads(item.config) if item.config else {}
        result.append({
            "id": item.id,
            "channel": item.channel,
            "enabled": bool(item.enabled),
            "config": config,
            "min_tier": item.min_tier,
            "daily_digest": bool(item.daily_digest),
        })
    return result


@router.put("/notifications/{channel}")
def update_notifications(channel: str, data: NotificationSettingsUpdate, db: Session = Depends(get_db)):
    ns = db.query(NotificationSettings).filter(NotificationSettings.channel == channel).first()
    if not ns:
        raise HTTPException(status_code=404, detail="Channel not found")
    if data.enabled is not None:
        ns.enabled = 1 if data.enabled else 0
    if data.config is not None:
        ns.config = json.dumps(data.config)
    if data.min_tier is not None:
        ns.min_tier = data.min_tier
    if data.daily_digest is not None:
        ns.daily_digest = 1 if data.daily_digest else 0
    db.commit()
    return {"status": "updated"}


@router.post("/test-telegram")
async def test_telegram():
    result = await notification_service.send_telegram("🧪 Test message from Job Finder v5!")
    return {"success": result}


@router.post("/test-email")
def test_email():
    result = notification_service.send_email(
        "Job Finder v5 - Test", "<h1>Test Email</h1><p>This is a test from Job Finder v5.</p>"
    )
    return {"success": result}


@router.get("/scheduler")
def get_scheduler(db: Session = Depends(get_db)):
    configs = scheduler_service.get_scheduler_configs(db)
    if not configs:
        # Create defaults
        defaults = [
            ("auto_scrape", settings.auto_scrape_cron),
            ("auto_evaluate", settings.auto_evaluate_cron),
            ("daily_report", settings.daily_report_cron),
        ]
        for name, cron in defaults:
            scheduler_service.update_scheduler_config(db, name, enabled=False, cron=cron)
        configs = scheduler_service.get_scheduler_configs(db)
    return [SchedulerConfigResponse.model_validate(c) for c in configs]


@router.put("/scheduler/{task_name}")
def update_scheduler(task_name: str, data: SchedulerConfigUpdate, db: Session = Depends(get_db)):
    config = scheduler_service.update_scheduler_config(
        db, task_name, enabled=data.enabled, cron=data.cron_expression,
    )
    return SchedulerConfigResponse.model_validate(config)
```

- [ ] **Step 6: Write API __init__.py (aggregate routers)**

```python
# backend/app/api/__init__.py
from fastapi import APIRouter
from app.api.jobs import router as jobs_router
from app.api.scrapers import router as scrapers_router
from app.api.evaluator import router as evaluator_router
from app.api.applications import router as applications_router
from app.api.settings import router as settings_router

api_router = APIRouter()
api_router.include_router(jobs_router)
api_router.include_router(scrapers_router)
api_router.include_router(evaluator_router)
api_router.include_router(applications_router)
api_router.include_router(settings_router)
```

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/
git commit -m "feat: add all API route handlers"
```

---

### Task 8: FastAPI main entry point

**Files:**
- Create: `backend/app/main.py`

- [ ] **Step 1: Write main.py**

```python
# backend/app/main.py
import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.models import *  # noqa: ensure all models registered
from app.api import api_router
from app.api.websocket import ws_manager
from app.services.scheduler_service import init_scheduler, shutdown_scheduler

# Encoding fix for Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Job Finder v5 Pro...")
    Base.metadata.create_all(bind=engine)
    init_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()
    logger.info("Job Finder v5 Pro stopped.")


app = FastAPI(title="Job Finder v5 Pro", version="5.0.0", lifespan=lifespan)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router)


# WebSocket endpoint
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

- [ ] **Step 2: Verify backend starts**

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

Expected: Server starts, creates new tables, scheduler initializes. Visit http://localhost:8000/docs to see Swagger UI.

- [ ] **Step 3: Test key endpoints**

```bash
# In another terminal:
curl http://localhost:8000/api/jobs/stats
curl http://localhost:8000/api/jobs?page=1&per_page=5
curl http://localhost:8000/api/scrapers/status
curl http://localhost:8000/api/evaluator/status
```

Expected: JSON responses with actual data from jobs.db.

- [ ] **Step 4: Commit**

```bash
git add backend/app/main.py
git commit -m "feat: add FastAPI main entry point with lifespan, CORS, and WebSocket"
```

---

## Chunk 2: Frontend

### Task 9: Frontend scaffold

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/index.css`

- [ ] **Step 1: Initialize frontend project**

```bash
cd C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router-dom @tanstack/react-query zustand axios recharts lucide-react @hello-pangea/dnd
npm install -D tailwindcss @tailwindcss/vite
```

- [ ] **Step 2: Write tailwind.config.js**

```javascript
// frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        dark: {
          900: "#0f172a",
          800: "#1e293b",
          700: "#334155",
          600: "#475569",
        },
        tier: {
          s: "#10b981",
          a: "#3b82f6",
          b: "#f59e0b",
          c: "#ef4444",
        },
      },
    },
  },
  plugins: [],
};
```

- [ ] **Step 3: Write vite.config.ts with API proxy**

```typescript
// frontend/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        ws: true,
      },
    },
  },
});
```

- [ ] **Step 4: Write index.css with dark theme**

```css
/* frontend/src/index.css */
@import "tailwindcss";

body {
  @apply bg-dark-900 text-slate-50 font-sans;
  margin: 0;
}

::-webkit-scrollbar {
  width: 6px;
}
::-webkit-scrollbar-track {
  background: #1e293b;
}
::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 3px;
}
```

- [ ] **Step 5: Write types/index.ts**

```typescript
// frontend/src/types/index.ts
export interface Job {
  id: string;
  platform: string;
  title: string;
  company: string | null;
  url: string | null;
  salary: string | null;
  location: string | null;
  level: string | null;
  skills: string | null;
  deadline: string | null;
  keyword_score: number;
  llm_score: number;
  final_score: number;
  tier: string | null;
  llm_rationale: string | null;
  llm_pros: string | null;
  llm_cons: string | null;
  scraped_at: string | null;
  // Detail fields
  summary?: string | null;
  description?: string | null;
  requirements?: string | null;
  benefits?: string | null;
  domain?: string | null;
  views?: number;
  published_at?: string | null;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface DashboardStats {
  total_jobs: number;
  tier_s: number;
  tier_a: number;
  tier_b: number;
  tier_c: number;
  by_platform: Record<string, number>;
  evaluated: number;
  pending_eval: number;
  avg_score: number;
  new_today: number;
  applications_count: number;
  interviews_count: number;
}

export interface Application {
  id: number;
  job_id: string;
  status: string;
  applied_at: string | null;
  notes: string | null;
  interview_date: string | null;
  interview_notes: string | null;
  salary_offered: string | null;
  created_at: string | null;
  updated_at: string | null;
  job_title: string | null;
  job_company: string | null;
  job_platform: string | null;
  job_tier: string | null;
  job_score: number | null;
  job_url: string | null;
}

export interface ScraperRun {
  id: number;
  platform: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  error_message: string | null;
  triggered_by: string;
}

export type TierType = "S" | "A" | "B" | "C";
```

- [ ] **Step 6: Write api/client.ts**

```typescript
// frontend/src/api/client.ts
import axios from "axios";
import type {
  Job,
  JobListResponse,
  DashboardStats,
  Application,
  ScraperRun,
} from "../types";

const api = axios.create({ baseURL: "/api" });

// Jobs
export const getJobs = (params: Record<string, any>) =>
  api.get<JobListResponse>("/jobs", { params }).then((r) => r.data);

export const getJob = (id: string) =>
  api.get<Job>(`/jobs/${id}`).then((r) => r.data);

export const getStats = () =>
  api.get<DashboardStats>("/jobs/stats").then((r) => r.data);

// Scrapers
export const startScraping = (platforms: string[] = ["all"]) =>
  api.post("/scrapers/run", { platforms }).then((r) => r.data);

export const getScraperStatus = () =>
  api.get("/scrapers/status").then((r) => r.data);

export const getScraperHistory = () =>
  api.get<ScraperRun[]>("/scrapers/history").then((r) => r.data);

export const stopScraping = () =>
  api.post("/scrapers/stop").then((r) => r.data);

// Evaluator
export const runKeywordScoring = () =>
  api.post("/evaluator/keyword").then((r) => r.data);

export const runLlmEvaluation = () =>
  api.post("/evaluator/llm").then((r) => r.data);

export const getEvalStatus = () =>
  api.get("/evaluator/status").then((r) => r.data);

export const resetScores = () =>
  api.post("/evaluator/reset").then((r) => r.data);

// Applications
export const getApplications = (status?: string) =>
  api.get<Application[]>("/applications", { params: status ? { status } : {} }).then((r) => r.data);

export const createApplication = (data: { job_id: string; status?: string; notes?: string }) =>
  api.post<Application>("/applications", data).then((r) => r.data);

export const updateApplication = (id: number, data: Record<string, any>) =>
  api.patch<Application>(`/applications/${id}`, data).then((r) => r.data);

export const deleteApplication = (id: number) =>
  api.delete(`/applications/${id}`).then((r) => r.data);

// Settings
export const getProfile = () =>
  api.get("/settings/profile").then((r) => r.data);

export const updateProfile = (data: any) =>
  api.put("/settings/profile", { data }).then((r) => r.data);

export const getNotifications = () =>
  api.get("/settings/notifications").then((r) => r.data);

export const updateNotification = (channel: string, data: any) =>
  api.put(`/settings/notifications/${channel}`, data).then((r) => r.data);

export const testTelegram = () =>
  api.post("/settings/test-telegram").then((r) => r.data);

export const testEmail = () =>
  api.post("/settings/test-email").then((r) => r.data);

export const getScheduler = () =>
  api.get("/settings/scheduler").then((r) => r.data);

export const updateScheduler = (taskName: string, data: any) =>
  api.put(`/settings/scheduler/${taskName}`, data).then((r) => r.data);
```

- [ ] **Step 7: Write api/websocket.ts**

```typescript
// frontend/src/api/websocket.ts
type MessageHandler = (data: any) => void;

class WebSocketClient {
  private ws: WebSocket | null = null;
  private handlers: Map<string, MessageHandler[]> = new Map();
  private reconnectTimeout: number = 3000;

  connect() {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const url = `${protocol}//${window.location.host}/api/ws`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => console.log("WebSocket connected");

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        const handlers = this.handlers.get(data.type) || [];
        handlers.forEach((h) => h(data));
        // Also notify "all" handlers
        const allHandlers = this.handlers.get("*") || [];
        allHandlers.forEach((h) => h(data));
      } catch (e) {
        console.error("WS parse error:", e);
      }
    };

    this.ws.onclose = () => {
      console.log("WebSocket disconnected, reconnecting...");
      setTimeout(() => this.connect(), this.reconnectTimeout);
    };

    this.ws.onerror = (e) => console.error("WebSocket error:", e);
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, []);
    }
    this.handlers.get(type)!.push(handler);
    return () => {
      const handlers = this.handlers.get(type);
      if (handlers) {
        const idx = handlers.indexOf(handler);
        if (idx > -1) handlers.splice(idx, 1);
      }
    };
  }

  disconnect() {
    this.ws?.close();
  }
}

export const wsClient = new WebSocketClient();
```

- [ ] **Step 8: Write stores/appStore.ts**

```typescript
// frontend/src/stores/appStore.ts
import { create } from "zustand";

interface AppState {
  sidebarCollapsed: boolean;
  selectedJobId: string | null;
  toggleSidebar: () => void;
  setSelectedJob: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  selectedJobId: null,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSelectedJob: (id) => set({ selectedJobId: id }),
}));
```

- [ ] **Step 9: Write shared UI components**

```tsx
// frontend/src/components/ui/TierBadge.tsx
import type { TierType } from "../../types";

const tierColors: Record<TierType, string> = {
  S: "bg-tier-s text-white",
  A: "bg-tier-a text-white",
  B: "bg-tier-b text-white",
  C: "bg-tier-c text-white",
};

export function TierBadge({ tier }: { tier: TierType | string | null }) {
  if (!tier) return null;
  const t = tier as TierType;
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-bold ${tierColors[t] || "bg-dark-700 text-slate-400"}`}>
      {tier}
    </span>
  );
}
```

```tsx
// frontend/src/components/ui/StatsCard.tsx
import { type ReactNode } from "react";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  change?: string;
  color?: string;
}

export function StatsCard({ label, value, icon, change, color = "text-slate-50" }: StatsCardProps) {
  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
      <div className="flex justify-between items-center mb-2">
        <span className="text-slate-400 text-xs">{label}</span>
        {change && <span className="text-tier-s text-xs">{change}</span>}
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
```

```tsx
// frontend/src/components/ui/LoadingSpinner.tsx
export function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="w-8 h-8 border-2 border-tier-s border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
```

- [ ] **Step 10: Write Layout components**

```tsx
// frontend/src/components/layout/Sidebar.tsx
import { NavLink } from "react-router-dom";
import { LayoutDashboard, Briefcase, ClipboardList, Bug, Settings } from "lucide-react";

const navItems = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/jobs", icon: Briefcase, label: "Jobs" },
  { to: "/applications", icon: ClipboardList, label: "Applications" },
  { to: "/scrapers", icon: Bug, label: "Scrapers" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  return (
    <aside className="w-56 bg-dark-900 border-r border-dark-700 flex flex-col h-screen fixed left-0 top-0">
      {/* Logo */}
      <div className="px-5 py-5 flex items-center gap-3">
        <div className="w-9 h-9 bg-gradient-to-br from-tier-s to-tier-a rounded-lg flex items-center justify-center text-white font-bold text-sm">
          JF
        </div>
        <div>
          <div className="text-slate-50 font-bold text-sm">Job Finder</div>
          <div className="text-slate-500 text-[10px]">v5 Pro</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="px-3 flex-1">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg mb-1 text-sm transition-colors ${
                isActive
                  ? "bg-dark-800 text-slate-50 font-medium"
                  : "text-slate-400 hover:text-slate-50 hover:bg-dark-800/50"
              }`
            }
          >
            <item.icon size={18} />
            {item.label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
```

```tsx
// frontend/src/components/layout/Layout.tsx
import { Outlet } from "react-router-dom";
import { Sidebar } from "./Sidebar";

export function Layout() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 ml-56 p-6 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
```

- [ ] **Step 11: Write App.tsx and main.tsx**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Layout } from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Jobs from "./pages/Jobs";
import Applications from "./pages/Applications";
import Scrapers from "./pages/Scrapers";
import SettingsPage from "./pages/Settings";

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs" element={<Jobs />} />
            <Route path="/applications" element={<Applications />} />
            <Route path="/scrapers" element={<Scrapers />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

```tsx
// frontend/src/main.tsx
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { wsClient } from "./api/websocket";

// Connect WebSocket
wsClient.connect();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 12: Commit**

```bash
git add frontend/
git commit -m "feat: scaffold React frontend with routing, API client, WebSocket, and layout"
```

---

### Task 10: Dashboard page

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`

- [ ] **Step 1: Write Dashboard page**

```tsx
// frontend/src/pages/Dashboard.tsx
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { getStats, getJobs } from "../api/client";
import { StatsCard } from "../components/ui/StatsCard";
import { TierBadge } from "../components/ui/TierBadge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
  });
  const { data: topJobs } = useQuery({
    queryKey: ["topJobs"],
    queryFn: () => getJobs({ page: 1, per_page: 5, sort_by: "final_score", sort_order: "desc" }),
  });

  if (statsLoading) return <LoadingSpinner />;
  if (!stats) return <div className="text-slate-400">Failed to load stats</div>;

  const tierData = [
    { name: "Tier S", count: stats.tier_s, fill: "#10b981" },
    { name: "Tier A", count: stats.tier_a, fill: "#3b82f6" },
    { name: "Tier B", count: stats.tier_b, fill: "#f59e0b" },
    { name: "Tier C", count: stats.tier_c, fill: "#ef4444" },
  ];

  const platformData = Object.entries(stats.by_platform).map(([name, count]) => ({
    name,
    count,
    pct: Math.round(((count as number) / stats.total_jobs) * 100),
  }));

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-slate-400 text-sm">
            {stats.new_today > 0 ? (
              <>Có <span className="text-tier-s">{stats.new_today} jobs mới</span> hôm nay.</>
            ) : "Không có jobs mới hôm nay."}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatsCard label="Total Jobs" value={stats.total_jobs.toLocaleString()} />
        <StatsCard label="Tier S Matches" value={stats.tier_s} color="text-tier-s" />
        <StatsCard label="Applied" value={stats.applications_count} color="text-tier-a" />
        <StatsCard label="AI Evaluated" value={stats.evaluated} color="text-violet-400" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Tier Distribution */}
        <div className="col-span-2 bg-dark-800 rounded-xl p-5 border border-dark-700">
          <h3 className="text-sm font-semibold mb-4">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tierData}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#f8fafc" }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {tierData.map((entry, i) => (
                  <Bar key={i} dataKey="count" fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Breakdown */}
        <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
          <h3 className="text-sm font-semibold mb-4">By Platform</h3>
          <div className="space-y-3">
            {platformData.map((p) => (
              <div key={p.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">{p.name}</span>
                  <span>{p.count}</span>
                </div>
                <div className="bg-dark-700 rounded h-1.5">
                  <div
                    className="bg-tier-s rounded h-full transition-all"
                    style={{ width: `${p.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Matches */}
      <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
        <h3 className="text-sm font-semibold mb-4">Top Matches</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left p-2 text-slate-400 font-medium">Tier</th>
              <th className="text-left p-2 text-slate-400 font-medium">Title</th>
              <th className="text-left p-2 text-slate-400 font-medium">Company</th>
              <th className="text-left p-2 text-slate-400 font-medium">Score</th>
              <th className="text-left p-2 text-slate-400 font-medium">Salary</th>
            </tr>
          </thead>
          <tbody>
            {topJobs?.jobs.map((job) => (
              <tr key={job.id} className="border-b border-dark-900 hover:bg-dark-700/50">
                <td className="p-2"><TierBadge tier={job.tier} /></td>
                <td className="p-2">{job.title}</td>
                <td className="p-2 text-slate-400">{job.company}</td>
                <td className="p-2 font-semibold text-tier-s">{job.final_score > -1 ? job.final_score : job.keyword_score}</td>
                <td className="p-2 text-slate-400">{job.salary || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify renders**

```bash
cd frontend && npm run dev
```

Open http://localhost:5173 — Dashboard should render with data from backend.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Dashboard.tsx
git commit -m "feat: add Dashboard page with stats, charts, and top matches"
```

---

### Task 11: Jobs page

**Files:**
- Create: `frontend/src/pages/Jobs.tsx`

- [ ] **Step 1: Write Jobs page**

```tsx
// frontend/src/pages/Jobs.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getJobs, getJob, createApplication } from "../api/client";
import { TierBadge } from "../components/ui/TierBadge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { X, ExternalLink, Bookmark, ChevronLeft, ChevronRight } from "lucide-react";
import type { Job } from "../types";

export default function Jobs() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", page, filters],
    queryFn: () => getJobs({ page, per_page: 50, sort_by: "final_score", sort_order: "desc", ...filters }),
  });

  const { data: detail } = useQuery({
    queryKey: ["job", selectedId],
    queryFn: () => getJob(selectedId!),
    enabled: !!selectedId,
  });

  const saveMutation = useMutation({
    mutationFn: (jobId: string) => createApplication({ job_id: jobId, status: "saved" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="flex gap-0">
      <div className={`flex-1 ${selectedId ? "mr-96" : ""}`}>
        <h1 className="text-2xl font-bold mb-4">Jobs</h1>

        {/* Filters */}
        <div className="flex gap-3 mb-4 flex-wrap">
          <select
            className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm"
            onChange={(e) => setFilters((f) => ({ ...f, tier: e.target.value || undefined }))}
          >
            <option value="">All Tiers</option>
            <option value="S">Tier S</option>
            <option value="A">Tier A</option>
            <option value="B">Tier B</option>
            <option value="C">Tier C</option>
          </select>
          <select
            className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm"
            onChange={(e) => setFilters((f) => ({ ...f, platform: e.target.value || undefined }))}
          >
            <option value="">All Platforms</option>
            {["VietnamWorks", "CareerViet", "ITviec", "Ybox", "TopCV", "Joboko"].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Search title, company..."
            className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm flex-1 min-w-[200px]"
            onChange={(e) => {
              const v = e.target.value;
              setTimeout(() => setFilters((f) => ({ ...f, search: v || undefined })), 300);
            }}
          />
        </div>

        {/* Table */}
        <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                {["Tier", "Score", "Title", "Company", "Salary", "Location", "Platform"].map((h) => (
                  <th key={h} className="text-left p-3 text-slate-400 font-medium text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data?.jobs.map((job) => (
                <tr
                  key={job.id}
                  className={`border-b border-dark-900 cursor-pointer transition-colors ${
                    selectedId === job.id ? "bg-dark-700" : "hover:bg-dark-700/50"
                  }`}
                  onClick={() => setSelectedId(job.id)}
                >
                  <td className="p-3"><TierBadge tier={job.tier} /></td>
                  <td className="p-3 font-semibold">{job.final_score > -1 ? job.final_score : job.keyword_score}</td>
                  <td className="p-3 max-w-xs truncate">{job.title}</td>
                  <td className="p-3 text-slate-400 max-w-[150px] truncate">{job.company}</td>
                  <td className="p-3 text-slate-400 text-xs">{job.salary || "—"}</td>
                  <td className="p-3 text-slate-400 text-xs">{job.location || "—"}</td>
                  <td className="p-3 text-slate-400 text-xs">{job.platform}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <span className="text-slate-400 text-sm">{data.total} jobs total</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm py-1.5">{page} / {data.total_pages}</span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selectedId && detail && (
        <div className="fixed right-0 top-0 h-full w-96 bg-dark-800 border-l border-dark-700 overflow-y-auto p-5 z-50">
          <div className="flex justify-between items-center mb-4">
            <TierBadge tier={detail.tier} />
            <button onClick={() => setSelectedId(null)} className="text-slate-400 hover:text-slate-50">
              <X size={20} />
            </button>
          </div>
          <h2 className="text-lg font-bold mb-1">{detail.title}</h2>
          <p className="text-slate-400 text-sm mb-4">{detail.company} · {detail.platform}</p>

          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="bg-dark-900 rounded-lg p-2 text-center">
              <div className="text-xs text-slate-400">KW</div>
              <div className="font-bold">{detail.keyword_score}</div>
            </div>
            <div className="bg-dark-900 rounded-lg p-2 text-center">
              <div className="text-xs text-slate-400">LLM</div>
              <div className="font-bold">{detail.llm_score > -1 ? detail.llm_score : "—"}</div>
            </div>
            <div className="bg-dark-900 rounded-lg p-2 text-center">
              <div className="text-xs text-slate-400">Final</div>
              <div className="font-bold text-tier-s">{detail.final_score > -1 ? detail.final_score : "—"}</div>
            </div>
          </div>

          {detail.salary && <p className="text-sm mb-2"><span className="text-slate-400">Salary:</span> {detail.salary}</p>}
          {detail.location && <p className="text-sm mb-2"><span className="text-slate-400">Location:</span> {detail.location}</p>}
          {detail.level && <p className="text-sm mb-4"><span className="text-slate-400">Level:</span> {detail.level}</p>}

          {detail.llm_rationale && (
            <div className="bg-dark-900 rounded-lg p-3 mb-4">
              <div className="text-xs text-slate-400 mb-1">AI Analysis</div>
              <p className="text-sm">{detail.llm_rationale}</p>
            </div>
          )}

          {detail.description && (
            <div className="mb-4">
              <h4 className="text-xs text-slate-400 mb-1 uppercase">Description</h4>
              <p className="text-sm text-slate-300 whitespace-pre-line max-h-40 overflow-y-auto">{detail.description}</p>
            </div>
          )}

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => saveMutation.mutate(detail.id)}
              className="flex-1 bg-tier-a hover:bg-blue-600 text-white rounded-lg py-2 text-sm font-medium flex items-center justify-center gap-2"
            >
              <Bookmark size={14} /> Save
            </button>
            {detail.url && (
              <a
                href={detail.url}
                target="_blank"
                rel="noopener"
                className="flex-1 bg-dark-700 hover:bg-dark-600 rounded-lg py-2 text-sm font-medium flex items-center justify-center gap-2"
              >
                <ExternalLink size={14} /> Open
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Verify with filters**

Test filtering by tier S, searching for "analyst", sorting by score desc.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Jobs.tsx
git commit -m "feat: add Jobs page with filters, table, and detail panel"
```

---

### Task 12: Applications page (Kanban)

**Files:**
- Create: `frontend/src/pages/Applications.tsx`

- [ ] **Step 1: Write Applications Kanban page**

```tsx
// frontend/src/pages/Applications.tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { DragDropContext, Droppable, Draggable, type DropResult } from "@hello-pangea/dnd";
import { getApplications, updateApplication, deleteApplication } from "../api/client";
import { TierBadge } from "../components/ui/TierBadge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { Trash2 } from "lucide-react";
import type { Application } from "../types";

const COLUMNS = ["saved", "applied", "interview", "offer", "rejected"] as const;
const COLUMN_LABELS: Record<string, string> = {
  saved: "Saved", applied: "Applied", interview: "Interview", offer: "Offer", rejected: "Rejected",
};
const COLUMN_COLORS: Record<string, string> = {
  saved: "border-slate-500", applied: "border-tier-a", interview: "border-violet-500",
  offer: "border-tier-s", rejected: "border-tier-c",
};

export default function Applications() {
  const queryClient = useQueryClient();
  const { data: apps, isLoading } = useQuery({
    queryKey: ["applications"],
    queryFn: () => getApplications(),
  });

  const updateMut = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) => updateApplication(id, { status }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteApplication(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  const onDragEnd = (result: DropResult) => {
    if (!result.destination) return;
    const newStatus = result.destination.droppableId;
    const appId = parseInt(result.draggableId);
    updateMut.mutate({ id: appId, status: newStatus });
  };

  if (isLoading) return <LoadingSpinner />;

  const grouped: Record<string, Application[]> = {};
  COLUMNS.forEach((c) => (grouped[c] = []));
  apps?.forEach((app) => {
    if (grouped[app.status]) grouped[app.status].push(app);
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Applications</h1>
      {(!apps || apps.length === 0) && (
        <p className="text-slate-400">No applications yet. Save jobs from the Jobs page to get started.</p>
      )}
      <DragDropContext onDragEnd={onDragEnd}>
        <div className="flex gap-4 overflow-x-auto pb-4">
          {COLUMNS.map((status) => (
            <Droppable key={status} droppableId={status}>
              {(provided, snapshot) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className={`w-64 flex-shrink-0 bg-dark-800 rounded-xl border-t-2 ${COLUMN_COLORS[status]} min-h-[400px] p-3`}
                >
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-sm font-semibold">{COLUMN_LABELS[status]}</h3>
                    <span className="text-xs text-slate-400 bg-dark-700 px-2 py-0.5 rounded">
                      {grouped[status].length}
                    </span>
                  </div>
                  {grouped[status].map((app, index) => (
                    <Draggable key={app.id} draggableId={String(app.id)} index={index}>
                      {(provided) => (
                        <div
                          ref={provided.innerRef}
                          {...provided.draggableProps}
                          {...provided.dragHandleProps}
                          className="bg-dark-900 rounded-lg p-3 mb-2 border border-dark-700 hover:border-dark-600"
                        >
                          <div className="flex justify-between items-start mb-1">
                            <TierBadge tier={app.job_tier} />
                            <button
                              onClick={() => deleteMut.mutate(app.id)}
                              className="text-slate-500 hover:text-tier-c"
                            >
                              <Trash2 size={12} />
                            </button>
                          </div>
                          <p className="text-sm font-medium truncate">{app.job_title}</p>
                          <p className="text-xs text-slate-400 truncate">{app.job_company}</p>
                          {app.job_score && (
                            <p className="text-xs text-slate-500 mt-1">Score: {app.job_score}</p>
                          )}
                          {app.notes && (
                            <p className="text-xs text-slate-500 mt-1 truncate">📝 {app.notes}</p>
                          )}
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          ))}
        </div>
      </DragDropContext>
    </div>
  );
}
```

- [ ] **Step 2: Verify drag and drop**

Create a test application via API, verify it appears in Kanban and can be dragged.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Applications.tsx
git commit -m "feat: add Applications Kanban board with drag-and-drop"
```

---

### Task 13: Scrapers page

**Files:**
- Create: `frontend/src/pages/Scrapers.tsx`

- [ ] **Step 1: Write Scrapers page**

```tsx
// frontend/src/pages/Scrapers.tsx
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { startScraping, stopScraping, getScraperStatus, getScraperHistory } from "../api/client";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { wsClient } from "../api/websocket";
import { Play, Square, RefreshCw } from "lucide-react";

const PLATFORMS = ["Ybox", "VietnamWorks", "TopCV", "ITviec", "CareerViet", "Joboko"];

export default function Scrapers() {
  const queryClient = useQueryClient();
  const [logs, setLogs] = useState<{ platform: string; level: string; message: string; timestamp: number }[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const { data: status } = useQuery({ queryKey: ["scraperStatus"], queryFn: getScraperStatus, refetchInterval: 3000 });
  const { data: history, isLoading } = useQuery({ queryKey: ["scraperHistory"], queryFn: getScraperHistory });

  const startMut = useMutation({
    mutationFn: (platforms: string[]) => startScraping(platforms),
    onSuccess: () => { setIsRunning(true); queryClient.invalidateQueries({ queryKey: ["scraperStatus"] }); },
  });

  const stopMut = useMutation({
    mutationFn: stopScraping,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scraperStatus"] }),
  });

  useEffect(() => {
    const unsub1 = wsClient.on("scraper_log", (data) => {
      setLogs((prev) => [...prev.slice(-100), data]);
    });
    const unsub2 = wsClient.on("scraper_complete", () => {
      queryClient.invalidateQueries({ queryKey: ["scraperHistory"] });
      queryClient.invalidateQueries({ queryKey: ["scraperStatus"] });
    });
    return () => { unsub1(); unsub2(); };
  }, [queryClient]);

  useEffect(() => {
    if (status) setIsRunning(status.is_running);
  }, [status]);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Scrapers</h1>
        <div className="flex gap-2">
          {isRunning ? (
            <button onClick={() => stopMut.mutate()} className="bg-tier-c hover:bg-red-600 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2">
              <Square size={14} /> Stop
            </button>
          ) : (
            <button onClick={() => startMut.mutate(["all"])} className="bg-tier-s hover:bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2">
              <Play size={14} /> Run All
            </button>
          )}
        </div>
      </div>

      {/* Platform Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {PLATFORMS.map((p) => {
          const lastRun = history?.find((h) => h.platform === p);
          const running = status?.current_platforms?.includes(p.toLowerCase());
          return (
            <div key={p} className="bg-dark-800 rounded-xl p-4 border border-dark-700">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-sm">{p}</span>
                <div className={`w-2.5 h-2.5 rounded-full ${running ? "bg-tier-s animate-pulse" : lastRun?.status === "completed" ? "bg-tier-s" : "bg-slate-500"}`} />
              </div>
              <p className="text-xs text-slate-400">
                {lastRun ? `Last: ${new Date(lastRun.started_at!).toLocaleDateString()} — ${lastRun.jobs_found} jobs` : "Never run"}
              </p>
              {!isRunning && (
                <button
                  onClick={() => startMut.mutate([p.toLowerCase()])}
                  className="mt-2 text-xs text-tier-a hover:text-blue-400 flex items-center gap-1"
                >
                  <RefreshCw size={10} /> Run
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Live Logs */}
      {logs.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-700 mb-6">
          <h3 className="text-sm font-semibold mb-2">Live Logs</h3>
          <div className="bg-dark-900 rounded-lg p-3 max-h-48 overflow-y-auto font-mono text-xs space-y-1">
            {logs.map((log, i) => (
              <div key={i} className={log.level === "error" ? "text-tier-c" : "text-slate-300"}>
                [{log.platform}] {log.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Table */}
      <div className="bg-dark-800 rounded-xl p-4 border border-dark-700">
        <h3 className="text-sm font-semibold mb-3">Run History</h3>
        {(!history || history.length === 0) ? (
          <p className="text-slate-400 text-sm">No scraper runs yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                {["Platform", "Status", "Jobs Found", "Started", "Duration", "Triggered By"].map((h) => (
                  <th key={h} className="text-left p-2 text-slate-400 font-medium text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.map((run) => (
                <tr key={run.id} className="border-b border-dark-900">
                  <td className="p-2">{run.platform}</td>
                  <td className="p-2">
                    <span className={`text-xs ${run.status === "completed" ? "text-tier-s" : run.status === "failed" ? "text-tier-c" : "text-tier-b"}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="p-2">{run.jobs_found}</td>
                  <td className="p-2 text-slate-400 text-xs">{run.started_at ? new Date(run.started_at).toLocaleString() : "—"}</td>
                  <td className="p-2 text-slate-400 text-xs">
                    {run.started_at && run.completed_at
                      ? `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                      : "—"}
                  </td>
                  <td className="p-2 text-slate-400 text-xs">{run.triggered_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify scrapers page**

Open http://localhost:5173/scrapers — platform cards and history table should load.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Scrapers.tsx
git commit -m "feat: add Scrapers control page with real-time WebSocket updates"
```

---

### Task 14: Settings page

**Files:**
- Create: `frontend/src/pages/Settings.tsx`

- [ ] **Step 1: Write Settings page**

```tsx
// frontend/src/pages/Settings.tsx
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProfile, getNotifications, updateNotification, testTelegram, testEmail, getScheduler, updateScheduler } from "../api/client";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { Save, Send, Check, X } from "lucide-react";

const TABS = ["Profile", "Notifications", "Scheduler"] as const;

export default function SettingsPage() {
  const [tab, setTab] = useState<typeof TABS[number]>("Profile");
  const queryClient = useQueryClient();

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      <div className="flex gap-1 mb-6 bg-dark-800 rounded-lg p-1 w-fit">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t ? "bg-dark-700 text-slate-50" : "text-slate-400 hover:text-slate-50"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Profile" && <ProfileTab />}
      {tab === "Notifications" && <NotificationsTab />}
      {tab === "Scheduler" && <SchedulerTab />}
    </div>
  );
}

function ProfileTab() {
  const { data, isLoading } = useQuery({ queryKey: ["profile"], queryFn: getProfile });
  if (isLoading) return <LoadingSpinner />;
  if (!data) return <p className="text-slate-400">Failed to load profile</p>;

  const profile = data.data;
  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700 max-w-2xl">
      <h3 className="font-semibold mb-4">User Profile</h3>
      <div className="space-y-3 text-sm">
        <div><span className="text-slate-400">Name:</span> {profile.profile_name}</div>
        <div><span className="text-slate-400">Background:</span> {profile.background}</div>
        <div><span className="text-slate-400">Location:</span> {profile.location}</div>
        <div><span className="text-slate-400">Experience:</span> {profile.experience_years} years</div>
        <div className="mt-4">
          <span className="text-slate-400">Tier S Keywords:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {profile.title_keywords?.tier_s?.keywords?.map((kw: string) => (
              <span key={kw} className="bg-dark-700 px-2 py-0.5 rounded text-xs">{kw}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function NotificationsTab() {
  const queryClient = useQueryClient();
  const { data: notifs, isLoading } = useQuery({ queryKey: ["notifications"], queryFn: getNotifications });
  const [testResult, setTestResult] = useState<string | null>(null);

  const updateMut = useMutation({
    mutationFn: ({ channel, data }: { channel: string; data: any }) => updateNotification(channel, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const testTgMut = useMutation({
    mutationFn: testTelegram,
    onSuccess: (d) => setTestResult(d.success ? "Telegram sent!" : "Failed"),
  });

  const testEmailMut = useMutation({
    mutationFn: testEmail,
    onSuccess: (d) => setTestResult(d.success ? "Email sent!" : "Failed"),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-4 max-w-2xl">
      {notifs?.map((n: any) => (
        <div key={n.channel} className="bg-dark-800 rounded-xl p-5 border border-dark-700">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold capitalize">{n.channel}</h3>
            <button
              onClick={() => updateMut.mutate({ channel: n.channel, data: { enabled: !n.enabled } })}
              className={`w-10 h-5 rounded-full transition-colors ${n.enabled ? "bg-tier-s" : "bg-dark-700"} relative`}
            >
              <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${n.enabled ? "left-5" : "left-0.5"}`} />
            </button>
          </div>
          <div className="text-sm text-slate-400 mb-3">
            Min Tier: {n.min_tier} | Daily Digest: {n.daily_digest ? "On" : "Off"}
          </div>
          <button
            onClick={() => n.channel === "telegram" ? testTgMut.mutate() : testEmailMut.mutate()}
            className="text-xs text-tier-a hover:text-blue-400 flex items-center gap-1"
          >
            <Send size={12} /> Test {n.channel}
          </button>
        </div>
      ))}
      {testResult && <p className="text-sm text-tier-s">{testResult}</p>}
    </div>
  );
}

function SchedulerTab() {
  const queryClient = useQueryClient();
  const { data: configs, isLoading } = useQuery({ queryKey: ["scheduler"], queryFn: getScheduler });

  const updateMut = useMutation({
    mutationFn: ({ name, data }: { name: string; data: any }) => updateScheduler(name, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduler"] }),
  });

  if (isLoading) return <LoadingSpinner />;

  const labels: Record<string, string> = {
    auto_scrape: "Auto Scrape", auto_evaluate: "Auto Evaluate", daily_report: "Daily Report",
  };

  return (
    <div className="space-y-4 max-w-2xl">
      {configs?.map((c: any) => (
        <div key={c.task_name} className="bg-dark-800 rounded-xl p-5 border border-dark-700">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold">{labels[c.task_name] || c.task_name}</h3>
            <button
              onClick={() => updateMut.mutate({ name: c.task_name, data: { enabled: !c.enabled } })}
              className={`w-10 h-5 rounded-full transition-colors ${c.enabled ? "bg-tier-s" : "bg-dark-700"} relative`}
            >
              <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${c.enabled ? "left-5" : "left-0.5"}`} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Cron:</span>
            <input
              defaultValue={c.cron_expression}
              className="bg-dark-900 border border-dark-700 rounded px-2 py-1 text-xs font-mono w-32"
              onBlur={(e) => updateMut.mutate({ name: c.task_name, data: { cron_expression: e.target.value } })}
            />
            {c.last_run && <span className="text-xs text-slate-500">Last: {new Date(c.last_run).toLocaleString()}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Verify settings page**

Open http://localhost:5173/settings — all 3 tabs should load.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/Settings.tsx
git commit -m "feat: add Settings page with profile, notifications, and scheduler tabs"
```

---

## Chunk 3: Final Integration & Polish

### Task 15: End-to-end integration verification

- [ ] **Step 1: Start backend**

```bash
cd backend && python -m uvicorn app.main:app --reload --port 8000
```

- [ ] **Step 2: Start frontend**

```bash
cd frontend && npm run dev
```

- [ ] **Step 3: Verify all pages work**

1. Dashboard: stats load, charts render, top matches show
2. Jobs: table loads, filters work, job detail opens, save to application works
3. Applications: kanban shows saved jobs, drag between columns works
4. Scrapers: status shows, history loads (run scraper if Ollama available)
5. Settings: profile loads, notification config saves, scheduler config saves

- [ ] **Step 4: Fix any issues found during verification**

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "fix: integration fixes from end-to-end testing"
```

---

### Task 16: Polish and error handling

- [ ] **Step 1: Add loading states to all pages**

Every page should show `<LoadingSpinner />` while data is fetching, and an error message if fetch fails.

- [ ] **Step 2: Add empty states**

- Jobs page: "No jobs found matching your filters"
- Applications: "No applications yet. Save jobs from the Jobs page to get started."
- Scrapers history: "No scraper runs yet"

- [ ] **Step 3: Add toast notifications for actions**

When user saves a job, starts scraping, resets scores, etc. — show a brief toast notification at top-right.

- [ ] **Step 4: Responsive sidebar**

On mobile (< 768px), sidebar should collapse to icons only or slide out.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ frontend/src/components/ frontend/src/index.css
git commit -m "feat: add loading states, empty states, toasts, and responsive design"
```

---

### Task 17: Copy existing jobs.db and final setup

- [ ] **Step 1: Symlink or copy jobs.db to backend**

```bash
# The backend .env DATABASE_URL points to sqlite:///./jobs.db
# Copy the existing v4 database into the backend directory
cp C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4/jobs.db C:/Users/PC/OneDrive/Desktop/job-finder/job-finder-v4/backend/jobs.db
```

- [ ] **Step 2: Verify data loads in dashboard**

Start backend + frontend, verify Dashboard shows real stats from the 7,500+ jobs.

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "feat: Job Finder v5 Pro complete — full-stack web application"
```

---

## Execution Summary

| Chunk | Tasks | Description |
|-------|-------|-------------|
| **1: Backend** | Tasks 1-8 | Config, models, schemas, core, services, API, main.py |
| **2: Frontend** | Tasks 9-14 | Scaffold, dashboard, jobs, applications, scrapers, settings |
| **3: Integration** | Tasks 15-17 | E2E testing, polish, database migration |

**Total tasks:** 17
**Total new files:** ~55
**Estimated implementation:** Tasks are bite-sized and independently committable.

**To run the app:**
```bash
# Terminal 1: Backend
cd backend && python -m uvicorn app.main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend && npm run dev

# Open: http://localhost:5173
```
