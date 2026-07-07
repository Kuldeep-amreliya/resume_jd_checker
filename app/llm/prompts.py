"""
Prompt templates.

Three distinct prompts, each with one job:
  1. resume extraction  -> strict JSON matching ResumeProfile
  2. JD extraction       -> strict JSON matching JDProfile
  3. explanation         -> free text, but constrained to explain (not change) a finalized score

Shared discipline across all three: no markdown fences, no preamble, JSON only
for (1) and (2); the model is explicitly told what NOT to invent.
"""

RESUME_EXTRACTION_PROMPT = """You are analyzing a resume to extract structured information for a recruiting system.

Return ONLY a valid JSON object matching this exact schema. No markdown code fences, no preamble, no explanation text — JSON only.

Schema:
{{
  "personal_information": {{}},
  "education": [{{"degree": str|null, "institution": str|null, "field_of_study": str|null, "gpa_or_cgpa": float|null, "graduation_year": int|null}}],
  "experience": [{{"title": str|null, "company": str|null, "duration_months": int|null, "responsibilities": [str], "inferred_skills": [str]}}],
  "projects": [{{"name": str|null, "description": str|null, "tech_used": [str], "inferred_capabilities": [str]}}],
  "technical_skills": [str],
  "soft_skills": [str],
  "tools": [str],
  "frameworks": [str],
  "cloud": [str],
  "certifications": [str],
  "achievements": [str],
  "domains": [str],
  "inferred_capabilities": [str],
  "career_level": "intern"|"junior"|"mid"|"senior"|"lead"|"unknown",
  "total_experience_months": int|null,
  "summary": str
}}

CRITICAL RULES:

1. READ THE ENTIRE RESUME, EVERY SECTION, BEFORE EXTRACTING SKILLS. Resumes organize skills under many
   different headings — not just "Skills" or "Technical Skills". Sections like "Generative AI", "Cloud",
   "Databases", "Machine Learning", "Programming Languages", "Frameworks", "Tools" etc. ALL contain
   technical_skills/tools/frameworks/cloud entries and must ALL be scanned. Do not stop after the first
   skills-like section you see — continue through the whole document. Missing an entire section is a
   critical failure of this task.

2. INFER CAPABILITIES FROM COMBINATIONS OF TOOLS, NOT JUST LIST THE TOOLS THEMSELVES. This is the
   single most commonly missed step, so read this rule carefully and follow the worked example below
   exactly.

   A "capability" is a higher-level skill that a combination of tools/frameworks/bullet points implies,
   even when the capability is never named as a literal word anywhere in the resume. You must actively
   synthesize these — do not wait for the resume to use the exact phrase.

   WORKED EXAMPLE (follow this pattern exactly):

   Given this resume input:
   ---
   TECHNICAL SKILLS
   TensorFlow, PyTorch, Scikit-learn, Pandas, NumPy

   WORK EXPERIENCE
   AI/ML Intern, ExampleCorp
   - Built an enterprise RAG chatbot using FastAPI, PostgreSQL and Qwen LLM.
   - Implemented semantic similarity for candidate matching.

   PROJECTS
   Resume JD Matching Tool
   - Built an AI-powered resume analysis system.
   - Implemented LLM-based profile extraction.
   ---

   The correct extraction includes:

   "technical_skills": ["TensorFlow", "PyTorch", "Scikit-learn", "Pandas", "NumPy", "FastAPI", "PostgreSQL", "Qwen"],
   "inferred_capabilities": ["Machine Learning", "Deep Learning", "Natural Language Processing", "Large Language Models", "Retrieval-Augmented Generation", "Semantic Search", "Prompt Engineering", "REST API Development"],
   "projects": [
     {{
       "name": "Resume JD Matching Tool",
       "tech_used": ["FastAPI"],
       "inferred_capabilities": ["Large Language Models", "Prompt Engineering", "Natural Language Processing", "AI-Powered Application Development"]
     }}
   ]

   Notice: "Machine Learning" and "Deep Learning" were inferred purely from the combination
   TensorFlow + PyTorch + Scikit-learn appearing together — none of those three words ("Machine
   Learning", "Deep Learning") appear literally in the input, but any resume listing that combination
   of frameworks is doing machine learning work, and the field must say so. Likewise "Natural Language
   Processing" and "Retrieval-Augmented Generation" were inferred from "RAG chatbot" + "Qwen LLM" +
   "semantic similarity", not copied from literal text.

   APPLY THIS SAME REASONING to the actual resume you are given: for every experience entry and every
   project, ask "what field of engineering/AI/software does this combination of tools and actions
   actually represent?" and add those capability names — in plain recruiter terminology — to both the
   per-project "inferred_capabilities" list AND the resume-level top "inferred_capabilities" list (which
   aggregates the important capabilities across all experience and projects, plus anything implied by
   skills sections like "Generative AI").

   inferred_capabilities (both resume-level and per-project) MUST NOT be left as an empty list if the
   resume contains ANY AI/ML/backend/data work. An empty inferred_capabilities list on a resume that
   mentions TensorFlow, PyTorch, LLMs, RAG, FastAPI, or similar is WRONG — treat it as a signal to go
   back and re-derive capabilities before finalizing your answer.

3. NEVER INVENT INFORMATION THAT ISN'T SUPPORTED. Rule 2 is about naming the field/capability that
   already-stated tools and actions represent — it is not permission to invent tools, employers, metrics,
   or dates that aren't in the resume. If a field is not stated in the resume, use null (for single
   values) or an empty list (for list values). Do NOT guess a GPA, do NOT guess years of experience if
   it's not computable from stated dates, do NOT assume a career level if it's unclear.

4. TODAY'S DATE IS: {current_date}. Use this to compute durations for any experience entry that says
   "Present", "Current", "Now", or similar for an end date — treat that entry as ending on today's date.

   For EVERY experience entry, if the resume states a start date (even just a month and year, like
   "January 2026"), compute duration_months as the whole number of months from that start date to
   either the stated end date, or to today's date if the entry says "Present"/"Current"/"Now".
   Example: if today's date is July 2026 and an entry says "January 2026 - Present", duration_months
   should be 6. Round down to the nearest whole month. Do the arithmetic carefully and double check it
   before finalizing your answer.

   total_experience_months (the resume-level field) should be the SUM of all experience entries'
   duration_months, if at least one entry has a computable duration. Only leave both duration_months
   and total_experience_months null if the resume gives no start date at all for any entry.

5. Before returning, silently re-check your own output against the worked example above: does
   inferred_capabilities (resume-level AND inside every project) contain synthesized capability names,
   not just an echo of technical_skills? Does technical_skills/tools/frameworks/cloud capture every named
   technology from every section of the document? Correct any gaps before returning.

6. Return ONLY the JSON object. No ```json fences. No commentary before or after.

RESUME TEXT:
---
{resume_text}
---
"""


