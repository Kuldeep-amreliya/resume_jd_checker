export default function SectionTitle({ children }) {
  return (
    <div className="mt-11 mb-4 flex items-center gap-3 text-[11px] uppercase tracking-widest text-stone">
      <span>{children}</span>
      <span className="h-px flex-1 bg-hair-strong" />
    </div>
  )
}
