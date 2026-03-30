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
