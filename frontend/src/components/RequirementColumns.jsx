function Column({ title, swatchClass, items }) {
  return (
    <div className="bg-paper-raised p-4.5 px-[18px] pb-5 pt-[18px]">
      <h3 className="mb-3 flex items-center gap-2 text-[11px] uppercase tracking-wide">
        <span className={`inline-block h-2 w-2 rounded-full ${swatchClass}`} />
        {title}
      </h3>
      {!items || items.length === 0 ? (
        <div className="text-xs italic text-[#B4AF9F]">— none —</div>
      ) : (
        <ul className="m-0 list-none p-0">
          {items.map((item, i) => (
            <li
              key={i}
              className="flex gap-2 border-b border-hair py-1.5 text-[12.5px] last:border-b-0"
            >
              <span className="flex-shrink-0 text-stone">—</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export default function RequirementColumns({ matched, missing, unknown }) {
  return (
    <div className="grid grid-cols-1 gap-px border border-hair-strong bg-hair-strong md:grid-cols-3">
      <Column title="Matched" swatchClass="bg-pine" items={matched} />
      <Column title="Missing" swatchClass="bg-rust" items={missing} />
      <Column title="Unclear" swatchClass="bg-stone" items={unknown} />
    </div>
  )
}
