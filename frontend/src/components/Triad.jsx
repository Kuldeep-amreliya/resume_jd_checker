function Block({ title, items }) {
  return (
    <div>
      <h3 className="mb-2.5 font-display text-base font-semibold">{title}</h3>
      {!items || items.length === 0 ? (
        <div className="text-xs italic text-[#B4AF9F]">— none —</div>
      ) : (
        <ul className="m-0 list-inside list-disc p-0">
          {items.map((item, i) => (
            <li key={i} className="mb-1.5 text-[12.5px] leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function Triad({ strengths, weaknesses, recommendations }) {
  return (
    <div className="mt-2 grid grid-cols-1 gap-8 md:grid-cols-3">
      <Block title="Strengths" items={strengths} />
      <Block title="Weaknesses" items={weaknesses} />
      <Block title="Recommendations" items={recommendations} />
    </div>
  )
}
