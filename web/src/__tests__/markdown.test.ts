import { describe, expect, it } from 'vitest'
import { buildPrDescription } from '../markdown.ts'
import { noopReport, report } from './fixtures.ts'

describe('buildPrDescription', () => {
  it('lists accepted pages with patches and leaves rejected ones out', () => {
    const md = buildPrDescription(report, { 'api/charges.mdx': 'accepted', 'quickstart.mdx': 'rejected' })
    expect(md).toContain('## docs: update for API changes')
    expect(md).toContain('`api/charges.mdx` (3 stale refs)')
    expect(md).toContain('```diff')
    expect(md).not.toContain('payment_method=tok_visa')
    expect(md).toContain('Rejected: `quickstart.mdx`')
  })

  it('includes undecided pages as pending review', () => {
    const md = buildPrDescription(report, {})
    expect(md).toContain('Pending review: `api/charges.mdx`, `quickstart.mdx`')
  })

  it('handles no-op PRs', () => {
    expect(buildPrDescription(noopReport, {})).toContain('No API contract changes')
  })
})
