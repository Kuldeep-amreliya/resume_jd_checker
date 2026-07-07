"""
Single entry point for document ingestion.

Accepts EITHER an uploaded file (pdf/docx/txt) OR raw pasted text for a
resume/JD, and always returns a uniform ExtractedDocument — nothing
downstream needs to branch on file type ever again.

File type is detected from magic bytes first (don't trust the extension/
content-type header — they can lie or be missing), falling back to the
filename extension only if magic-byte sniffing is inconclusive.
"""
from app.config import get_settings
from app.ingestion.extractors import extract_pdf_text, extract_docx_text, extract_txt_text
from app.ingestion.ingestion_schemas import ExtractedDocument, IngestionError

# Magic bytes for supported formats.
PDF_MAGIC = b"%PDF-"
DOCX_MAGIC = b"PK\x03\x04"  # DOCX (and any OOXML/zip-based format) starts as a ZIP


def _sniff_format(file_bytes: bytes, filename: str | None) -> str:
    """Return one of 'pdf', 'docx', 'txt' based on content, falling back to extension."""
    if file_bytes.startswith(PDF_MAGIC):
        return "pdf"
    if file_bytes.startswith(DOCX_MAGIC):
        # Zip-based — almost certainly docx here since that's all we support,
        # but confirm via extension if available to give a clearer error otherwise.
        if filename and filename.lower().endswith(".docx"):
            return "docx"
        # Could still genuinely be a .docx with a stripped/renamed extension; python-docx
        # will raise its own clear error if it turns out not to be a real Word doc.
        return "docx"

    # Not a recognized binary magic — fall back to extension for plain text.
    if filename:
        lower = filename.lower()
        if lower.endswith(".txt"):
            return "txt"
        if lower.endswith(".pdf"):
            return "pdf"  # extension says pdf but magic bytes didn't match -> will raise a clear error downstream
        if lower.endswith(".docx"):
            return "docx"

    # No extension and no recognizable magic bytes — treat as plain text as a last resort.
    return "txt"


def extract_text(
    file_bytes: bytes | None = None,
    filename: str | None = None,
    raw_text: str | None = None,
) -> ExtractedDocument:
    """
    The one function the rest of the app calls for ingestion.

    Exactly one of (file_bytes, raw_text) should be provided:
      - file_bytes + filename -> detect format, extract accordingly
      - raw_text -> passthrough, source_format="raw"

    Raises IngestionError for anything unrecoverable (empty input, corrupt
    file, unsupported format). Never raises for "extraction succeeded but
    text looks thin" — that's surfaced via low_text_confidence/warnings instead.
    """
    settings = get_settings()

    if raw_text is not None and raw_text.strip():
        text = raw_text.strip()
        return ExtractedDocument(
            raw_text=text,
            source_format="raw",
            char_count=len(text),
            low_text_confidence=False,
            warnings=[],
        )

    if file_bytes is None or len(file_bytes) == 0:
        raise IngestionError("No document provided. Supply either a file upload or raw text.")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise IngestionError(
            f"File is too large (max {settings.max_upload_size_mb}MB)."
        )

    fmt = _sniff_format(file_bytes, filename)

    if fmt == "pdf":
        text, low_conf, warnings = extract_pdf_text(
            file_bytes, settings.low_text_confidence_char_threshold
        )
    elif fmt == "docx":
        text, warnings = extract_docx_text(file_bytes)
        low_conf = len(text) < settings.low_text_confidence_char_threshold
        if low_conf and "No readable text found" not in " ".join(warnings):
            warnings.append("Very little text extracted from this DOCX file.")
    elif fmt == "txt":
        text, warnings = extract_txt_text(file_bytes)
        low_conf = len(text) < settings.low_text_confidence_char_threshold
    else:
        raise IngestionError(f"Unsupported file format: {fmt}")

    if not text:
        raise IngestionError(
            "No text could be extracted from this document.",
            detail="The file may be empty, corrupt, or an image-only scan.",
        )

    return ExtractedDocument(
        raw_text=text,
        source_format=fmt,
        char_count=len(text),
        low_text_confidence=low_conf,
        warnings=warnings,
    )