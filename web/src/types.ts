export type Severity = 'breaking' | 'behavioral' | 'additive'
export type Context = 'code' | 'table' | 'prose'

export interface Change {
  id: string
  kind: string
  severity: Severity
  method: string
  path: string
  operation_id: string | null
  name: string | null
  new_name: string | null
  value: string | null
  location: string | null
  replacement: string | null
  detail: string
}

export interface Hit {
  path: string
  line: number
  excerpt: string
  context: Context
  change_id: string
  kind: string
  severity: Severity
  term: string
}

export interface Impact {
  path: string
  score: number
  hit_count: number
  severity: Severity
  change_ids: string[]
  hits: Hit[]
  suggested_patch: string
}

export interface Summary {
  change_count: number
  breaking_count: number
  impacted_pages: number
  total_hits: number
  pages_scanned: number
  skip_llm: boolean
  scan_ms: number
  drafter: string
}

export interface Report {
  changes: Change[]
  impacts: Impact[]
  summary: Summary
}

export interface Scenario {
  id: string
  title: string
  description: string
}

export type Decision = 'accepted' | 'rejected'

export interface DocInput {
  path: string
  content: string
}
