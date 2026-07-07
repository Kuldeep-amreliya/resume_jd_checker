"""
SQLAlchemy ORM models — documents, profiles, matches.
"""
from datetime import datetime

from sqlalchemy import ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    doc_type: Mapped[str]  # 'resume' | 'jd'
    source_format: Mapped[str]  # pdf/docx/txt/raw
    raw_text: Mapped[str]
    char_count: Mapped[int]
    low_text_confidence: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"))
    profile_json: Mapped[dict] = mapped_column(JSON)
    llm_model: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True)
    resume_profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    jd_profile_id: Mapped[int] = mapped_column(ForeignKey("profiles.id"))
    overall_score: Mapped[int]
    score_breakdown_json: Mapped[dict] = mapped_column(JSON)
    matched_requirements_json: Mapped[list] = mapped_column(JSON)
    missing_requirements_json: Mapped[list] = mapped_column(JSON)
    unknown_requirements_json: Mapped[list] = mapped_column(JSON)
    semantic_matches_json: Mapped[list] = mapped_column(JSON)
    strengths_json: Mapped[list] = mapped_column(JSON)
    weaknesses_json: Mapped[list] = mapped_column(JSON)
    recommendations_json: Mapped[list] = mapped_column(JSON)
    explanation: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)