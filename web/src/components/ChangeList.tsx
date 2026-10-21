import { motion } from 'motion/react'
import type { Change } from '../types.ts'
import { SeverityChip } from './SeverityChip.tsx'
import { distance, stagger, transition } from '../motion.ts'

function describe(c: Change): string {
  if (c.kind === 'param_renamed') return `${c.name} → ${c.new_name}`
  if (c.kind === 'enum_value_removed') return `${c.name}: −${c.value}`
  if (c.kind === 'endpoint_deprecated') return c.replacement ? `use ${c.replacement}` : 'deprecated'
  return c.name ?? ''
}

export function ChangeList({ changes }: { changes: Change[] }) {
  return (
    <ul className="changes">
      {changes.map((c, i) => (
        <motion.li
          key={c.id}
          className="changes__item"
          initial={{ opacity: 0, y: distance.sm }}
          animate={{ opacity: 1, y: 0 }}
          transition={transition(0.4, i * stagger)}
        >
          <SeverityChip severity={c.severity} />
          <span className="changes__kind">{c.kind.replace(/_/g, ' ')}</span>
          <code className="changes__op">{`${c.method} ${c.path}`}</code>
          {describe(c) && <span className="changes__detail">{describe(c)}</span>}
        </motion.li>
      ))}
    </ul>
  )
}
