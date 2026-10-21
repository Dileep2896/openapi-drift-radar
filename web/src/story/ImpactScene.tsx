import { motion } from 'motion/react'
import { Link } from 'react-router'
import { ImpactCounter } from './ImpactCounter.tsx'
import { reveal } from './reveal.ts'

interface Metrics {
  stale_refs: number
  scan_ms: number
  pages_scanned: number
  cited_pct: number
  noop_llm_tokens: number | null
}

export function ImpactScene({ reduced, metrics }: { reduced: boolean; metrics: Metrics }) {
  const stats = [
    { id: 'stale_refs', value: metrics.stale_refs, label: 'stale refs found', decimals: 0, suffix: '' },
    { id: 'scan_ms', value: metrics.scan_ms, label: `ms to scan ${metrics.pages_scanned} pages`, decimals: 1, suffix: '' },
    { id: 'cited_pct', value: metrics.cited_pct, label: 'cited file:line', decimals: 0, suffix: '%' },
    { id: 'noop_llm_tokens', value: metrics.noop_llm_tokens ?? 0, label: 'LLM tokens on no-op PRs', decimals: 0, suffix: '' },
  ]
  return (
    <>
      <motion.h2 className="headline" {...reveal(reduced, 0)}>
        Every stale line, found before the agent runs.
      </motion.h2>
      <div className="stats">
        {stats.map((s, i) => (
          <motion.div key={s.id} className="stat" {...reveal(reduced, i + 1, 20)}>
            <ImpactCounter id={s.id} value={s.value} decimals={s.decimals} suffix={s.suffix} reduced={reduced} />
            <span className="stat__label">{s.label}</span>
          </motion.div>
        ))}
      </div>
      <motion.div className="cta" {...reveal(reduced, 6, 10)}>
        <Link to="/" className="btn btn--primary">Try the radar →</Link>
        <p className="fineprint">Numbers come from the real Acme Pay seed run (story-metrics.json).</p>
      </motion.div>
    </>
  )
}
