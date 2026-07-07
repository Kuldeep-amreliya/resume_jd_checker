import ChipRow from './ChipRow'

export default function ResumeProfileDetail({ profile }) {
  if (!profile) {
    return <span className="text-[#B4AF9F]">No resume profile returned.</span>
  }

  const exp = profile.experience || []
  const edu = profile.education || []
  const proj = profile.projects || []

  return (
    <div className="grid grid-cols-1 gap-4.5 md:grid-cols-2">
      <div>
        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Summary</h4>
        <div className="text-[12.5px] leading-relaxed">
          {profile.summary || <span className="text-[11px] text-[#B4AF9F]">none</span>}
        </div>

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Career level</h4>
        <div className="text-[12.5px]">
          {profile.career_level || 'unknown'}
          {profile.total_experience_months != null
            ? ` · ${profile.total_experience_months} months experience`
            : ' · experience unspecified'}
        </div>

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Technical skills</h4>
        <ChipRow items={profile.technical_skills} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Frameworks</h4>
        <ChipRow items={profile.frameworks} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Tools</h4>
        <ChipRow items={profile.tools} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Cloud</h4>
        <ChipRow items={profile.cloud} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Soft skills</h4>
        <ChipRow items={profile.soft_skills} />
      </div>

      <div>
        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Experience</h4>
        {exp.length ? (
          exp.map((e, i) => (
            <div key={i} className="border-b border-hair py-1.5 text-xs last:border-b-0">
              <div className="font-medium">
                {e.title || '—'}
                {e.company ? ` · ${e.company}` : ''}
              </div>
              <div className="text-stone">
                {e.duration_months != null ? `${e.duration_months} months` : 'duration unspecified'}
              </div>
            </div>
          ))
        ) : (
          <span className="text-[11px] text-[#B4AF9F]">none listed</span>
        )}

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Education</h4>
        {edu.length ? (
          edu.map((e, i) => (
            <div key={i} className="border-b border-hair py-1.5 text-xs last:border-b-0">
              <div className="font-medium">
                {e.degree || '—'}
                {e.field_of_study ? ` in ${e.field_of_study}` : ''}
              </div>
              <div className="text-stone">
                {e.institution || ''}
                {e.graduation_year ? ` · ${e.graduation_year}` : ''}
              </div>
            </div>
          ))
        ) : (
          <span className="text-[11px] text-[#B4AF9F]">none listed</span>
        )}

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Projects</h4>
        {proj.length ? (
          proj.map((p, i) => (
            <div key={i} className="border-b border-hair py-1.5 text-xs last:border-b-0">
              <div className="font-medium">{p.name || '—'}</div>
              <div className="text-stone">{(p.tech_used || []).join(', ')}</div>
            </div>
          ))
        ) : (
          <span className="text-[11px] text-[#B4AF9F]">none listed</span>
        )}

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Certifications</h4>
        <ChipRow items={profile.certifications} />

        <h4 className="mt-3.5 mb-1.5 text-[10.5px] uppercase tracking-wide text-stone">Domains</h4>
        <ChipRow items={profile.domains} />
      </div>
    </div>
  )
}
