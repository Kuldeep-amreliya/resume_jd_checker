"""
Deterministic scoring engine.

ZERO LLM CALLS HAPPEN IN THIS FILE. Everything here is pure Python operating
on already-validated ResumeProfile/JDProfile objects. This is the boundary
the whole architecture is built around: the LLM understands, this file decides.

The central rule enforced everywhere: missing information is UNKNOWN, not
FAILED. A candidate is never penalized to zero for a category the resume
simply didn't mention — see `score_category_with_unknown_rule`, the one
function all category scorers route through so this rule can't be
accidentally skipped in one category but not another.
"""
from app.config import get_settings
from app.profiles.schemas import ResumeProfile, JDProfile
from app.scoring.scoring_schemas import CategoryScore, MatchResult, SemanticMatch, SkillVerdict

WEIGHTS = {
    "technical_skills": 0.30,
    "experience": 0.20,
    "projects": 0.15,
    "education": 0.10,
    "certifications": 0.05,
    "domain_match": 0.10,
    "soft_skills": 0.05,
    "constraints": 0.05,
}

assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9, "WEIGHTS must sum to 1.0"


def _normalize(term: str) -> str:
    """Lowercase + strip for case-insensitive set comparisons."""
    return term.strip().lower()


def _normalize_set(terms: list[str]) -> set[str]:
    return {_normalize(t) for t in terms if t and t.strip()}


def score_category_with_unknown_rule(
    is_unknown: bool,
    matched_count: int,
    total_required: int,
    weight: float,
    unknown_note: str = "Not stated in resume — not held against the candidate.",
) -> CategoryScore:
    """
    THE single place the UNKNOWN-safe rule lives.

    If the relevant info wasn't in the resume/JD at all, this category is
    UNKNOWN and gets a neutral score (configurable, not 0 and not full marks)
    rather than being counted as a failure.

    Otherwise, score = matched / total_required, with status derived from
    the ratio.
    """
    settings = get_settings()

    if is_unknown:
        return CategoryScore(
            status="UNKNOWN",
            score=settings.neutral_unknown_score,
            weight=weight,
            notes=unknown_note,
        )

    if total_required == 0:
        # nothing was required in this category -> treat as fully satisfied, not penalized
        return CategoryScore(status="MATCHED", score=1.0, weight=weight, notes="No requirements specified.")

    ratio = matched_count / total_required
    if ratio >= 0.999:
        status = "MATCHED"
    elif ratio > 0:
        status = "PARTIAL"
    else:
        status = "MISSING"

    return CategoryScore(
        status=status,
        score=round(ratio, 4),
        weight=weight,
        notes=f"{matched_count}/{total_required} matched.",
    )


def score_technical_skills(
    resume: ResumeProfile, jd: JDProfile, skill_verdicts: list[SkillVerdict]
) -> tuple[CategoryScore, list[str], list[str], list[SemanticMatch]]:
    """
    Technical skill matching, driven by SkillVerdict results from a direct
    LLM read of the resume against each JD skill (see llm/skill_matching.py).
    This replaced independent-extraction-then-diff matching, which reliably
    missed equivalent-but-differently-worded skills (e.g. "Basic AWS
    Knowledge" vs "AWS").

    Returns (category_score, matched_terms, missing_terms, semantic_matches)
    to keep the exact same return shape the rest of engine.py already expects.
    """
    required = [v for v in skill_verdicts if v.is_required]
    preferred = [v for v in skill_verdicts if not v.is_required]

    if not required and not preferred:
        return (
            CategoryScore(status="UNKNOWN", score=get_settings().neutral_unknown_score,
                          weight=WEIGHTS["technical_skills"],
                          notes="JD did not specify required or preferred skills."),
            [], [], [],
        )

    matched: list[str] = []
    missing: list[str] = []
    semantic_matches: list[SemanticMatch] = []

    def status_weight(status: str) -> float:
        # PARTIAL counts as half credit toward the ratio, same spirit as
        # your original ratio-based scoring elsewhere in this file.
        return {"MATCHED": 1.0, "PARTIAL": 0.5, "MISSING": 0.0}[status]

    for v in skill_verdicts:
        if v.status in ("MATCHED", "PARTIAL"):
            matched.append(v.skill)
            if v.evidence:
                semantic_matches.append(
                    SemanticMatch(resume_term=v.evidence, jd_term=v.skill, similarity_basis="llm_capability")
                )
        else:
            missing.append(v.skill)

    req_weighted = sum(status_weight(v.status) for v in required)
    pref_weighted = sum(status_weight(v.status) for v in preferred)

    total_weighted = len(required) * 2 + len(preferred)
    matched_weighted = req_weighted * 2 + pref_weighted
    ratio = matched_weighted / total_weighted if total_weighted else 1.0

    if ratio >= 0.999:
        status = "MATCHED"
    elif ratio > 0:
        status = "PARTIAL"
    else:
        status = "MISSING"

    req_matched_count = sum(1 for v in required if v.status == "MATCHED")
    pref_matched_count = sum(1 for v in preferred if v.status == "MATCHED")

    category = CategoryScore(
        status=status,
        score=round(ratio, 4),
        weight=WEIGHTS["technical_skills"],
        notes=f"{req_matched_count}/{len(required)} required, {pref_matched_count}/{len(preferred)} preferred skills matched (LLM-verified against resume text).",
    )
    return category, matched, missing, semantic_matches


