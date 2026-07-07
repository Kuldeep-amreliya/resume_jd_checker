import { useRef, useState } from 'react'
import HealthBadge from './components/HealthBadge'
import IntakePanel from './components/IntakePanel'
import LoadingStages from './components/LoadingStages'
import ScoreDial from './components/ScoreDial'
import SectionTitle from './components/SectionTitle'
import CategoryBreakdown from './components/CategoryBreakdown'
import RequirementColumns from './components/RequirementColumns'
import SemanticMatches from './components/SemanticMatches'
import Triad from './components/Triad'
import ResumeProfileDetail from './components/ResumeProfileDetail'
import JDProfileDetail from './components/JDProfileDetail'
import { submitMatch } from './api'

function verdictHeadline(score) {
  if (score >= 85) return 'Strong fit'
  if (score >= 70) return 'Good fit, with gaps'
  if (score >= 50) return 'Partial fit'
  if (score >= 30) return 'Weak fit'
  return 'Poor fit'
}

export default function App() {
  const [resume, setResume] = useState({ mode: 'file', file: null, text: '' })
  const [jd, setJd] = useState({ mode: 'file', file: null, text: '' })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const verdictRef = useRef(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    if (resume.mode === 'file' && !resume.file) {
      setError('Add a resume file, or switch to "Paste text" and paste the resume.')
      return
    }
    if (resume.mode === 'text' && !resume.text?.trim()) {
      setError('Paste resume text, or switch to "File" and upload one.')
      return
    }
    if (jd.mode === 'file' && !jd.file) {
      setError('Add a job description file, or switch to "Paste text" and paste the JD.')
      return
    }
    if (jd.mode === 'text' && !jd.text?.trim()) {
      setError('Paste job description text, or switch to "File" and upload one.')
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const data = await submitMatch({
        resumeMode: resume.mode,
        resumeFile: resume.file,
        resumeText: resume.text,
        jdMode: jd.mode,
        jdFile: jd.file,
        jdText: jd.text,
      })
      setResult(data)
      // scroll to the verdict on the next paint
      requestAnimationFrame(() => {
        verdictRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    } catch (err) {
      setError(err.message || 'Something went wrong reaching the matching service.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto max-w-[1180px] px-7 pb-32">
      <header className="flex flex-wrap items-baseline justify-between gap-4 border-b border-hair-strong py-9 pb-5">
        <div className="flex items-baseline gap-3.5">
          <span className="font-display text-2xl font-bold tracking-tight">Fit Readout</span>
          <span className="text-xs uppercase tracking-wide text-stone">Resume ⟷ JD diagnostic</span>
        </div>
        <HealthBadge />
      </header>

      <form onSubmit={handleSubmit}>
        <div className="mt-7 grid grid-cols-1 gap-px border border-hair-strong bg-hair-strong md:grid-cols-2">
          <IntakePanel
            label="Resume"
            eyebrow="01 — Candidate resume"
            value={resume}
            onChange={setResume}
          />
          <IntakePanel
            label="Job Description"
            eyebrow="02 — Job description"
            value={jd}
            onChange={setJd}
          />
        </div>

        <div className="mt-5.5 flex flex-wrap items-center justify-between gap-4">
          <span className="text-xs text-stone">
            Provide one resume and one JD — either as a file or pasted text.
          </span>
          <button
            type="submit"
            disabled={loading}
            className="group inline-flex items-center gap-2.5 bg-ink px-7 py-4 font-mono text-[13px] uppercase tracking-wide text-paper transition-colors hover:enabled:bg-[#1e2b25] disabled:cursor-not-allowed disabled:bg-stone"
          >
            Run match{' '}
            <span className="inline-block transition-transform group-hover:enabled:translate-x-1">→</span>
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-[2px] border border-[#e0b6a4] bg-rust-dim px-3 py-2.5 text-[12.5px] text-rust">
            {error}
          </div>
        )}
      </form>

      {loading && <LoadingStages />}

      {result && (
        <div ref={verdictRef} className="mt-13">
          <div className="grid grid-cols-1 items-center gap-9 border-b border-hair-strong pb-8 text-center md:grid-cols-[220px_1fr] md:text-left">
            <ScoreDial score={result.overall_score} />
            <div>
              <div className="mb-2.5 text-[11px] uppercase tracking-wide text-stone">Match verdict</div>
              <h1 className="mb-3 font-display text-3xl font-semibold leading-tight">
                {verdictHeadline(result.overall_score)} — {result.overall_score}/100
              </h1>
              <div className="max-w-[64ch] text-[13.5px] leading-relaxed text-[#2b2c28]">
                {result.explanation}
              </div>
              <span className="mt-3.5 inline-block rounded-[2px] border border-hair-strong px-2 py-0.5 text-[11px] text-stone">
                match #{result.match_id}
              </span>
            </div>
          </div>

          <SectionTitle>Category breakdown</SectionTitle>
          <CategoryBreakdown breakdown={result.score_breakdown} />

          <SectionTitle>Requirements</SectionTitle>
          <RequirementColumns
            matched={result.matched_requirements}
            missing={result.missing_requirements}
            unknown={result.unknown_requirements}
          />

          {result.semantic_matches?.length > 0 && (
            <>
              <SectionTitle>Semantic matches</SectionTitle>
              <SemanticMatches matches={result.semantic_matches} />
            </>
          )}

          <SectionTitle>Assessment</SectionTitle>
          <Triad
            strengths={result.strengths}
            weaknesses={result.weaknesses}
            recommendations={result.recommendations}
          />

          <SectionTitle>Extracted profiles</SectionTitle>
          <details className="group mt-3 border border-hair-strong">
            <summary className="flex cursor-pointer items-center justify-between bg-paper-raised px-7 py-3.5 text-[12.5px] transition-colors hover:bg-[#F0EDE3] marker:content-none [&::-webkit-details-marker]:hidden">
              <span>Resume profile — parsed fields</span>
              <svg
                className="h-3.5 w-3.5 flex-shrink-0 text-stone transition-transform duration-200 group-open:rotate-180"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </summary>
            <div className="border-t border-hair bg-paper-raised px-7 pb-5 pt-3">
              <ResumeProfileDetail profile={result.resume_profile} />
            </div>
          </details>
          <details className="group mt-3 border border-hair-strong">
            <summary className="flex cursor-pointer items-center justify-between bg-paper-raised px-7 py-3.5 text-[12.5px] transition-colors hover:bg-[#F0EDE3] marker:content-none [&::-webkit-details-marker]:hidden">
              <span>JD profile — parsed fields</span>
              <svg
                className="h-3.5 w-3.5 flex-shrink-0 text-stone transition-transform duration-200 group-open:rotate-180"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="6 9 12 15 18 9" />
              </svg>
            </summary>
            <div className="border-t border-hair bg-paper-raised px-7 pb-5 pt-3">
              <JDProfileDetail profile={result.jd_profile} />
            </div>
          </details>
        </div>
      )}

      <footer className="mt-16 flex flex-wrap justify-between gap-2 border-t border-hair-strong pt-5 text-[11px] text-stone">
        <span>Resume–JD Matching Tool · E2M take-home</span>
        <span>{import.meta.env.VITE_API_BASE || 'same-origin (proxy in dev)'}</span>
      </footer>
    </div>
  )
}
