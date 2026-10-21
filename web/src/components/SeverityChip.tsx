import type { Severity } from '../types.ts'

const LABEL: Record<Severity, string> = { breaking: 'Breaking', behavioral: 'Behavioral', additive: 'Additive' }

export function SeverityChip({ severity }: { severity: Severity }) {
  return <span className={`chip chip--${severity}`}>{LABEL[severity]}</span>
}
