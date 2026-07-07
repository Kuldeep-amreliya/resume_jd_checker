import { useRef, useState } from 'react'

/**
 * A single intake panel (Resume or JD side). Handles switching between
 * "file" and "text" mode, drag-and-drop, and reports its current value
 * up to the parent via onChange.
 */
export default function IntakePanel({ label, eyebrow, value, onChange }) {
  const [mode, setMode] = useState(value.mode || 'file')
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  function setMode_(next) {
    setMode(next)
    onChange({ ...value, mode: next })
  }

  function handleFile(file) {
    onChange({ ...value, mode, file })
  }

  function handleText(text) {
    onChange({ ...value, mode, text })
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files?.[0]
    if (file) {
      handleFile(file)
      if (inputRef.current) {
        // keep the native input in sync so a re-render doesn't lose it visually
        const dt = new DataTransfer()
        dt.items.add(file)
        inputRef.current.files = dt.files
      }
    }
  }

  function clearFile() {
    onChange({ ...value, mode, file: null })
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="bg-paper-raised p-6">
      <div className="mb-3.5 flex items-center justify-between text-[11px] uppercase tracking-wider text-stone">
        <span>{eyebrow}</span>
        <div className="inline-flex overflow-hidden rounded-[3px] border border-hair-strong">
          <button
            type="button"
            onClick={() => setMode_('file')}
            className={`px-2.5 py-1.5 text-[11px] uppercase tracking-wide ${
              mode === 'file' ? 'bg-ink text-paper' : 'text-stone'
            }`}
          >
            File
          </button>
          <button
            type="button"
            onClick={() => setMode_('text')}
            className={`px-2.5 py-1.5 text-[11px] uppercase tracking-wide ${
              mode === 'text' ? 'bg-ink text-paper' : 'text-stone'
            }`}
          >
            Paste text
          </button>
        </div>
      </div>

      <h2 className="mb-4 font-display text-[22px] font-semibold">{label}</h2>

      {mode === 'file' ? (
        <div>
          <label
            onDragEnter={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragOver={(e) => {
              e.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={(e) => {
              e.preventDefault()
              setDragActive(false)
            }}
            onDrop={handleDrop}
            className={`block cursor-pointer rounded-[2px] border border-dashed px-4 py-9 text-center text-stone transition-colors ${
              dragActive ? 'border-pine bg-pine-dim' : 'border-hair-strong hover:border-pine hover:bg-pine-dim'
            }`}
          >
            <span className="mb-1.5 block font-display text-xl text-stone">⇪</span>
            <span>Drop a PDF / DOCX / TXT, or click to browse</span>
            {value.file && (
              <span className="mt-2 block font-medium text-ink">{value.file.name}</span>
            )}
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.docx,.doc,.txt"
              className="hidden"
              onChange={(e) => handleFile(e.target.files?.[0] || null)}
            />
          </label>
          {value.file && (
            <button
              type="button"
              onClick={clearFile}
              className="mt-2 border-none bg-transparent p-0 text-[11px] text-rust underline"
            >
              remove file
            </button>
          )}
        </div>
      ) : (
        <textarea
          value={value.text || ''}
          onChange={(e) => handleText(e.target.value)}
          placeholder={`Paste ${label.toLowerCase()} text here…`}
          className="min-h-[220px] w-full resize-y rounded-[2px] border border-hair-strong bg-paper p-3.5 font-mono text-[12.5px] leading-relaxed text-ink placeholder:text-[#B4AF9F] focus:outline-2 focus:outline-pine"
        />
      )}
    </div>
  )
}
