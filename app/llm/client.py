"""
Thin wrapper around the Groq SDK.

Everything that talks to Groq goes through here — if we ever swap providers,
this is the only file that changes.

Two responsibilities:
  - extract_json(): call the model, enforce JSON response format, validate
    against a Pydantic schema, and repair-retry once if validation fails.
  - generate_text(): plain free-text generation (used only for the final
    explanation step, which deliberately does NOT return JSON).
"""
import json
import logging
from typing import Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the LLM call fails or returns unusable output after retries.
    Caught at the API layer and turned into a 502, never a raw 500."""

    def __init__(self, message: str, detail: str | None = None):
        self.message = message
        self.detail = detail
        super().__init__(message)


def _get_groq_client():
    settings = get_settings()
    if not settings.groq_api_key:
        raise LLMError(
            "AI service is not configured.",
            detail="GROQ_API_KEY is not set on the server.",
        )
    try:
        from groq import Groq
    except ImportError as e:
        raise LLMError(
            "AI service library is not installed.",
            detail="Install with: pip install groq",
        ) from e

    return Groq(api_key=settings.groq_api_key, timeout=settings.groq_timeout_seconds)


def _strip_json_fences(text: str) -> str:
    """Defensive cleanup — even with response_format json_object, models
    occasionally wrap output in ```json fences. Strip them if present."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # drop first fence line (``` or ```json) and trailing ``` if present
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def extract_json(prompt: str, schema: Type[T]) -> T:
    """
    Call the LLM expecting strict JSON matching `schema`.

    Flow: call -> parse -> validate. If parse/validate fails, retry ONCE with
    a repair prompt that includes the error. If that also fails, raise LLMError
    rather than fabricating a default/empty profile — a silently-empty profile
    would produce a misleading score, which is worse than a clear failure.
    """
    settings = get_settings()
    client = _get_groq_client()

    messages = [{"role": "user", "content": prompt}]

    last_error: str | None = None

    for attempt in range(settings.groq_max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=settings.groq_model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.1,  # low temperature — this is extraction, not creative writing
            )
        except Exception as e:
            logger.error(f"Groq API call failed (attempt {attempt + 1}): {e}")
            last_error = str(e)
            continue

        raw_content = response.choices[0].message.content or ""
        cleaned = _strip_json_fences(raw_content)

        try:
            parsed = json.loads(cleaned)
            validated = schema.model_validate(parsed)
            return validated
        except (json.JSONDecodeError, ValidationError) as e:
            last_error = str(e)
            logger.warning(f"LLM output failed validation (attempt {attempt + 1}): {e}")

            # build a repair prompt for the next attempt
            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": raw_content},
                {
                    "role": "user",
                    "content": (
                        "That JSON was invalid or did not match the required schema. "
                        f"Error: {e}\n\n"
                        "Return ONLY the corrected, valid JSON object. No markdown fences, no commentary."
                    ),
                },
            ]

    raise LLMError(
        "AI service returned an unusable response after retries.",
        detail=last_error,
    )


def generate_text(prompt: str) -> str:
    """Free-text generation — used only for the final explanation step."""
    settings = get_settings()
    client = _get_groq_client()

    try:
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,  # a little more natural language latitude, still not creative-writing high
        )
    except Exception as e:
        raise LLMError("AI service call failed while generating explanation.", detail=str(e)) from e

    return (response.choices[0].message.content or "").strip()