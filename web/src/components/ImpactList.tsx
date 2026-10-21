import type { Decision, Impact } from '../types.ts'
import { SeverityChip } from './SeverityChip.tsx'

interface Props {
  impacts: Impact[]
  selected: string | null
  decisions: Record<string, Decision>
  onSelect: (path: string) => void
}

export function ImpactList({ impacts, selected, decisions, onSelect }: Props) {
  const max = Math.max(1, ...impacts.map((i) => i.score))
  return (
    <ol className="impacts">
      {impacts.map((impact, rank) => {
        const decision = decisions[impact.path]
        return (
          <li key={impact.path}>
            <button
              type="button"
              className={`impact ${selected === impact.path ? 'impact--active' : ''}`}
              data-path={impact.path}
              aria-pressed={selected === impact.path}
              onClick={() => onSelect(impact.path)}
            >
              <span className="impact__rank">{rank + 1}</span>
              <span className="impact__body">
                <span className="impact__path">{impact.path}</span>
                <span className="impact__meta">
                  <SeverityChip severity={impact.severity} />
                  <span>{impact.hit_count === 1 ? '1 hit' : `${impact.hit_count} hits`}</span>
                  {decision && (
                    <span className={`decision decision--${decision}`}>
                      {decision === 'accepted' ? 'Accepted' : 'Rejected'}
                    </span>
                  )}
                </span>
                <span className="impact__bar" aria-hidden="true">
                  <span style={{ transform: `scaleX(${impact.score / max})` }} />
                </span>
              </span>
            </button>
          </li>
        )
      })}
    </ol>
  )
}
