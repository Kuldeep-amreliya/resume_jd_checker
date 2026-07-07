"""
Structured profile schemas — the LLM's output contract.

These are the shapes llm.extraction.build_resume_profile() and
build_jd_profile() validate Groq's JSON output against (via
llm.client.extract_json). Field names here must match the JSON schema
described in llm/prompts.py exactly, since that's what the model is
instructed to produce.

Nothing in this file touches the LLM or the DB — these are pure data
contracts, consumed by scoring/engine.py on one side and persisted as
JSON by database/models.py on the other.
"""
from typing import Literal
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Resume-side nested entries
# ---------------------------------------------------------------------------

class EducationEntry(BaseModel):
    degree: str | None = None
    institution: str | None = None
    field_of_study: str | None = None
    gpa_or_cgpa: float | None = None
    graduation_year: int | None = None


class ExperienceEntry(BaseModel):
    title: str | None = None
    company: str | None = None
    duration_months: int | None = None
    responsibilities: list[str] = Field(default_factory=list)
    inferred_skills: list[str] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str | None = None
    description: str | None = None
    tech_used: list[str] = Field(default_factory=list)
    inferred_capabilities: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# JD-side nested entries
# ---------------------------------------------------------------------------

class Constraint(BaseModel):
    type: str
    description: str
    value: str | None = None
    is_must_have: bool = True


# ---------------------------------------------------------------------------
# Top-level profiles
# ---------------------------------------------------------------------------

class ResumeProfile(BaseModel):
    personal_information: dict = Field(default_factory=dict)  # name/email/phone — optional, never scored
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    technical_skills: list[str] = Field(default_factory=list)
    soft_skills: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    cloud: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    inferred_capabilities: list[str] = Field(default_factory=list)
    career_level: Literal["intern", "junior", "mid", "senior", "lead", "unknown"] = "unknown"
    total_experience_months: int | None = None  # None = UNKNOWN, never assume 0
    summary: str = ""


class JDProfile(BaseModel):
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    required_experience_months: int | None = None  # None = not specified in the JD
    education_requirements: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    domains: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    must_have_constraints: list[Constraint] = Field(default_factory=list)
    preferred_constraints: list[Constraint] = Field(default_factory=list)
    inferred_requirement_capabilities: list[str] = Field(default_factory=list)
    career_level_expected: str = ""
    summary: str = ""