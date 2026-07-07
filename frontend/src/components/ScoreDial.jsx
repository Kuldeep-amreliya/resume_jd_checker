/**
 * Hand-instrument-style dial rendering the 0-100 overall_score as a
 * semicircular gauge with a needle, tick marks, and the score number
 * inside the arc.
 */
export default function ScoreDial({ score }) {
  const clamped = Math.max(0, Math.min(100, score ?? 0))
  const cx = 110
  const cy = 120
  const r = 90

  const arcColor = clamped >= 70 ? '#2B6E5C' : clamped >= 40 ? '#C98A2C' : '#B5482A'

  function pt(t, radius) {
    const a = Math.PI * (1 - t)
    return [cx - radius * Math.cos(a), cy - radius * Math.sin(a)]
  }

  const [bx1, by1] = pt(0, r)
  const [bx2, by2] = pt(1, r)
  const [fx2, fy2] = pt(clamped / 100, r)

  const needleT = clamped / 100
  const needleAngle = Math.PI * (1 - needleT)
  const nx = cx - (r - 14) * Math.cos(needleAngle)
  const ny = cy - (r - 14) * Math.sin(needleAngle)

  const ticks = []
  for (let i = 0; i <= 10; i++) {
    const t = i / 10
    const a = Math.PI * (1 - t)
    const r1 = r + 6
    const r2 = r + (i % 5 === 0 ? 14 : 10)
    const x1 = cx - r1 * Math.cos(a)
    const y1 = cy - r1 * Math.sin(a)
    const x2 = cx - r2 * Math.cos(a)
    const y2 = cy - r2 * Math.sin(a)
    ticks.push(
      <line
        key={i}
        x1={x1.toFixed(1)}
        y1={y1.toFixed(1)}
        x2={x2.toFixed(1)}
        y2={y2.toFixed(1)}
        stroke="#8A8577"
        strokeWidth="1"
        opacity="0.55"
      />
    )
  }

  return (
    <div className="text-center">
      <svg viewBox="0 0 220 140" width="220" height="140" role="img" aria-label="Overall match score dial">
        <title>Overall match score dial</title>
        <path
          d={`M ${bx1.toFixed(1)} ${by1.toFixed(1)} A ${r} ${r} 0 0 1 ${bx2.toFixed(1)} ${by2.toFixed(1)}`}
          fill="none"
          stroke="#DED8C4"
          strokeWidth="10"
          strokeLinecap="round"
        />
        <path
          d={`M ${bx1.toFixed(1)} ${by1.toFixed(1)} A ${r} ${r} 0 0 1 ${fx2.toFixed(1)} ${fy2.toFixed(1)}`}
          fill="none"
          stroke={arcColor}
          strokeWidth="10"
          strokeLinecap="round"
        />
        {ticks}
        <line
          x1={cx}
          y1={cy}
          x2={nx.toFixed(1)}
          y2={ny.toFixed(1)}
          stroke="#0F1512"
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        <circle cx={cx} cy={cy} r="5" fill="#0F1512" />
        <text
          x={cx}
          y={cy - 24}
          textAnchor="middle"
          fontFamily="Fraunces, serif"
          fontWeight="700"
          fontSize="34"
          fill="#0F1512"
        >
          {clamped}
        </text>
        <text
          x={cx - r - 2}
          y={cy + 16}
          textAnchor="start"
          fontSize="10"
          fill="#8A8577"
          fontFamily="'IBM Plex Mono', monospace"
        >
          0
        </text>
        <text
          x={cx + r + 2}
          y={cy + 16}
          textAnchor="end"
          fontSize="10"
          fill="#8A8577"
          fontFamily="'IBM Plex Mono', monospace"
        >
          100
        </text>
      </svg>
      <div className="mt-1.5 text-[11px] uppercase tracking-wider text-stone">Overall score</div>
    </div>
  )
}
