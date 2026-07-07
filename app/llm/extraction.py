"""
High-level extraction functions — the only place profiles.schemas and
llm.prompts/client meet. Everything else imports from here, not from
llm.client directly.
"""
from app.llm.client import extract_json, generate_text
from app.llm.prompts import RESUME_EXTRACTION_PROMPT, JD_EXTRACTION_PROMPT, EXPLANATION_PROMPT
from app.profiles.schemas import ResumeProfile, JDProfile
from datetime import date


def build_resume_profile(resume_text: str) -> ResumeProfile:
    current_date = date.today().strftime("%B %Y")  # e.g. "July 2026"
    prompt = RESUME_EXTRACTION_PROMPT.format(resume_text=resume_text, current_date=current_date)
    return extract_json(prompt, ResumeProfile)


def build_jd_profile(jd_text: str) -> JDProfile:
    prompt = JD_EXTRACTION_PROMPT.format(jd_text=jd_text)
    return extract_json(prompt, JDProfile)


def generate_explanation(
    overall_score: int,
    score_breakdown: dict,
    matched_requirements: list[str],
    missing_requirements: list[str],
    unknown_requirements: list[str],
    strengths: list[str],
    weaknesses: list[str],
) -> str:
    """
    The ONLY free-text LLM call in the pipeline. Takes an already-finalized
    score and breakdown (computed deterministically by the scoring engine)
    and turns it into recruiter-style prose. This function does not and
    cannot change the score — it only narrates it.
    """
    prompt = EXPLANATION_PROMPT.format(
        overall_score=overall_score,
        score_breakdown="\n".join(f"- {k}: {v}" for k, v in score_breakdown.items()),
        matched_requirements="\n".join(f"- {m}" for m in matched_requirements) or "(none)",
        missing_requirements="\n".join(f"- {m}" for m in missing_requirements) or "(none)",
        unknown_requirements="\n".join(f"- {m}" for m in unknown_requirements) or "(none)",
        strengths="\n".join(f"- {s}" for s in strengths) or "(none)",
        weaknesses="\n".join(f"- {w}" for w in weaknesses) or "(none)",
    )
    return generate_text(prompt)