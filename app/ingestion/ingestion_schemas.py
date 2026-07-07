"""
Ingestion-layer data contracts.

ExtractedDocument is the uniform shape every extractor (PDF/DOCX/TXT/raw
text) normalizes into — nothing downstream (crud, LLM extraction) needs to
know or care what format the original document was in.

IngestionError is raised for anything unrecoverable during ingestion
(corrupt file, unsupported format, empty input, missing optional
dependency). It is caught in api/routes_match.py and turned into a 422.
"""
from pydantic import BaseModel, Field


class ExtractedDocument(BaseModel):
    raw_text: str
    source_format: str  # "pdf" | "docx" | "txt" | "raw"
    char_count: int
    low_text_confidence: bool = False
    warnings: list[str] = Field(default_factory=list)


class IngestionError(Exception):
    """Raised for unrecoverable ingestion failures. Carries a user-facing
    message plus an optional technical detail string for logs/debugging."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)