import { getDefaultNormalizer, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Radar } from '../pages/Radar.tsx'
import { noopReport, report } from './fixtures.ts'

function mockFetch(analyze = report) {
  return vi.fn(async (url: string, init?: RequestInit) => {
    if (url === '/api/scenarios') {
      return new Response(JSON.stringify({ scenarios: [
        { id: 'acme-payments', title: 'Acme Pay release', description: 'PR #482' },
        { id: 'noop', title: 'README-only PR', description: 'PR #483' },
      ] }))
    }
    if (url === '/api/analyze' && init?.method === 'POST') {
      const body = JSON.parse(String(init.body))
      if (body.before_spec === 'bad') return new Response(JSON.stringify({ error: 'Could not parse spec' }), { status: 400 })
      return new Response(JSON.stringify(body.scenario === 'noop' ? noopReport : analyze))
    }
    return new Response('{}', { status: 404 })
  })
}

const renderRadar = () => render(<MemoryRouter><Radar /></MemoryRouter>)

describe('Radar page', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', mockFetch())
  })
  afterEach(() => vi.unstubAllGlobals())

  it('runs the radar on a scenario and shows ranked impacts', async () => {
    renderRadar()
    await screen.findByRole('option', { name: 'Acme Pay release' })
    await userEvent.click(screen.getByRole('button', { name: /run radar/i }))
    expect(await screen.findByText('4 stale references')).toBeInTheDocument()
    expect(screen.getByText('across 2 pages')).toBeInTheDocument()
    expect(screen.getAllByText('api/charges.mdx:18').length).toBeGreaterThan(0)
    const raw = { normalizer: getDefaultNormalizer({ collapseWhitespace: false, trim: false }) }
    expect(screen.getByText("+  payment_method: 'tok_visa',", raw)).toBeInTheDocument()
  })

  it('switches the selected page and records accept/reject', async () => {
    renderRadar()
    await screen.findByRole('option', { name: 'Acme Pay release' })
    await userEvent.click(screen.getByRole('button', { name: /run radar/i }))
    await screen.findByText('4 stale references')
    await userEvent.click(screen.getByRole('button', { name: /accept patch/i }))
    expect(screen.getByText('Accepted')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /quickstart\.mdx/ }))
    expect(screen.getAllByText('quickstart.mdx:22').length).toBeGreaterThan(0)
    await userEvent.click(screen.getByRole('button', { name: /reject/i }))
    expect(screen.getByText('Rejected')).toBeInTheDocument()
  })

  it('exports the PR description to the clipboard', async () => {
    const user = userEvent.setup()
    const writeText = vi.fn(async () => {})
    Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
    renderRadar()
    await screen.findByRole('option', { name: 'Acme Pay release' })
    await user.click(screen.getByRole('button', { name: /run radar/i }))
    await screen.findByText('4 stale references')
    await user.click(screen.getByRole('button', { name: /export as pr description/i }))
    await waitFor(() => expect(writeText).toHaveBeenCalled())
    expect((writeText.mock.calls[0] as unknown as string[])[0]).toContain('## docs: update for API changes')
    expect(await screen.findByText(/copied/i)).toBeInTheDocument()
  })

  it('shows the skip-the-agent state for a no-op PR', async () => {
    renderRadar()
    await screen.findByRole('option', { name: 'README-only PR' })
    await userEvent.selectOptions(screen.getByLabelText(/scenario/i), 'noop')
    await userEvent.click(screen.getByRole('button', { name: /run radar/i }))
    expect(await screen.findByText(/skip the agent run/i)).toBeInTheDocument()
  })

  it('surfaces API errors from pasted specs', async () => {
    renderRadar()
    await userEvent.click(screen.getByRole('tab', { name: /paste specs/i }))
    const before = screen.getByLabelText(/before spec/i)
    await userEvent.clear(before)
    await userEvent.type(before, 'bad')
    await userEvent.click(screen.getByRole('button', { name: /run radar/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Could not parse spec')
  })
})
