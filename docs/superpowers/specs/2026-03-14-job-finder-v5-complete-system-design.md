# Job Finder v5 Pro — Complete System Design

## 1. Overview

Transform the existing CLI-based job scraping tool (v4) into a full-stack web application with:
- Modern dark-themed React dashboard
- FastAPI REST API + WebSocket backend
- Application tracking (Kanban board)
- Auto-scheduling & notifications (Telegram/Email)
- Refactored, production-quality codebase

### Current State (v4)
- 6 working scrapers (Ybox, VietnamWorks, TopCV, ITviec, CareerViet, Joboko)
- Two-stage evaluation: keyword scoring + Ollama LLM (qwen2.5:14b)
- SQLite database with 7,500+ jobs
- CLI-only interface, Excel export
- Hardcoded config, minimal error handling, no tests

### Target State (v5)
- Full web UI with 5 pages (Dashboard, Jobs, Applications, Scrapers, Settings)
- REST API serving all data to the frontend
- Real-time scraper monitoring via WebSocket
- Background scheduler for auto-scraping and notifications
- Proper project structure, config management, error handling

## 2. Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 REACT FRONTEND                          │
│  Vite + TailwindCSS + Recharts + Zustand + React Query  │
│  Pages: Dashboard | Jobs | Applications | Scrapers | Settings │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP REST + WebSocket
┌───────────────────────┴─────────────────────────────────┐
│                 FASTAPI BACKEND                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │ API Layer: /api/jobs /api/scrapers /api/eval     │    │
│  │            /api/applications /api/stats /api/ws  │    │
│  └──────────────────┬──────────────────────────────┘    │
│  ┌──────────────────┴──────────────────────────────┐    │
│  │ Service Layer                                    │    │
│  │ JobService | ScraperService | EvaluatorService   │    │
│  │ ApplicationService | NotificationService         │    │
│  └──────────────────┬──────────────────────────────┘    │
│  ┌──────────────────┴──────────────────────────────┐    │
│  │ Core: Scoring Engine | LLM Client | Scheduler   │    │
│  └──────────────────┬──────────────────────────────┘    │
│  ┌──────────────────┴──────────────────────────────┐    │
│  │ Scrapers: BaseScraper → 6 implementations       │    │
│  └──────────────────┬──────────────────────────────┘    │
│  ┌──────────────────┴──────────────────────────────┐    │
│  │ SQLite + SQLAlchemy ORM                          │    │
│  └─────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────┐    │
│  │ Ollama LLM (localhost:11434)                     │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 3. Database Schema

### 3.0 Tier Score Thresholds (Business Logic)

Tiers are determined by `final_score` (or `keyword_score` if LLM not yet run):

| Tier | Score Range | Color | Meaning |
|------|-------------|-------|---------|
| S    | 75-100      | #10b981 (emerald) | Perfect match |
| A    | 50-74       | #3b82f6 (blue) | Strong match |
| B    | 35-49       | #f59e0b (amber) | Moderate match |
| C    | 1-34        | #ef4444 (red) | Weak match |

These thresholds are defined as constants in `backend/app/core/scoring.py` and shared with the frontend via `GET /api/jobs/stats` response. Both backend filtering and frontend display use the same values.

### 3.1 Existing table: `jobs` (migrated from v4)

The `id` column is the single-column PRIMARY KEY and is globally unique (each scraper prefixes IDs: `vnw_`, `cv_`, `it_`, etc., or uses platform-native UUIDs). The `UNIQUE(id, platform)` constraint is redundant but harmless and will be kept for backward compatibility.

All existing columns preserved:
- id (TEXT PRIMARY KEY — globally unique), platform, title, company, url, summary, deadline, views, published_at
- salary, domain, level, location, skills, requirements, benefits, description
- raw_data, relevance_score, evaluation_reason
- keyword_score, llm_score, final_score, llm_rationale, llm_pros, llm_cons
- scraped_at

### 3.2 New table: `applications`

