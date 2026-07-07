"""
Final report assembly.

Takes a MatchResult (already fully scored by scoring.engine.compute_match,
zero LLM involvement) and fills in its `explanation` field via one short,
free-text LLM call — the only place scoring/ touches the LLM directly for
narration, plus one upstream LLM call (skill matching) that scoring/engine.py
now depends on for its technical_skills category — see llm/skill_matching.py
for why that replaced pure string-diffing.
"""
from app.llm.extraction import generate_explanation
from app.profiles.schemas import ResumeProfile, JDProfile
from app.scoring.engine import compute_match
from app.scoring.scoring_schemas import MatchResult, SkillVerdict


def build_match_report(
    resume: ResumeProfile, jd: JDProfile, skill_verdicts: list[SkillVerdict]
) -> MatchResult:
    """
    End-to-end: score deterministically, then narrate the result.

    1. compute_match() — pure Python, deterministic, produces every number
       and category breakdown from the profiles PLUS the LLM-judged skill
       verdicts. explanation is left as "".
    2. generate_explanation() — one Groq call, fed the finalized numbers,
       told explicitly not to change them. Free text only.
    3. Return the same MatchResult with explanation filled in.
    """
    result = compute_match(resume, jd, skill_verdicts)

    explanation = generate_explanation(
        overall_score=result.overall_score,
        score_breakdown={name: cat.status for name, cat in result.score_breakdown.items()},
        matched_requirements=result.matched_requirements,
        missing_requirements=result.missing_requirements,
        unknown_requirements=result.unknown_requirements,
        strengths=result.strengths,
        weaknesses=result.weaknesses,
    )

    result.explanation = explanation
    return result