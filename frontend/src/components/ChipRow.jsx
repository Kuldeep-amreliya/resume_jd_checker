export default function ChipRow({ items }) {
  if (!items || items.length === 0) {
    return <span className="text-[11px] text-[#B4AF9F]">none listed</span>
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => (
        <span key={i} className="rounded-[2px] border border-hair-strong bg-paper px-2 py-0.5 text-[11px]">
          {item}
        </span>
      ))}
    </div>
  )
}