```sql
CREATE TABLE applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'saved',
    -- status: saved | applied | interview | offer | rejected
    applied_at TIMESTAMP,
    notes TEXT,
    interview_date TIMESTAMP,
    interview_notes TEXT,
    salary_offered TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### 3.3 New table: `scraper_runs`

```sql
CREATE TABLE scraper_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    platform TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    -- status: running | completed | failed
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    jobs_found INTEGER DEFAULT 0,
    jobs_new INTEGER DEFAULT 0,
    jobs_updated INTEGER DEFAULT 0,
    error_message TEXT,
    triggered_by TEXT DEFAULT 'manual'
    -- triggered_by: manual | scheduler
);
```

### 3.4 New table: `notification_settings`

```sql
CREATE TABLE notification_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL,
    -- channel: telegram | email
    enabled INTEGER DEFAULT 0,
    config TEXT,
    -- JSON: {token, chat_id} for telegram; {smtp_host, email, password} for email
    min_tier TEXT DEFAULT 'A',
    -- minimum tier to notify: S | A | B
    daily_digest INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 3.5 New table: `scheduler_config`

```sql
CREATE TABLE scheduler_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT NOT NULL UNIQUE,
    -- task_name: auto_scrape | auto_evaluate | daily_report
    enabled INTEGER DEFAULT 0,
    cron_expression TEXT NOT NULL,
    -- e.g., "0 6 * * *" for 6am daily
    last_run TIMESTAMP,
    next_run TIMESTAMP,
    config TEXT
    -- JSON: additional task-specific config
);
```

## 4. Backend API Design

### 4.1 Job Endpoints

```
GET    /api/jobs                    List jobs (paginated, filtered, sorted)
  Query params:
    - page (int, default 1)
    - per_page (int, default 50)
    - tier (str: S|A|B|C)
    - platform (str)
    - min_score (int)
    - max_score (int)
    - location (str)
    - has_salary (bool)
    - search (str, full-text search in title/company/description)
    - sort_by (str: final_score|keyword_score|llm_score|scraped_at)
    - sort_order (str: asc|desc)

GET    /api/jobs/{id}               Get job details (id is globally unique)
GET    /api/jobs/stats              Get aggregated statistics
  Response: {total, by_tier: {S, A, B, C}, by_platform: {...},
             evaluated, pending_eval, avg_score, new_today}
```

### 4.2 Scraper Endpoints

```
POST   /api/scrapers/run            Start scraping (all or specific platforms)
  Body: {platforms: ["all"] | ["ybox", "vnw", ...]}
GET    /api/scrapers/status          Get current scraper status
GET    /api/scrapers/history         Get scraper run history
POST   /api/scrapers/stop            Stop running scrapers
```

### 4.3 Evaluator Endpoints

```
POST   /api/evaluator/keyword        Run keyword scoring on all/new jobs
POST   /api/evaluator/llm            Run LLM evaluation on candidates
GET    /api/evaluator/status          Get evaluation progress
POST   /api/evaluator/reset           Reset all scores
```

### 4.4 Application Endpoints

```
GET    /api/applications              List all applications (grouped by status)
POST   /api/applications              Create application (save/apply to job)
  Body: {job_id, status, notes}
PATCH  /api/applications/{id}         Update application status/notes
DELETE /api/applications/{id}         Remove application
GET    /api/applications/stats        Application stats (by status)
```

### 4.5 Settings Endpoints

```
GET    /api/settings/profile          Get user profile (from user_profile.json)
PUT    /api/settings/profile          Update user profile
GET    /api/settings/notifications    Get notification settings
PUT    /api/settings/notifications    Update notification settings
GET    /api/settings/scheduler        Get scheduler config
PUT    /api/settings/scheduler        Update scheduler config
POST   /api/settings/test-telegram    Test telegram notification
POST   /api/settings/test-email       Test email notification
```

### 4.6 WebSocket Endpoint

```
WS     /api/ws                        Real-time updates
  Messages (server → client):
    - {type: "scraper_progress", platform, page, jobs_found, status}
    - {type: "scraper_complete", platform, total_new, total_updated}
    - {type: "scraper_log", platform, level, message, timestamp}
    - {type: "eval_progress", evaluated, total, current_job}
    - {type: "new_match", job, tier, score}
    - {type: "notification_sent", channel, job_count}
```

