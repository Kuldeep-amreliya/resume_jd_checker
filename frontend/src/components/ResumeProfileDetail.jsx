import ChipRow from './ChipRow'

function Field({ label, children }) {
  return (
    <div className="border-b border-hair py-3 last:border-b-0">
      <div className="mb-1 text-[10.5px] uppercase tracking-wide text-stone">{label}</div>
      <div className="text-[12.5px] leading-relaxed">{children}</div>
    </div>
  )
}

export default function ResumeProfileDetail({ profile }) {
  if (!profile) {
    return <span className="text-[#B4AF9F]">No resume profile returned.</span>
  }

  const exp = profile.experience || []
  const edu = profile.education || []
  const proj = profile.projects || []

  return (
    <div className="grid grid-cols-1 gap-x-8 md:grid-cols-3">

      {/* ── Column 1 ── */}
      <div>
        <Field label="Summary">
          {profile.summary || <span className="text-[11px] text-[#B4AF9F]">none</span>}
        </Field>
        <Field label="Career level">
          {profile.career_level || 'unknown'}
          {profile.total_experience_months != null
            ? ` · ${profile.total_experience_months} months`
            : ' · experience unspecified'}
        </Field>
        <Field label="Technical skills">
          <ChipRow items={profile.technical_skills} />
        </Field>
        <Field label="Frameworks">
          <ChipRow items={profile.frameworks} />
        </Field>
      </div>

      {/* ── Column 2 ── */}
      <div>
        <Field label="Tools">
          <ChipRow items={profile.tools} />
        </Field>
        <Field label="Cloud">
          <ChipRow items={profile.cloud} />
        </Field>
        <Field label="Soft skills">
          <ChipRow items={profile.soft_skills} />
        </Field>
        <Field label="Certifications">
          <ChipRow items={profile.certifications} />
        </Field>
        <Field label="Domains">
          <ChipRow items={profile.domains} />
        </Field>
      </div>

      {/* ── Column 3 ── */}
      <div>
        <Field label="Experience">
          {exp.length ? (
            exp.map((e, i) => (
              <div key={i} className="mb-2">
                <div className="font-medium">{e.title || '—'}{e.company ? ` · ${e.company}` : ''}</div>
                <div className="text-stone">{e.duration_months != null ? `${e.duration_months} months` : 'duration unspecified'}</div>
              </div>
            ))
          ) : (
            <span className="text-[11px] text-[#B4AF9F]">none listed</span>
          )}
        </Field>
        <Field label="Education">
          {edu.length ? (
            edu.map((e, i) => (
              <div key={i} className="mb-2">
                <div className="font-medium">{e.degree || '—'}{e.field_of_study ? ` in ${e.field_of_study}` : ''}</div>
                <div className="text-stone">{e.institution || ''}{e.graduation_year ? ` · ${e.graduation_year}` : ''}</div>
              </div>
            ))
          ) : (
            <span className="text-[11px] text-[#B4AF9F]">none listed</span>
          )}
        </Field>
        <Field label="Projects">
          {proj.length ? (
            proj.map((p, i) => (
              <div key={i} className="mb-2">
                <div className="font-medium">{p.name || '—'}</div>
                <div className="text-stone">{(p.tech_used || []).join(', ')}</div>
              </div>
            ))
          ) : (
            <span className="text-[11px] text-[#B4AF9F]">none listed</span>
          )}
        </Field>
      </div>

    </div>
  )
}
