import { useEffect, useState } from 'react'
import { fetchHealth } from '../api'

export default function HealthBadge() {
  const [state, setState] = useState({ status: 'checking', label: 'checking service…' })

  useEffect(() => {
    let cancelled = false
    fetchHealth()
      .then((data) => {
        if (cancelled) return
        if (data.status === 'ok' && data.llm_configured) {
          setState({ status: 'ok', label: 'service ready' })
        } else if (data.status === 'ok') {
          setState({ status: 'bad', label: 'service up, LLM not configured' })
        } else {
          setState({ status: 'bad', label: 'service degraded' })
        }
      })
      .catch(() => {
        if (!cancelled) setState({ status: 'bad', label: 'service unreachable' })
      })
    return () => {
      cancelled = true
    }
  }, [])

  const dotColor =
    state.status === 'ok' ? 'bg-pine' : state.status === 'bad' ? 'bg-rust' : 'bg-stone'

  return (
    <div className="flex items-center gap-2 text-[11px] uppercase tracking-wider text-stone">
      <span className={`inline-block h-[7px] w-[7px] rounded-full ${dotColor}`} />
      <span>{state.label}</span>
    </div>
  )
}
