import type { DocInput, Report, Scenario } from './types.ts'

async function json<T>(res: Response): Promise<T> {
  const body = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error((body as { error?: string }).error ?? `Request failed (${res.status})`)
  return body as T
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const data = await json<{ scenarios: Scenario[] }>(await fetch('/api/scenarios'))
  return data.scenarios
}

export async function analyzeScenario(scenario: string): Promise<Report> {
  return json<Report>(
    await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario }),
    }),
  )
}

export async function analyzeSpecs(before_spec: string, after_spec: string, docs: DocInput[]): Promise<Report> {
  return json<Report>(
    await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ before_spec, after_spec, docs }),
    }),
  )
}
