// Thin API client for the Resume-JD Matching backend.
//
// In dev, Vite's proxy (see vite.config.js) forwards /api/* to the FastAPI
// server at http://localhost:8000, so relative paths work with no CORS
// headaches. In production, either serve this build from the same FastAPI
// app (mount StaticFiles) so relative paths still work, or set
// VITE_API_BASE at build time to point at a different host.

const API_BASE = import.meta.env.VITE_API_BASE || ''

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/api/health`)
  if (!res.ok) throw new Error(`Health check failed (${res.status})`)
  return res.json()
}

export async function submitMatch({ resumeMode, resumeFile, resumeText, jdMode, jdFile, jdText }) {
  const fd = new FormData()
  if (resumeMode === 'file') {
    fd.append('resume_file', resumeFile)
  } else {
    fd.append('resume_text', resumeText)
  }
  if (jdMode === 'file') {
    fd.append('jd_file', jdFile)
  } else {
    fd.append('jd_text', jdText)
  }

  const res = await fetch(`${API_BASE}/api/match`, {
    method: 'POST',
    body: fd,
  })

  if (!res.ok) {
    let detail = `Request failed (${res.status}).`
    try {
      const errJson = await res.json()
      if (errJson && errJson.detail) detail = errJson.detail
    } catch (_e) {
      // ignore parse failure, use default message
    }
    throw new Error(detail)
  }

  return res.json()
}

export async function fetchMatch(matchId) {
  const res = await fetch(`${API_BASE}/api/match/${matchId}`)
  if (!res.ok) {
    let detail = `Request failed (${res.status}).`
    try {
      const errJson = await res.json()
      if (errJson && errJson.detail) detail = errJson.detail
    } catch (_e) {}
    throw new Error(detail)
  }
  return res.json()
}
