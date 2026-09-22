from __future__ import annotations

import os
from dataclasses import dataclass


def _float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


@dataclass(frozen=True)
class Settings:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://capstone:capstone@localhost:5432/capstone")
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    vision_model: str = os.getenv("VISION_MODEL", "gemini-3.1-flash-lite")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-2")
    ai_budget_usd: float = _float("AI_BUDGET_USD", 0.10)
    ai_max_calls_per_job: int = _int("AI_MAX_CALLS_PER_JOB", 160)
    vision_confidence_threshold: float = _float("VISION_CONFIDENCE_THRESHOLD", 0.70)
    match_similarity_threshold: float = _float("MATCH_SIMILARITY_THRESHOLD", 0.70)
    ai_mode: str = os.getenv("AI_MODE", "fixture")


settings = Settings()

