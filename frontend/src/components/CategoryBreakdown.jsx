const TAG_STYLES = {
  MATCHED: 'bg-pine-dim text-pine',
  PARTIAL: 'bg-amber-dim text-[#96631a]',
  MISSING: 'bg-rust-dim text-rust',
  UNKNOWN: 'bg-stone-dim text-stone',
}

const METER_STYLES = {
  MATCHED: 'bg-pine',
  PARTIAL: 'bg-amber',
  MISSING: 'bg-rust',
  UNKNOWN: 'bg-stone',
}

export default function CategoryBreakdown({ breakdown }) {
  const entries = Object.entries(breakdown || {})

  if (entries.length === 0) {
    return (
      <div className="border border-hair-strong bg-paper-raised p-4">
        <span className="italic text-[#B4AF9F]">No category breakdown returned.</span>
      </div>
    )
  }

  return (
    <div
      className="grid gap-px border border-hair-strong bg-hair-strong"
      style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))' }}
    >
      {entries.map(([name, cat]) => {
        const pct = Math.round((cat.score || 0) * 100)
        const status = cat.status || 'UNKNOWN'
        return (
          <div key={name} className="bg-paper-raised p-4 pb-3.5">
            <div className="mb-2.5 flex items-center justify-between text-xs capitalize">
              <span>{name.replaceAll('_', ' ')}</span>
              <span
                className={`rounded-[2px] px-1.5 py-0.5 text-[9.5px] font-semibold uppercase tracking-wide ${
                  TAG_STYLES[status] || TAG_STYLES.UNKNOWN
                }`}
              >
                {status}
              </span>
            </div>
            <div className="mb-2 h-[5px] overflow-hidden rounded-[3px] bg-hair">
              <span
                className={`block h-full rounded-[3px] ${METER_STYLES[status] || METER_STYLES.UNKNOWN}`}
                style={{ width: `${pct}%` }}
              />
            </div>
            {cat.notes && <div className="text-[11.5px] leading-snug text-stone">{cat.notes}</div>}
            <div className="mt-2 text-[10px] text-[#B4AF9F]">
              weight {typeof cat.weight === 'number' ? cat.weight.toFixed(2) : cat.weight}
            </div>
          </div>
        )
      })}
    </div>
  )
}