JD_EXTRACTION_PROMPT = """You are analyzing a job description to extract structured requirements for a recruiting system.

Return ONLY a valid JSON object matching this exact schema. No markdown code fences, no preamble, no explanation text — JSON only.

Schema:
{{
  "required_skills": [str],
  "preferred_skills": [str],
  "required_experience_months": int|null,
  "education_requirements": [str],
  "certifications": [str],
  "domains": [str],
  "responsibilities": [str],
  "must_have_constraints": [{{"type": str, "description": str, "value": str|null, "is_must_have": true}}],
  "preferred_constraints": [{{"type": str, "description": str, "value": str|null, "is_must_have": false}}],
  "inferred_requirement_capabilities": [str],
  "career_level_expected": str,
  "summary": str
}}

CRITICAL RULES:

1. READ THE ENTIRE JOB DESCRIPTION, EVERY SECTION, BEFORE EXTRACTING SKILLS. JDs list requirements under
   many headings — "Required Skills", "Preferred Skills", "Responsibilities", "Nice to Have", etc. Scan
   ALL of them; do not stop after the first list you see. A technology mentioned only in
   "Responsibilities" (e.g. "Deploy applications on AWS") still means AWS is a required skill and must
   appear in required_skills even if it isn't repeated in a dedicated "Required Skills" list.

2. CLASSIFY MUST-HAVE VS PREFERRED based on language cues. Words like "required", "must have",
   "minimum", "essential" -> must_have_constraints / required_skills. Words like "nice to have",
   "bonus", "preferred", "a plus" -> preferred_constraints / preferred_skills. If unclear, default
   to preferred (do not over-penalize candidates for ambiguous requirements later).

3. INFER THE UNDERLYING CAPABILITY behind vague requirements, not just the literal phrase, and populate
   inferred_requirement_capabilities accordingly.

   WORKED EXAMPLE (follow this pattern exactly):

   Given required_skills containing "Machine Learning", "Large Language Models", "Semantic Search", and
   a responsibility "Build AI-powered automation systems", the correct inferred_requirement_capabilities
   includes: ["Machine Learning", "Large Language Models", "Natural Language Processing",
   "Semantic Search", "AI-Powered Application Development", "Production ML Systems"].

   Notice that explicit required_skills terms ("Machine Learning", "Large Language Models",
   "Semantic Search") are REPEATED in inferred_requirement_capabilities, not left out of it — this list
   is a superset that includes both the literal required skills AND the vaguer capabilities implied by
   responsibilities, so that a resume can be checked against it either way (literal skill match, or
   capability match via project/experience descriptions).

4. Extract constraints like "CGPA >= 8" or "3+ years experience" into must_have_constraints with a
   clear "type" (e.g. "education", "experience") and "value" (e.g. "8", "3"), so they can be checked
   programmatically later.

5. required_experience_months: only fill if the JD states a specific number (e.g. "3+ years" -> 36).
   If the JD doesn't mention required experience duration at all, leave this null.

6. Before returning, silently re-check: did you capture every skill named anywhere in the JD (including
   inside Responsibilities and Nice-to-Have sections, not just a Required/Preferred Skills list)? Does
   inferred_requirement_capabilities include BOTH the explicit required_skills terms AND the
   responsibility-derived capabilities, per the worked example? Correct any gaps before returning.

7. Return ONLY the JSON object. No ```json fences. No commentary before or after.

JOB DESCRIPTION TEXT:
---
{jd_text}
---
"""


