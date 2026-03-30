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