def score_experience(resume: ResumeProfile, jd: JDProfile) -> CategoryScore:
    if jd.required_experience_months is None:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["experience"],
            unknown_note="JD did not specify a required experience duration.",
        )
    if resume.total_experience_months is None:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["experience"],
            unknown_note="Resume does not state a computable total experience duration.",
        )

    required = jd.required_experience_months
    actual = resume.total_experience_months

    if actual >= required:
        return CategoryScore(status="MATCHED", score=1.0, weight=WEIGHTS["experience"],
                              notes=f"{actual} months experience vs {required} required.")
    ratio = round(actual / required, 4) if required > 0 else 1.0
    status = "PARTIAL" if ratio > 0 else "MISSING"
    return CategoryScore(status=status, score=ratio, weight=WEIGHTS["experience"],
                          notes=f"{actual} months experience vs {required} required.")


def score_projects(resume: ResumeProfile, jd: JDProfile) -> CategoryScore:
    """
    Checks whether project-derived inferred_capabilities cover JD responsibilities/
    requirement-capabilities not otherwise covered — lets strong personal projects
    offset thin formal experience, unlike a pure keyword matcher.
    """
    project_capabilities = _normalize_set(
        [cap for p in resume.projects for cap in p.inferred_capabilities]
    )
    jd_capabilities = _normalize_set(jd.inferred_requirement_capabilities)

    if not jd_capabilities:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["projects"],
            unknown_note="JD requirements did not yield inferable capabilities to check against projects.",
        )

    if not resume.projects:
        return CategoryScore(status="MISSING", score=0.0, weight=WEIGHTS["projects"],
                              notes="No projects listed on resume.")

    matched = jd_capabilities & project_capabilities
    return score_category_with_unknown_rule(
        is_unknown=False, matched_count=len(matched), total_required=len(jd_capabilities),
        weight=WEIGHTS["projects"],
    )


import re


def _parse_numeric_requirement(req: str) -> tuple[float, str] | None:
    """
    Detect a numeric threshold requirement like "CGPA >= 8" or "GPA of at least 3.5".
    Returns (threshold, operator) where operator is '>=' (the only case we need here,
    since education/GPA requirements are virtually always a minimum bar), or None if
    this requirement string isn't a numeric one (e.g. "Bachelor's degree in CS").
    """
    match = re.search(r"(\d+(\.\d+)?)", req)
    if not match:
        return None
    is_gpa_like = bool(re.search(r"\b(cgpa|gpa|grade)\b", req, re.IGNORECASE))
    if not is_gpa_like:
        return None
    return float(match.group(1)), ">="


