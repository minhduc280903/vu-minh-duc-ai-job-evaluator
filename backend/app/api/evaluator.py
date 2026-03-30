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
