import { useEffect, useState } from 'react'

const STAGES = [
  'Reading documents…',
  'Extracting skills and requirements…',
  'Scoring the match…',
  'Writing the explanation…',
]

export default function LoadingStages() {
  const [i, setI] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setI((prev) => (prev + 1) % STAGES.length)
    }, 1800)
    return () => clearInterval(timer)
  }, [])

  return (
    <div className="mt-10 py-10 text-center">
      <div className="mb-3.5 font-display text-lg">{STAGES[i]}</div>
      <div className="track-sweep relative mx-auto h-0.5 max-w-[340px] overflow-hidden bg-hair" />
    </div>
  )
}
