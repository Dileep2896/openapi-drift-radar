import type { ReactNode } from 'react'
import type { Change, Impact } from '../types.ts'
import { SeverityChip } from './SeverityChip.tsx'

function escapeRe(s: string) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function highlight(excerpt: string, term: string): ReactNode[] {
  // Templated path terms like /v1/users/{id} highlight whatever literal id the docs used.
  const source = term.startsWith('/')
    ? term.split('/').map((seg) => (seg.startsWith('{') ? '[^/\\s"\'`?]+' : escapeRe(seg))).join('/')
    : `(?<![\\w-])${escapeRe(term)}(?![\\w-])`
  const re = new RegExp(source, 'g')
  const out: ReactNode[] = []
  let last = 0
  for (const m of excerpt.matchAll(re)) {
    const at = m.index ?? 0
    out.push(excerpt.slice(last, at), <mark key={at}>{m[0]}</mark>)
    last = at + m[0].length
  }
  out.push(excerpt.slice(last))
  return out
}

export function CitationView({ impact, changes }: { impact: Impact; changes: Change[] }) {
  const byId = new Map(changes.map((c) => [c.id, c]))
  return (
    <ul className="citations">
      {impact.hits.map((h) => {
        const change = byId.get(h.change_id)
        return (
          <li key={`${h.line}-${h.change_id}`} className="citation">
            <div className="citation__head">
              <code className="citation__loc">{`${h.path}:${h.line}`}</code>
              <span className={`ctx ctx--${h.context}`}>{h.context}</span>
              <SeverityChip severity={h.severity} />
              {change && <span className="citation__why">{change.kind.replace(/_/g, ' ')}</span>}
            </div>
            <code className="citation__excerpt">{highlight(h.excerpt, h.term)}</code>
          </li>
        )
      })}
    </ul>
  )
}
