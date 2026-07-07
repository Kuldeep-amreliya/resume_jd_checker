"""
Output schemas for the scoring engine. Nothing in this file touches the LLM.
"""
from typing import Literal
from pydantic import BaseModel, Field


class CategoryScore(BaseModel):
    status: Literal["MATCHED", "PARTIAL", "MISSING", "UNKNOWN"]
    score: float  # 0.0-1.0 normalized score for this category
    weight: float  # this category's weight in the overall score
    notes: str = ""


class SemanticMatch(BaseModel):
    resume_term: str
    jd_term: str
    similarity_basis: Literal["llm_capability", "embedding"]
    similarity_score: float | None = None  # only set for embedding-based matches


class MatchResult(BaseModel):
    overall_score: int
    score_breakdown: dict[str, CategoryScore]
    matched_requirements: list[str] = Field(default_factory=list)
    missing_requirements: list[str] = Field(default_factory=list)
    unknown_requirements: list[str] = Field(default_factory=list)
    semantic_matches: list[SemanticMatch] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    explanation: str = ""  # filled in AFTER this object is built, by a separate LLM call


class SkillVerdict(BaseModel):
    """One JD skill's match status against the actual resume text, as judged
    directly by an LLM reading both — not derived from diffing two
    independently-extracted skill lists (see llm/skill_matching.py for why)."""
    skill: str                          # the JD skill/requirement text, verbatim
    is_required: bool                   # True if from required_skills, False if preferred_skills
    status: Literal["MATCHED", "PARTIAL", "MISSING"]
    evidence: str = ""                  # short quote/paraphrase from the resume, or "" if MISSING


class SkillVerdictList(BaseModel):
    """Wrapper so extract_json() can validate a JSON array via a schema
    (Pydantic needs a model, not a bare list, as the top-level validation
    target)."""
    verdicts: list[SkillVerdict]