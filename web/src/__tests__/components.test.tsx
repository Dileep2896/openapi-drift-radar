import { getDefaultNormalizer, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { SeverityChip } from '../components/SeverityChip.tsx'
import { ImpactList } from '../components/ImpactList.tsx'
import { DiffView } from '../components/DiffView.tsx'
import { ChangeList } from '../components/ChangeList.tsx'
import { CitationView } from '../components/CitationView.tsx'
import { report } from './fixtures.ts'

describe('SeverityChip', () => {
  it.each([
    ['breaking', 'Breaking'],
    ['behavioral', 'Behavioral'],
    ['additive', 'Additive'],
  ] as const)('renders %s as %s', (severity, label) => {
    render(<SeverityChip severity={severity} />)
    const chip = screen.getByText(label)
    expect(chip).toHaveClass(`chip--${severity}`)
  })
})

describe('ChangeList', () => {
  it('shows every change with its operation and severity', () => {
    render(<ChangeList changes={report.changes} />)
    const items = screen.getAllByRole('listitem')
    expect(items).toHaveLength(3)
    expect(within(items[0]).getByText('POST /v1/charges')).toBeInTheDocument()
    expect(within(items[0]).getByText('Breaking')).toBeInTheDocument()
    expect(within(items[0]).getByText(/source → payment_method/)).toBeInTheDocument()
  })
})

describe('ImpactList', () => {
  it('keeps the server ranking order and shows hit counts', () => {
    render(<ImpactList impacts={report.impacts} selected={null} decisions={{}} onSelect={() => {}} />)
    const buttons = screen.getAllByRole('button')
    expect(buttons.map((b) => b.dataset.path)).toEqual(['api/charges.mdx', 'quickstart.mdx'])
    expect(within(buttons[0]).getByText('3 hits')).toBeInTheDocument()
    expect(within(buttons[1]).getByText('1 hit')).toBeInTheDocument()
  })

  it('reports selection and marks decisions', async () => {
    const onSelect = vi.fn()
    render(
      <ImpactList impacts={report.impacts} selected="quickstart.mdx" decisions={{ 'api/charges.mdx': 'accepted' }}
        onSelect={onSelect} />,
    )
    await userEvent.click(screen.getByRole('button', { name: /api\/charges\.mdx/ }))
    expect(onSelect).toHaveBeenCalledWith('api/charges.mdx')
    expect(screen.getByRole('button', { name: /quickstart\.mdx/ })).toHaveAttribute('aria-pressed', 'true')
    expect(screen.getByText('Accepted')).toBeInTheDocument()
  })
})

describe('DiffView', () => {
  it('renders added, removed, hunk and context lines', () => {
    render(<DiffView patch={report.impacts[0].suggested_patch} />)
    const raw = { normalizer: getDefaultNormalizer({ collapseWhitespace: false, trim: false }) }
    expect(screen.getByText("-  source: 'tok_visa',", raw)).toHaveClass('diff__line--del')
    expect(screen.getByText("+  payment_method: 'tok_visa',", raw)).toHaveClass('diff__line--add')
    expect(screen.getByText('@@ -17,3 +17,3 @@')).toHaveClass('diff__line--hunk')
    expect(screen.getByText('context line', { exact: false })).toHaveClass('diff__line--ctx')
  })

  it('handles an empty patch', () => {
    render(<DiffView patch="" />)
    expect(screen.getByText(/No changes drafted/)).toBeInTheDocument()
  })
})

describe('CitationView', () => {
  it('cites file:line and highlights the matched term', () => {
    const { container } = render(<CitationView impact={report.impacts[0]} changes={report.changes} />)
    expect(screen.getByText('api/charges.mdx:18')).toBeInTheDocument()
    expect(screen.getByText('api/charges.mdx:40')).toBeInTheDocument()
    const marks = container.querySelectorAll('mark')
    expect(marks.length).toBe(3)
    expect(marks[0].textContent).toBe('source')
  })
})
