"""
Direct resume-vs-JD-skill matching via a single LLM call.

This exists because independently extracting a resume skill list and a JD
skill list and then diffing the two strings will never reliably converge —
"Basic AWS Knowledge" vs "AWS", "Developed REST APIs using FastAPI" vs
"REST APIs" are the same underlying fact expressed in different words, and
no amount of prompt tuning on the EXTRACTION side fixes that, because the
two extraction calls never see each other's vocabulary.

Instead: give one LLM call the JD's skill list AND the actual resume text
together, and ask it to judge each skill directly against the real text.
This still produces a strict, schema-validated, auditable list (matched/
partial/missing + evidence per skill) that scoring/engine.py turns into the
same deterministic CategoryScore it always has — the scoring math doesn't
change, only what feeds it.
"""
from app.llm.client import extract_json, LLMError
from app.llm.prompts import SKILL_MATCH_PROMPT
from app.scoring.scoring_schemas import SkillVerdict, SkillVerdictList


def match_skills_against_resume(
    resume_text: str,
    required_skills: list[str],
    preferred_skills: list[str],
) -> list[SkillVerdict]:
    """
    One LLM call, checking every required+preferred JD skill against the
    full resume text. Returns a SkillVerdict per skill.

    Raises LLMError if the call fails or the response can't be validated —
    same failure contract as build_resume_profile/build_jd_profile, so the
    API layer handles it identically (502, no silent fallback).
    """
    if not required_skills and not preferred_skills:
        return []

    lines = [f"- {s} (REQUIRED, is_required=true)" for s in required_skills]
    lines += [f"- {s} (PREFERRED, is_required=false)" for s in preferred_skills]
    skills_list = "\n".join(lines)

    prompt = SKILL_MATCH_PROMPT.format(skills_list=skills_list, resume_text=resume_text)

    result = extract_json(prompt, SkillVerdictList)

    # Defensive: if the model dropped a skill from its response, fail safe to
    # MISSING for it rather than silently under-reporting the total skill count
    # (which would distort the ratio in score_technical_skills).
    all_skills = [(s, True) for s in required_skills] + [(s, False) for s in preferred_skills]
    by_skill_lower = {v.skill.strip().lower(): v for v in result.verdicts}

    verdicts: list[SkillVerdict] = []
    for skill, is_required in all_skills:
        existing = by_skill_lower.get(skill.strip().lower())
        if existing is not None:
            verdicts.append(existing)
        else:
            verdicts.append(
                SkillVerdict(skill=skill, is_required=is_required, status="MISSING", evidence="")
            )

    return verdicts