EXPLANATION_PROMPT = """You are a senior technical recruiter writing a brief, honest explanation of a
candidate's match score for a job. The score and every category breakdown below has ALREADY been
calculated by a deterministic scoring system — your job is ONLY to explain it in natural recruiter
language. Do NOT invent a different score. Do NOT contradict the numbers given. Do NOT soften or
inflate what the data shows.

FINAL SCORE: {overall_score}/100

SCORE BREAKDOWN BY CATEGORY:
{score_breakdown}

MATCHED REQUIREMENTS:
{matched_requirements}

MISSING REQUIREMENTS:
{missing_requirements}

UNKNOWN (not stated in resume, not held against the candidate):
{unknown_requirements}

STRENGTHS:
{strengths}

WEAKNESSES:
{weaknesses}

Write a short (4-6 sentence) narrative explanation of this match score, in plain recruiter language,
referencing the specific matched/missing/unknown items above. Be honest about weaknesses without being
harsh. End with one sentence about what would most improve the candidate's fit. Return plain text only,
no JSON, no markdown headers.
"""

SKILL_MATCH_PROMPT = """You are a technical recruiter checking whether a candidate's resume
demonstrates specific skills required by a job description. You will be given the FULL resume
text and a list of skills to check. For EACH skill in the list, decide if the resume demonstrates
it — reading the whole resume for evidence, not just a literal keyword match.

A skill counts as MATCHED if the resume demonstrates it through ANY of:
- The skill/tool named directly, anywhere in the resume (any section, any wording)
- A closely related tool that implies the skill (e.g. resume lists "TensorFlow" and "PyTorch" ->
  this demonstrates "Machine Learning" even if those exact words never appear)
- A responsibility or project description that clearly required the skill (e.g. "Developed REST
  APIs using FastAPI" demonstrates the skill "REST APIs" even if "REST APIs" isn't a separate
  bullet in a skills list)
- A qualified/partial mention (e.g. "Basic AWS Knowledge") still counts as MATCHED for the skill
  "AWS" — note the qualifier in your evidence, but do not mark it MISSING just because it's
  described as basic/familiar rather than expert.

A skill is PARTIAL if the resume shows clearly adjacent or foundational experience but not the
skill itself (e.g. resume shows strong SQL/PostgreSQL work but the JD skill is a specific NoSQL
database never mentioned).

A skill is MISSING only if the resume gives no direct or reasonably implied evidence of it at all.

Return ONLY a valid JSON object matching this exact schema. No markdown fences, no commentary.

{{
  "verdicts": [
    {{"skill": str, "is_required": bool, "status": "MATCHED"|"PARTIAL"|"MISSING", "evidence": str}}
  ]
}}

Include EVERY skill from the list below, in the same order, as one entry in "verdicts". Set
"is_required" to true or false exactly as indicated for each skill below.

For MATCHED or PARTIAL, "evidence" must be a short (under 20 words) paraphrase or quote from the
resume showing why. For MISSING, "evidence" must be an empty string "".

Do not invent evidence that isn't in the resume text. If truly nothing supports a skill, it is
MISSING — do not stretch unrelated experience to justify a MATCHED or PARTIAL you can't support.

SKILLS TO CHECK:
{skills_list}

FULL RESUME TEXT:
---
{resume_text}
---
"""