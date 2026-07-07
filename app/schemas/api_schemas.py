"""
API request/response Pydantic models — NOT DB models, NOT the LLM profile
contracts (those live in profiles/schemas.py). This is purely the shape of
what /api/match returns to the client.
"""
from pydantic import BaseModel, Field

from app.profiles.schemas import ResumeProfile, JDProfile
from app.scoring.scoring_schemas import CategoryScore, SemanticMatch


class MatchResponse(BaseModel):
    match_id: int
    overall_score: int
    score_breakdown: dict[str, CategoryScore]
    matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    unknown_requirements: list[str] = Field(default_factory=list)
    semantic_matches: list[SemanticMatch] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explanation: str
    resume_profile: ResumeProfile
    jd_profile: JDProfile


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool


class ErrorResponse(BaseModel):
    message: str
    detail: str | None = None