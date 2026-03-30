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
