import ChipRow from './ChipRow'

function Field({ label, children }) {
  return (
    <div className="border-b border-hair py-3 last:border-b-0">
      <div className="mb-1 text-[10.5px] uppercase tracking-wide text-stone">{label}</div>
      <div className="text-[12.5px] leading-relaxed">{children}</div>
    </div>
  )
}

function ConstraintLine({ c }) {
  return (
    <div className="mb-2">
      <div className="font-medium">{c.description}</div>
      <div className="text-stone">
        {c.type}{c.value ? ` · ${c.value}` : ''} · {c.is_must_have ? 'must-have' : 'preferred'}
      </div>
    </div>
  )
}

export default function JDProfileDetail({ profile }) {
  if (!profile) {
    return <span className="text-[#B4AF9F]">No JD profile returned.</span>
  }

  return (
    <div className="grid grid-cols-1 gap-x-8 md:grid-cols-3">

      {/* ── Column 1 ── */}
      <div>
        <Field label="Summary">
          {profile.summary || <span className="text-[11px] text-[#B4AF9F]">none</span>}
        </Field>
        <Field label="Required skills">
          <ChipRow items={profile.required_skills} />
        </Field>
        <Field label="Preferred skills">
          <ChipRow items={profile.preferred_skills} />
        </Field>
      </div>

      {/* ── Column 2 ── */}
      <div>
        <Field label="Experience required">
          {profile.required_experience_months != null
            ? `${profile.required_experience_months} months`
            : 'not specified'}
        </Field>
        <Field label="Education requirements">
          <ChipRow items={profile.education_requirements} />
        </Field>
        <Field label="Career level expected">
          {profile.career_level_expected || 'not specified'}
        </Field>
        <Field label="Domains">
          <ChipRow items={profile.domains} />
        </Field>
        <Field label="Certifications">
          <ChipRow items={profile.certifications} />
        </Field>
      </div>

      {/* ── Column 3 ── */}
      <div>
        <Field label="Responsibilities">
          {profile.responsibilities?.length ? (
            <ul className="m-0 list-inside list-disc p-0">
              {profile.responsibilities.map((r, i) => (
                <li key={i} className="mb-1">{r}</li>
              ))}
            </ul>
          ) : (
            <span className="text-[11px] text-[#B4AF9F]">none listed</span>
          )}
        </Field>
        <Field label="Must-have constraints">
          {profile.must_have_constraints?.length ? (
            profile.must_have_constraints.map((c, i) => <ConstraintLine key={i} c={c} />)
          ) : (
            <span className="text-[11px] text-[#B4AF9F]">none listed</span>
          )}
        </Field>
        <Field label="Preferred constraints">
          {profile.preferred_constraints?.length ? (
            profile.preferred_constraints.map((c, i) => <ConstraintLine key={i} c={c} />)
          ) : (
            <span className="text-[11px] text-[#B4AF9F]">none listed</span>
          )}
        </Field>
      </div>

    </div>
  )
}
