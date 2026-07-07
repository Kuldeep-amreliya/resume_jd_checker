# Resume–JD Matching Tool — Frontend

Vite + React + Tailwind frontend for the Resume–JD Matching backend (FastAPI).

## Setup

```bash
cd frontend
npm install
```

## Run in dev

```bash
npm run dev
```

Opens at `http://localhost:5173`. API calls to `/api/*` are proxied to
`http://localhost:8000` (your FastAPI backend) via `vite.config.js` — make
sure `uvicorn app.main:app --reload` is running there.

If your backend runs on a different port, edit the `target` in
`vite.config.js`, under `server.proxy['/api']`.

## Build for production

```bash
npm run build
```

Outputs static files to `dist/`. Two ways to serve them:

1. **Same-origin with FastAPI** (recommended — no CORS needed): copy
   `dist/` contents somewhere FastAPI can serve as static files, e.g.

   ```python
   from fastapi.staticfiles import StaticFiles

   # after app.include_router(match_router)
   app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")
   ```

2. **Separate static host**: serve `dist/` with any static file server, and
   set `VITE_API_BASE` (e.g. `VITE_API_BASE=http://localhost:8000`) as an
   environment variable at build time so requests go to the right host.
   Requires the backend's CORS to allow that origin (already wide open via
   `allow_origins=["*"]` in `main.py`).

## Structure

```
src/
  api.js                     API client (fetchHealth, submitMatch, fetchMatch)
  App.jsx                    Page layout & state
  index.css                  Tailwind directives + a couple of custom keyframes
  components/
    HealthBadge.jsx           /api/health status dot
    IntakePanel.jsx           Resume/JD file-or-paste input panel
    LoadingStages.jsx         Animated loading copy while /api/match runs
    ScoreDial.jsx             SVG semicircular score gauge
    CategoryBreakdown.jsx     score_breakdown grid
    RequirementColumns.jsx    matched / missing / unknown lists
    SemanticMatches.jsx       semantic_matches rows
    Triad.jsx                 strengths / weaknesses / recommendations
    ChipRow.jsx               small pill-list helper
    ResumeProfileDetail.jsx   resume_profile detail view
    JDProfileDetail.jsx       jd_profile detail view
    SectionTitle.jsx          section header with trailing rule
```
