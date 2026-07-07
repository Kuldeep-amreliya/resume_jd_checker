import ChipRow from './ChipRow'

function ConstraintLine({ c }) {
  return (
    <div className="border-b border-hair py-1.5 text-xs last:border-b-0">
      <div className="font-medium">{c.description}</div>
      <div className="text-stone">
        {c.type}
        {c.value ? ` · ${c.value}` : ''} · {c.is_must_have ? 'must-have' : 'preferred'}
      </div>
    </div>
  )
}

export default function JDProfileDetail({ profile }) {
  if (!profile) {
    return <span className="text-[#B4AF9F]">No JD profile returned.</span>
  }

  return (
    <div className="grid grid-cols-1 gap-4.5 md:grid-cols-2">
      <div>
        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Summary</h4>
        <div className="text-[12.5px] leading-relaxed">
          {profile.summary || <span className="text-[11px] text-[#B4AF9F]">none</span>}
        </div>

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Required skills</h4>
        <ChipRow items={profile.required_skills} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Preferred skills</h4>
        <ChipRow items={profile.preferred_skills} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Experience required</h4>
        <div className="text-[12.5px]">
          {profile.required_experience_months != null
            ? `${profile.required_experience_months} months`
            : 'not specified'}
        </div>

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">
          Education requirements
        </h4>
        <ChipRow items={profile.education_requirements} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">
          Career level expected
        </h4>
        <div className="text-[12.5px]">{profile.career_level_expected || 'not specified'}</div>
      </div>

      <div>
        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Responsibilities</h4>
        {profile.responsibilities?.length ? (
          <ul className="m-0 list-disc pl-4">
            {profile.responsibilities.map((r, i) => (
              <li key={i} className="mb-1 text-[12.5px]">
                {r}
              </li>
            ))}
          </ul>
        ) : (
          <span className="text-[11px] text-[#B4AF9F]">none listed</span>
        )}

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">
          Must-have constraints
        </h4>
        {profile.must_have_constraints?.length ? (
          profile.must_have_constraints.map((c, i) => <ConstraintLine key={i} c={c} />)
        ) : (
          <span className="text-[11px] text-[#B4AF9F]">none listed</span>
        )}

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">
          Preferred constraints
        </h4>
        {profile.preferred_constraints?.length ? (
          profile.preferred_constraints.map((c, i) => <ConstraintLine key={i} c={c} />)
        ) : (
          <span className="text-[11px] text-[#B4AF9F]">none listed</span>
        )}

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Domains</h4>
        <ChipRow items={profile.domains} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Certifications</h4>
        <ChipRow items={profile.certifications} />
      </div>
    </div>
  )
}
