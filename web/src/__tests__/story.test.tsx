import { act, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { Story } from '../pages/Story.tsx'
import metrics from '../story/story-metrics.json'
import { motionPref } from '../test-setup.ts'

const renderStory = (url = '/story') => render(<MemoryRouter initialEntries={[url]}><Story /></MemoryRouter>)

describe('Story page', () => {
  afterEach(() => vi.useRealTimers())

  it('renders all six scenes', () => {
    renderStory()
    const scenes = screen.getAllByTestId('scene')
    expect(scenes.map((s) => s.dataset.scene)).toEqual(['problem', 'pain', 'decision', 'how', 'before-after', 'impact'])
    expect(screen.getByText('Drift Radar')).toBeInTheDocument()
    expect(screen.getByText(/independent open-source project/i)).toBeInTheDocument()
    expect(screen.getByTestId('how-steps').children).toHaveLength(4)
    for (const step of ['Spec change', 'Detect', 'Draft', 'Review']) expect(screen.getAllByText(step).length).toBeGreaterThan(0)
    expect(screen.getByRole('link', { name: /try the radar/i })).toHaveAttribute('href', '/')
  })

  it('uses the real seed numbers', () => {
    renderStory()
    expect(screen.getByTestId('pain-headline')).toHaveTextContent(`${metrics.stale_refs} stale docs lines`)
    expect(screen.getAllByText(`${metrics.top_page}:${metrics.pages[0].lines[0]}`).length).toBeGreaterThan(0)
  })

  it('renders counters at their final value under reduced motion', () => {
    motionPref.reduced = true
    renderStory()
    expect(screen.getByTestId('counter-stale_refs')).toHaveTextContent(String(metrics.stale_refs))
    expect(screen.getByTestId('counter-cited_pct')).toHaveTextContent('100%')
    expect(screen.getByTestId('counter-noop_llm_tokens')).toHaveTextContent('0')
  })

  it('autoplay advances one scene at a time', () => {
    vi.useFakeTimers()
    renderStory('/story?autoplay=1')
    expect(screen.getByTestId('story-progress')).toHaveAttribute('data-active', '0')
    act(() => { vi.advanceTimersByTime(4300) })
    expect(screen.getByTestId('story-progress')).toHaveAttribute('data-active', '1')
    act(() => { vi.advanceTimersByTime(4300 * 10) })
    expect(screen.getByTestId('story-progress')).toHaveAttribute('data-active', '5')
  })
})