## 5. Frontend Design

### 5.1 Tech Stack
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- React Router v6 (routing)
- React Query / TanStack Query (server state)
- Zustand (UI state)
- Recharts (charts)
- Lucide React (icons)
- @hello-pangea/dnd (kanban drag & drop — maintained fork of react-beautiful-dnd)

### 5.2 Theme: Modern Dark
- Background: `#0f172a` (slate-900)
- Card bg: `#1e293b` (slate-800)
- Border: `#334155` (slate-700)
- Text primary: `#f8fafc` (slate-50)
- Text secondary: `#94a3b8` (slate-400)
- Tier S: `#10b981` (emerald-500)
- Tier A: `#3b82f6` (blue-500)
- Tier B: `#f59e0b` (amber-500)
- Tier C: `#ef4444` (red-500)
- Accent: `#a78bfa` (violet-400)
- Border radius: 12px for cards, 8px for buttons

### 5.3 Pages

#### Dashboard Page
- 4 stat cards: Total Jobs, Tier S Matches, Applied Count, AI Evaluated Count
- Score distribution bar chart (Recharts)
- Platform breakdown (horizontal bars)
- Top 5 matches table (quick view)
- Greeting with new jobs count

#### Jobs Page
- Filter bar: Tier, Platform, Location, Salary, Score range, Search
- Data table with sortable columns: Tier, Score, Title, Company, Salary, Location, Platform
- Click row → Job detail slide-over panel
- Job detail shows: full description, requirements, AI rationale, pros/cons, score breakdown
- Actions: Save, Apply, Open URL, Dismiss

#### Applications Page
- Kanban board with 5 columns: Saved | Applied | Interview | Offer | Rejected
- Drag & drop cards between columns
- Each card: job title, company, tier badge, score, date
- Click card → detail panel with notes, interview dates, salary info
- Add/edit notes inline

#### Scrapers Page
- Platform cards (6) showing: last run, jobs found, status indicator
- "Run All" and individual "Run" buttons
- Real-time progress bar when running (WebSocket)
- Run history table: timestamp, platform, jobs found/new/updated, duration, status
- Live log stream when scraper is running

#### Settings Page
- **Profile tab**: Edit user_profile.json fields (name, skills, keywords, scoring weights)
- **Notifications tab**: Toggle Telegram/Email, configure credentials, set minimum tier, test button
- **Scheduler tab**: Configure cron jobs (auto-scrape time, auto-evaluate, daily report), enable/disable

### 5.4 Component Tree

```
App
├── Layout
│   ├── Sidebar (nav items, scheduler status)
│   └── MainContent
│       ├── DashboardPage
│       │   ├── StatsCards
│       │   ├── ScoreChart
│       │   ├── PlatformBreakdown
│       │   └── TopMatchesTable
│       ├── JobsPage
│       │   ├── JobFilters
│       │   ├── JobTable
│       │   └── JobDetailPanel
│       ├── ApplicationsPage
│       │   ├── KanbanBoard
│       │   │   └── KanbanColumn → ApplicationCard
│       │   └── ApplicationDetailPanel
│       ├── ScrapersPage
│       │   ├── ScraperCards
│       │   ├── ScraperProgress (WebSocket)
│       │   └── RunHistoryTable
│       └── SettingsPage
│           ├── ProfileEditor
│           ├── NotificationSettings
│           └── SchedulerSettings
```

## 6. Backend Structure

