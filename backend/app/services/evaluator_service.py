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
