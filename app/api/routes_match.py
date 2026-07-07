"""
POST /api/match, GET /api/match/{id}, GET /api/health.

Kept intentionally small — this is an analysis tool, not a CRUD app.
"""
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import crud
from app.database.session import get_db
from app.ingestion.router import extract_text
from app.ingestion.ingestion_schemas import IngestionError
from app.llm.client import LLMError
from app.llm.extraction import build_resume_profile, build_jd_profile
from app.schemas.api_schemas import MatchResponse, HealthResponse
from app.scoring.report import build_match_report
from app.llm.skill_matching import match_skills_against_resume


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["match"])


@router.get("/health", response_model=HealthResponse)
def health():
    settings = get_settings()
    return HealthResponse(status="ok", llm_configured=settings.llm_configured)


@router.post("/match", response_model=MatchResponse)
async def create_match(
    resume_file: UploadFile | None = File(default=None),
    resume_text: str | None = Form(default=None),
    jd_file: UploadFile | None = File(default=None),
    jd_text: str | None = Form(default=None),
    db: Session = Depends(get_db),
):
    settings = get_settings()

    # --- 1. Ingestion: accept either a file or raw text for each side ---
    if resume_file is None and not (resume_text and resume_text.strip()):
        raise HTTPException(status_code=422, detail="Provide either resume_file or resume_text.")
    if jd_file is None and not (jd_text and jd_text.strip()):
        raise HTTPException(status_code=422, detail="Provide either jd_file or jd_text.")

    try:
        resume_bytes = await resume_file.read() if resume_file is not None else None
        resume_doc = extract_text(
            file_bytes=resume_bytes,
            filename=resume_file.filename if resume_file else None,
            raw_text=resume_text,
        )

        jd_bytes = await jd_file.read() if jd_file is not None else None
        jd_doc = extract_text(
            file_bytes=jd_bytes,
            filename=jd_file.filename if jd_file else None,
            raw_text=jd_text,
        )
    except IngestionError as e:
        raise HTTPException(status_code=422, detail=e.message) from e

    # Persist raw documents (best-effort — never blocks the response)
    resume_doc_row = crud.try_save_document(db, "resume", resume_doc)
    jd_doc_row = crud.try_save_document(db, "jd", jd_doc)

    # --- 2. LLM extraction: resume + JD profiles ---
    try:
        resume_profile = build_resume_profile(resume_doc.raw_text)
        jd_profile = build_jd_profile(jd_doc.raw_text)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=e.message) from e

    resume_profile_row = crud.try_save_profile(
        db, resume_doc_row.id if resume_doc_row else None, resume_profile, settings.groq_model
    )
    jd_profile_row = crud.try_save_profile(
        db, jd_doc_row.id if jd_doc_row else None, jd_profile, settings.groq_model
    )

    # --- 3. Direct skill matching: LLM reads full resume text against each ---
    #        JD skill, rather than diffing two independently-extracted lists.
    #        See llm/skill_matching.py for why this replaced pure string diffing.
    try:
        skill_verdicts = match_skills_against_resume(
            resume_doc.raw_text,
            jd_profile.required_skills,
            jd_profile.preferred_skills,
        )
    except LLMError as e:
        raise HTTPException(status_code=502, detail=e.message) from e

    # --- 4. Scoring (deterministic) + explanation (1 LLM call) ---
    try:
        result = build_match_report(resume_profile, jd_profile, skill_verdicts)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=e.message) from e

    match_row = crud.try_save_match(
        db,
        resume_profile_row.id if resume_profile_row else None,
        jd_profile_row.id if jd_profile_row else None,
        result,
    )

    return MatchResponse(
        match_id=match_row.id if match_row else -1,
        overall_score=result.overall_score,
        score_breakdown=result.score_breakdown,
        matched_requirements=result.matched_requirements,
        missing_requirements=result.missing_requirements,
        unknown_requirements=result.unknown_requirements,
        semantic_matches=result.semantic_matches,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
        recommendations=result.recommendations,
        explanation=result.explanation,
        resume_profile=resume_profile,
        jd_profile=jd_profile,
    )


@router.get("/match/{match_id}", response_model=MatchResponse)
def get_match(match_id: int, db: Session = Depends(get_db)):
    match_row = crud.get_match(db, match_id)
    if match_row is None:
        raise HTTPException(status_code=404, detail=f"Match {match_id} not found.")

    resume_profile_row = crud.get_profile(db, match_row.resume_profile_id)
    jd_profile_row = crud.get_profile(db, match_row.jd_profile_id)
    if resume_profile_row is None or jd_profile_row is None:
        raise HTTPException(status_code=404, detail="Underlying profile data for this match is missing.")

    from app.profiles.schemas import ResumeProfile, JDProfile
    from app.scoring.scoring_schemas import CategoryScore, SemanticMatch

    resume_profile = ResumeProfile.model_validate(resume_profile_row.profile_json)
    jd_profile = JDProfile.model_validate(jd_profile_row.profile_json)
    score_breakdown = {
        k: CategoryScore.model_validate(v) for k, v in match_row.score_breakdown_json.items()
    }
    semantic_matches = [SemanticMatch.model_validate(m) for m in match_row.semantic_matches_json]

    return MatchResponse(
        match_id=match_row.id,
        overall_score=match_row.overall_score,
        score_breakdown=score_breakdown,
        matched_requirements=match_row.matched_requirements_json,
        missing_requirements=match_row.missing_requirements_json,
        unknown_requirements=match_row.unknown_requirements_json,
        semantic_matches=semantic_matches,
        strengths=match_row.strengths_json,
        weaknesses=match_row.weaknesses_json,
        recommendations=match_row.recommendations_json,
        explanation=match_row.explanation,
        resume_profile=resume_profile,
        jd_profile=jd_profile,
    )