### 6.1 Project Layout

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, CORS, lifespan
│   ├── config.py                  # Settings from .env (pydantic-settings)
│   ├── database.py                # SQLAlchemy engine, session, Base
│   │
│   ├── models/                    # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   ├── job.py
│   │   ├── application.py
│   │   ├── scraper_run.py
│   │   ├── notification.py
│   │   └── scheduler.py
│   │
│   ├── schemas/                   # Pydantic request/response schemas
│   │   ├── __init__.py
│   │   ├── job.py
│   │   ├── application.py
│   │   ├── scraper.py
│   │   ├── evaluator.py
│   │   ├── stats.py
│   │   └── settings.py
│   │
│   ├── api/                       # Route handlers
│   │   ├── __init__.py
│   │   ├── jobs.py
│   │   ├── scrapers.py
│   │   ├── evaluator.py
│   │   ├── applications.py
│   │   ├── stats.py
│   │   ├── settings.py
│   │   └── websocket.py
│   │
│   ├── services/                  # Business logic
│   │   ├── __init__.py
│   │   ├── job_service.py
│   │   ├── scraper_service.py
│   │   ├── evaluator_service.py
│   │   ├── application_service.py
│   │   ├── notification_service.py
│   │   └── scheduler_service.py
│   │
│   ├── scrapers/                  # Refactored scrapers
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract BaseScraper
│   │   ├── ybox.py
│   │   ├── vietnamworks.py
│   │   ├── topcv.py
│   │   ├── itviec.py
│   │   ├── careerviet.py
│   │   └── joboko.py
│   │
│   └── core/                      # Core utilities
│       ├── __init__.py
│       ├── scoring.py             # Keyword scoring engine (from v4)
│       ├── llm.py                 # Ollama client with retry
│       └── scheduler.py           # APScheduler setup
│
├── requirements.txt
├── .env.example
└── alembic/                       # DB migrations (optional)
```

### 6.2 Scraper Refactoring

Abstract `BaseScraper` to eliminate duplication:

```python
class BaseScraper(ABC):
    platform: str

    def __init__(self, db_session, ws_manager=None):
        """Receive SQLAlchemy session and optional WebSocket manager from service layer."""
        self.db = db_session
        self.ws = ws_manager

    @abstractmethod
    async def fetch_page(self, session, page, **kwargs) -> dict | None:
        """Fetch a single page of results."""

    @abstractmethod
    def parse_jobs(self, raw_data) -> list[dict]:
        """Parse raw API/HTML response into job dicts."""

    async def scrape(self, **kwargs) -> ScrapeResult:
        """Common scrape loop with error handling, progress reporting, and DB save.
        Checks self._cancelled flag between pages for cooperative cancellation."""

    def save_jobs(self, jobs: list[dict]) -> tuple[int, int]:
        """Save via SQLAlchemy session with smart upsert."""

    async def report_progress(self, page, total, jobs_found):
        """Report progress via WebSocket manager (if connected)."""

    def cancel(self):
        """Set cancellation flag for cooperative shutdown."""
        self._cancelled = True
```

### 6.3 LLM Client Improvements

```python
class OllamaClient:
    def __init__(self, url, model, timeout=120, max_retries=3):
        self.url = url
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    async def evaluate_job(self, job, system_prompt) -> EvalResult:
        """Evaluate with retry logic and JSON validation."""
        for attempt in range(self.max_retries):
            try:
                result = await self._call_ollama(job, system_prompt)
                return self._parse_and_validate(result)
            except (JSONDecodeError, TimeoutError) as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # exponential backoff
                    continue
                return EvalResult(score=-1, error=str(e))
```

### 6.4 Configuration (.env)

```env
# Database
DATABASE_URL=sqlite:///./jobs.db

# Ollama LLM
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b
LLM_TIMEOUT=120
LLM_THRESHOLD=25
LLM_MAX_RETRIES=3
LLM_BATCH_SIZE=1

# Notifications
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=
SMTP_PASSWORD=

# Scheduler
AUTO_SCRAPE_CRON=0 6 * * *
AUTO_EVALUATE_CRON=0 7 * * *
DAILY_REPORT_CRON=0 8 * * *

