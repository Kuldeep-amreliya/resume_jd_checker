"""
Simple insert/fetch helpers. No business logic here — just persistence.

DB writes are treated as best-effort logging, not blocking: if a write
fails, the caller (api/routes_match.py) should catch it, log it, and still
return the computed result to the client. The user's result matters more
than the audit trail.
"""
import logging

from sqlalchemy.orm import Session

from app.database.models import Document, Profile, Match
from app.ingestion.ingestion_schemas import ExtractedDocument
from app.profiles.schemas import ResumeProfile, JDProfile
from app.scoring.scoring_schemas import MatchResult

logger = logging.getLogger(__name__)


def save_document(db: Session, doc_type: str, extracted: ExtractedDocument) -> Document:
    row = Document(
        doc_type=doc_type,
        source_format=extracted.source_format,
        raw_text=extracted.raw_text,
        char_count=extracted.char_count,
        low_text_confidence=extracted.low_text_confidence,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_profile(
    db: Session,
    document_id: int,
    profile: ResumeProfile | JDProfile,
    llm_model: str,
) -> Profile:
    row = Profile(
        document_id=document_id,
        profile_json=profile.model_dump(mode="json"),
        llm_model=llm_model,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_match(
    db: Session,
    resume_profile_id: int,
    jd_profile_id: int,
    result: MatchResult,
) -> Match:
    row = Match(
        resume_profile_id=resume_profile_id,
        jd_profile_id=jd_profile_id,
        overall_score=result.overall_score,
        score_breakdown_json={k: v.model_dump(mode="json") for k, v in result.score_breakdown.items()},
        matched_requirements_json=result.matched_requirements,
        missing_requirements_json=result.missing_requirements,
        unknown_requirements_json=result.unknown_requirements,
        semantic_matches_json=[m.model_dump(mode="json") for m in result.semantic_matches],
        strengths_json=result.strengths,
        weaknesses_json=result.weaknesses,
        recommendations_json=result.recommendations,
        explanation=result.explanation,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def get_match(db: Session, match_id: int) -> Match | None:
    return db.get(Match, match_id)


def get_profile(db: Session, profile_id: int) -> Profile | None:
    return db.get(Profile, profile_id)


def try_save_document(db: Session, doc_type: str, extracted: ExtractedDocument) -> Document | None:
    """Best-effort variant — logs and returns None on failure instead of raising,
    per the error-handling strategy: DB persistence never blocks the response."""
    try:
        return save_document(db, doc_type, extracted)
    except Exception as e:
        logger.error(f"Failed to save {doc_type} document: {e}")
        db.rollback()
        return None


def try_save_profile(
    db: Session, document_id: int | None, profile: ResumeProfile | JDProfile, llm_model: str
) -> Profile | None:
    if document_id is None:
        return None
    try:
        return save_profile(db, document_id, profile, llm_model)
    except Exception as e:
        logger.error(f"Failed to save profile for document {document_id}: {e}")
        db.rollback()
        return None


def try_save_match(
    db: Session, resume_profile_id: int | None, jd_profile_id: int | None, result: MatchResult
) -> Match | None:
    if resume_profile_id is None or jd_profile_id is None:
        return None
    try:
        return save_match(db, resume_profile_id, jd_profile_id, result)
    except Exception as e:
        logger.error(f"Failed to save match: {e}")
        db.rollback()
        return None