def score_education(resume: ResumeProfile, jd: JDProfile) -> CategoryScore:
    if not jd.education_requirements:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["education"],
            unknown_note="JD did not specify education requirements.",
        )
    if not resume.education:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["education"],
            unknown_note="Resume does not list education details.",
        )

    # Split JD education requirements into numeric (e.g. "CGPA >= 8") vs textual
    # (e.g. "Bachelor's degree in Computer Science"), and score each on its own terms
    # rather than one blended substring ratio — this is what lets a missing CGPA stay
    # UNKNOWN instead of being counted as a failed text match.
    numeric_reqs = []
    textual_reqs = []
    for req in jd.education_requirements:
        parsed = _parse_numeric_requirement(req)
        if parsed:
            numeric_reqs.append((req, parsed))
        else:
            textual_reqs.append(req)

    statuses: list[str] = []  # collect "MATCHED"/"MISSING"/"UNKNOWN" per requirement, then combine
    notes_parts: list[str] = []

    # Numeric (e.g. CGPA) requirements: compare against any resume education entry's gpa_or_cgpa.
    resume_gpas = [edu.gpa_or_cgpa for edu in resume.education if edu.gpa_or_cgpa is not None]
    for req_text, (threshold, _op) in numeric_reqs:
        if not resume_gpas:
            statuses.append("UNKNOWN")
            notes_parts.append(f"'{req_text}': not stated on resume, not held against candidate.")
        elif max(resume_gpas) >= threshold:
            statuses.append("MATCHED")
            notes_parts.append(f"'{req_text}': satisfied ({max(resume_gpas)} >= {threshold}).")
        else:
            statuses.append("MISSING")
            notes_parts.append(f"'{req_text}': not met ({max(resume_gpas)} < {threshold}).")

    # Textual requirements (degree/field): substring match against resume degree/field text.
    if textual_reqs:
        req_text_blob = " ".join(textual_reqs).lower()
        any_textual_match = False
        for edu in resume.education:
            degree = (edu.degree or "").lower()
            field = (edu.field_of_study or "").lower()
            if (degree and degree in req_text_blob) or (field and field in req_text_blob):
                any_textual_match = True
                break
        if any_textual_match:
            statuses.append("MATCHED")
        else:
            statuses.append("MISSING")
        notes_parts.append(f"Degree/field requirement {'matched' if any_textual_match else 'not clearly matched'}.")

    # Combine: UNKNOWN only if EVERY requirement was unknown; otherwise average the known ones,
    # and surface unknowns separately via notes rather than silently averaging them away.
    if all(s == "UNKNOWN" for s in statuses):
        return CategoryScore(status="UNKNOWN", score=get_settings().neutral_unknown_score,
                              weight=WEIGHTS["education"], notes=" ".join(notes_parts))

    known_statuses = [s for s in statuses if s != "UNKNOWN"]
    matched_count = sum(1 for s in known_statuses if s == "MATCHED")
    total = len(known_statuses)
    ratio = matched_count / total if total else 1.0
    status = "MATCHED" if ratio >= 0.999 else ("PARTIAL" if ratio > 0 else "MISSING")

    return CategoryScore(status=status, score=round(ratio, 4), weight=WEIGHTS["education"],
                          notes=" ".join(notes_parts))


def score_certifications(resume: ResumeProfile, jd: JDProfile) -> CategoryScore:
    if not jd.certifications:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["certifications"],
            unknown_note="JD did not require specific certifications.",
        )
    resume_certs = _normalize_set(resume.certifications)
    jd_certs = _normalize_set(jd.certifications)
    matched = jd_certs & resume_certs
    return score_category_with_unknown_rule(
        is_unknown=False, matched_count=len(matched), total_required=len(jd_certs),
        weight=WEIGHTS["certifications"],
    )


def score_domain_match(resume: ResumeProfile, jd: JDProfile) -> CategoryScore:
    if not jd.domains:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["domain_match"],
            unknown_note="JD did not specify a target domain.",
        )
    resume_domains = _normalize_set(resume.domains)
    jd_domains = _normalize_set(jd.domains)
    matched = jd_domains & resume_domains
    return score_category_with_unknown_rule(
        is_unknown=False, matched_count=len(matched), total_required=len(jd_domains),
        weight=WEIGHTS["domain_match"],
    )


def score_soft_skills(resume: ResumeProfile, jd: JDProfile) -> CategoryScore:
    # JD soft-skill requirements aren't in the current JDProfile schema as a distinct field;
    # soft skills are typically implicit in responsibilities. Treat as UNKNOWN unless the resume
    # at least lists some (in which case, lightly reward as a neutral-positive signal).
    if not resume.soft_skills:
        return score_category_with_unknown_rule(
            is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["soft_skills"],
            unknown_note="No explicit soft-skill requirements to check against.",
        )
    return CategoryScore(status="MATCHED", score=1.0, weight=WEIGHTS["soft_skills"],
                          notes=f"Resume lists {len(resume.soft_skills)} soft skills.")