# App
APP_HOST=0.0.0.0
APP_PORT=8000
CORS_ORIGINS=http://localhost:5173
```

## 7. Notification System

### 7.1 Telegram Bot
- Create bot via @BotFather
- Send notifications when new Tier S/A jobs found after scraping
- Daily digest: top 10 new matches with scores, companies, links
- Format: Markdown message with tier badges and clickable URLs

### 7.2 Email
- SMTP integration (Gmail App Password or custom SMTP)
- HTML email template with job cards, tier colors, scores
- Weekly summary in HTML table format (no chart images — dashboard is available for visuals)

## 8. Scheduler System

Using APScheduler with SQLite job store:

### Default Jobs
1. **Auto-scrape**: Daily at 6:00 AM — run all scrapers
2. **Auto-evaluate**: Daily at 7:00 AM — keyword + LLM scoring on new jobs
3. **Daily report**: Daily at 8:00 AM — send Telegram/Email digest

All configurable via Settings page. Can be enabled/disabled independently.

## 9. Migration Strategy

Phases are sequential. Phase 1 must complete before Phase 2 starts (frontend needs working API). Phase 3 connects them. Phase 4 is polish.

### Phase 1: Backend restructure (must complete first — frontend depends on working API)
1. Create `backend/` directory structure
2. Move and refactor scrapers into `BaseScraper` pattern
3. Create FastAPI app with all endpoints
4. Create SQLAlchemy models (preserve existing jobs table, add new tables)
5. Create service layer
6. Add .env config, requirements.txt
7. Migrate existing evaluation logic to service layer
8. Add LLM retry logic
9. **Success criteria**: All API endpoints return correct data from existing jobs.db. Scrapers run via API. Evaluator works via API.

### Phase 2: Frontend (requires Phase 1 API to be working)
1. Scaffold React + Vite + TailwindCSS project
2. Build Layout (sidebar + main content)
3. Build Dashboard page with charts
4. Build Jobs page with table + filters + detail panel
5. Build Applications Kanban page
6. Build Scrapers control page with WebSocket
7. Build Settings page
8. **Success criteria**: All 5 pages render with real data from backend API.

### Phase 3: Integration (requires both Phase 1 and Phase 2)
1. Connect frontend to backend API (if not already done in Phase 2)
2. Implement WebSocket for real-time updates
3. Add Telegram bot integration
4. Add Email notification
5. Configure APScheduler
6. End-to-end testing
7. **Success criteria**: Full workflow works: scrape → evaluate → view → apply → notify.

### Phase 4: Polish
1. Error handling & loading states
2. Responsive design (mobile-friendly)
3. Performance optimization (pagination, lazy loading)
4. Add requirements.txt and setup instructions
5. **Success criteria**: No unhandled errors. Works on mobile browsers.

## 10. Key Files to Create

### Backend (~25 files)
- `backend/app/main.py` — FastAPI entry point
- `backend/app/config.py` — Pydantic settings
- `backend/app/database.py` — SQLAlchemy setup
- `backend/app/models/*.py` — 5 model files
- `backend/app/schemas/*.py` — 7 schema files
- `backend/app/api/*.py` — 7 route files
- `backend/app/services/*.py` — 6 service files
- `backend/app/scrapers/*.py` — 7 scraper files (base + 6)
- `backend/app/core/*.py` — 3 core files
- `backend/requirements.txt`
- `backend/.env.example`

### Frontend (~30 files)
- `frontend/src/App.tsx` — Router setup
- `frontend/src/main.tsx` — Entry point
- `frontend/src/pages/*.tsx` — 5 page files
- `frontend/src/components/**/*.tsx` — ~15 component files
- `frontend/src/hooks/*.ts` — 3-4 hook files
- `frontend/src/api/client.ts` — API client
- `frontend/src/stores/appStore.ts` — Zustand store
- `frontend/src/types/index.ts` — TypeScript types
- `frontend/package.json`
- `frontend/tailwind.config.js`
- `frontend/vite.config.ts`

Total: ~55 new files

## 11. Non-Goals (YAGNI)

- User authentication/multi-user (this is a personal tool)
- PostgreSQL/MySQL migration (SQLite is fine for this scale)
- Docker/containerization (local tool)
- CI/CD pipeline (personal project)
- Unit tests (focus on working system first)
- i18n/localization (Vietnamese + English hardcoded is fine)
