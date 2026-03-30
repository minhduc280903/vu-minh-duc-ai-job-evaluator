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