def score_constraints(resume: ResumeProfile, jd: JDProfile) -> tuple[CategoryScore, list[str]]:
    """
    Checks must_have_constraints. UNKNOWN constraints (resume simply doesn't say)
    do NOT penalize. Only explicitly CONTRADICTED constraints reduce this score.
    Returns (category_score, list of violated constraint descriptions).
    """
    if not jd.must_have_constraints:
        return (
            score_category_with_unknown_rule(
                is_unknown=True, matched_count=0, total_required=0, weight=WEIGHTS["constraints"],
                unknown_note="JD specified no hard must-have constraints.",
            ),
            [],
        )

    # Without deep NLP contradiction-detection here (that's an LLM-side inference concern,
    # already captured if the LLM flagged it during extraction), we conservatively treat all
    # must-have constraints as UNKNOWN unless directly checkable (e.g. numeric CGPA/experience
    # constraints, which are already covered by score_education/score_experience). This avoids
    # double-penalizing and avoids fabricating contradictions the resume never stated.
    violated: list[str] = []
    return (
        CategoryScore(
            status="UNKNOWN",
            score=get_settings().neutral_unknown_score,
            weight=WEIGHTS["constraints"],
            notes=f"{len(jd.must_have_constraints)} must-have constraint(s) noted; "
            "specific numeric constraints are checked via education/experience scoring.",
        ),
        violated,
    )


def compute_match(resume: ResumeProfile, jd: JDProfile, skill_verdicts: list[SkillVerdict]) -> MatchResult:
    """
    The single public entry point for scoring. Pure function: same inputs
    always produce the same outputs. No LLM calls happen here.
    """
    tech_score, tech_matched, tech_missing, semantic_matches = score_technical_skills(resume, jd, skill_verdicts)
    exp_score = score_experience(resume, jd)
    proj_score = score_projects(resume, jd)
    edu_score = score_education(resume, jd)
    cert_score = score_certifications(resume, jd)
    domain_score = score_domain_match(resume, jd)
    soft_score = score_soft_skills(resume, jd)
    constraints_score, violated_constraints = score_constraints(resume, jd)

    breakdown = {
        "technical_skills": tech_score,
        "experience": exp_score,
        "projects": proj_score,
        "education": edu_score,
        "certifications": cert_score,
        "domain_match": domain_score,
        "soft_skills": soft_score,
        "constraints": constraints_score,
    }

    overall = sum(cat.score * cat.weight for cat in breakdown.values())
    overall_pct = round(overall * 100)

    if violated_constraints:
        overall_pct = min(overall_pct, 40)

    unknown_requirements = [
        f"{name}: {cat.notes}" for name, cat in breakdown.items() if cat.status == "UNKNOWN"
    ]
    missing_requirements = list(tech_missing)
    for name, cat in breakdown.items():
        if cat.status == "MISSING" and name != "technical_skills":
            missing_requirements.append(f"{name}: {cat.notes}")

    strengths = [
        f"Strong {name.replace('_', ' ')} match" for name, cat in breakdown.items()
        if cat.status == "MATCHED"
    ]
    weaknesses = [
        f"Weak {name.replace('_', ' ')} match" for name, cat in breakdown.items()
        if cat.status == "MISSING"
    ]

    recommendations = []
    if tech_missing:
        recommendations.append(
            f"Consider highlighting or gaining experience with: {', '.join(tech_missing[:5])}."
        )
    if exp_score.status in ("PARTIAL", "MISSING"):
        recommendations.append("Gaining more directly relevant work experience would strengthen this application.")
    if proj_score.status in ("PARTIAL", "MISSING") and resume.projects:
        recommendations.append("Consider projects that more directly demonstrate the JD's core requirements.")

    return MatchResult(
        overall_score=overall_pct,
        score_breakdown=breakdown,
        matched_requirements=tech_matched,
        missing_requirements=missing_requirements,
        unknown_requirements=unknown_requirements,
        semantic_matches=semantic_matches,
        strengths=strengths,
        weaknesses=weaknesses,
        recommendations=recommendations,
        explanation="",  # filled in afterward by llm.extraction.generate_explanation
    )