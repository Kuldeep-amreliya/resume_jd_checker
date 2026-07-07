"""
Cheap heuristic classifier distinguishing "resume-like" text from
"JD-like" text — used to auto-correct the common user mistake of
uploading/pasting a resume and JD into the wrong form fields.

Deliberately NOT an LLM call: this runs on every request before any
expensive extraction happens, so it needs to be near-zero-cost. It trades
some accuracy for speed/cost — see routes_match.py for how a wrong guess
is handled (silent swap, no hard block), which keeps the blast radius of
a misclassification low.
"""
import re

# Phrases/patterns weighted toward "this is a resume".
_RESUME_PATTERNS = [
    r"\bemail\s*:", r"\bphone\s*:", r"\blinkedin\b", r"\bgithub\b",
    r"\bwork experience\b", r"\bprofessional experience\b",
    r"\beducation\b", r"\bcertifications?\b", r"\bprojects?\b",
    r"\bcgpa\b", r"\bgpa\b", r"\btechnical skills\b", r"\bsoft skills\b",
    r"\blanguages\b", r"\bachievements\b", r"\bobjective\b",
    r"\bcareer summary\b", r"\bprofessional summary\b",
    # past-tense first-person-implied action verbs, common in resume bullets
    r"\bbuilt\b", r"\bdeveloped\b", r"\bimplemented\b", r"\boptimized\b",
    r"\bdesigned and\b", r"\bcollaborated with\b", r"\bcreated\b",
    r"\bled\b(?!\s+to)",  # "led" but not "led to" (avoid false hits in JD prose)
]

# Phrases/patterns weighted toward "this is a job description".
_JD_PATTERNS = [
    r"\bresponsibilit(y|ies)\b", r"\brequirements?\b", r"\bqualifications?\b",
    r"\bwe are looking for\b", r"\bthe candidate should\b", r"\bthe ideal candidate\b",
    r"\bjob summary\b", r"\bjob description\b", r"\bpreferred skills\b",
    r"\brequired skills\b", r"\bnice to have\b", r"\bmust have\b",
    r"\bminimum \d+ years?\b", r"\bexperience required\b", r"\byears? of experience\b",
    r"\bwe offer\b", r"\bbenefits\b", r"\bsalary\b", r"\bcompensation\b",
    r"\babout the role\b", r"\babout the company\b", r"\bwhat you('ll| will) do\b",
    # imperative/infinitive-style bullets common in JD responsibility lists
    r"\bdesign\b.{0,20}\busing\b", r"\bdevelop\b.{0,20}\barchitecture\b",
    r"\bcollaborate with\b", r"\bwrite clean\b", r"\bdeploy applications\b",
]


def _score(text: str, patterns: list[str]) -> int:
    lowered = text.lower()
    return sum(len(re.findall(p, lowered)) for p in patterns)


def classify_doc_type(text: str) -> tuple[str, int, int]:
    """
    Returns (guess, resume_score, jd_score) where guess is "resume" or "jd" —
    whichever scored higher. Ties default to "resume" (arbitrary but stable).
    """
    resume_score = _score(text, _RESUME_PATTERNS)
    jd_score = _score(text, _JD_PATTERNS)
    guess = "jd" if jd_score > resume_score else "resume"
    return guess, resume_score, jd_score


def detect_and_fix_swap(
    resume_text: str, jd_text: str
) -> tuple[str, str, bool]:
    """
    Given the text currently sitting in the resume slot and the JD slot,
    check whether they look swapped, and if so, swap them back.

    Returns (corrected_resume_text, corrected_jd_text, was_swapped).

    Heuristic: classify both texts independently. If the text in the
    "resume" slot looks more JD-like than the text in the "jd" slot (or
    equivalently, the "jd" slot looks more resume-like), swap them. This
    catches the common case (fields fully reversed) without needing every
    edge case to be perfectly classified — we only act when the mismatch
    is clear in both directions at once, to keep false-swap risk low.
    """
    resume_guess, resume_r_score, resume_j_score = classify_doc_type(resume_text)
    jd_guess, jd_r_score, jd_j_score = classify_doc_type(jd_text)

    looks_swapped = (
        resume_guess == "jd"
        and jd_guess == "resume"
        and resume_j_score > resume_r_score  # resume slot clearly more JD-like
        and jd_r_score > jd_j_score           # jd slot clearly more resume-like
    )

    if looks_swapped:
        return jd_text, resume_text, True

    return resume_text, jd_text, False