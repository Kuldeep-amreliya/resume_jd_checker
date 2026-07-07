export default function SemanticMatches({ matches }) {
  if (!matches || matches.length === 0) return null

  return (
    <div className="flex flex-col gap-px border border-hair-strong bg-hair-strong">
      {matches.map((m, i) => {
        const simText =
          m.similarity_score !== null && m.similarity_score !== undefined
            ? ` · ${(m.similarity_score * 100).toFixed(0)}%`
            : ''
        return (
          <div
            key={i}
            className="grid grid-cols-1 items-center gap-3 bg-paper-raised p-3 px-4 text-[12.5px] md:grid-cols-[1fr_auto_1fr_auto]"
          >
            <span className="font-medium">{m.resume_term}</span>
            <span className="text-stone">→</span>
            <span className="font-medium">{m.jd_term}</span>
            <span className="text-[10px] uppercase tracking-wide text-stone md:justify-self-end">
              {m.similarity_basis}
              {simText}
            </span>
          </div>
        )
      })}
    </div>
  )
}
