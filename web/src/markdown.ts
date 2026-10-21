import type { Decision, Report } from './types.ts'

export function buildPrDescription(report: Report, decisions: Record<string, Decision>): string {
  const s = report.summary
  if (!report.changes.length) {
    return '## docs: no update needed\n\nNo API contract changes in this PR. Skipped the docs agent run.\n'
  }
  const accepted = report.impacts.filter((i) => decisions[i.path] === 'accepted')
  const rejected = report.impacts.filter((i) => decisions[i.path] === 'rejected')
  const pending = report.impacts.filter((i) => !decisions[i.path])
  const out = [
    '## docs: update for API changes',
    '',
    `OpenAPI Drift Radar found **${s.total_hits} stale references across ${s.impacted_pages} pages** ` +
      `(${s.change_count} contract changes, ${s.breaking_count} breaking).`,
    '',
    '### Contract changes',
    ...report.changes.map((c) => `- **${c.kind}** \`${c.method} ${c.path}\`: ${c.detail}`),
    '',
  ]
  if (accepted.length) {
    out.push('### Accepted doc updates', '')
    for (const i of accepted) {
      out.push(`#### \`${i.path}\` (${i.hit_count} stale refs)`, '')
      out.push(...i.hits.map((h) => `- \`${h.path}:${h.line}\` ${h.kind}`), '')
      out.push('```diff', i.suggested_patch.replace(/\n$/, ''), '```', '')
    }
  }
  if (rejected.length) out.push(`Rejected: ${rejected.map((i) => `\`${i.path}\``).join(', ')}`, '')
  if (pending.length) out.push(`Pending review: ${pending.map((i) => `\`${i.path}\``).join(', ')}`, '')
  out.push('_Drafted by OpenAPI Drift Radar._')
  return out.join('\n') + '\n'
}
