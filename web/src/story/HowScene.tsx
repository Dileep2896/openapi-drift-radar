import { motion } from 'motion/react'
import { reveal } from './reveal.ts'

interface Props {
  reduced: boolean
  changes: number
  breaking: number
  pagesScanned: number
  impactedPages: number
}

export function HowScene({ reduced, changes, breaking, pagesScanned, impactedPages }: Props) {
  const steps = [
    {
      title: 'Diff the spec',
      body: 'A typed structural diff of the before/after OpenAPI files: renames, removed params, new required fields, type and enum changes, deprecations.',
      stat: `${changes} changes · ${breaking} breaking`,
    },
    {
      title: 'Trace every reference',
      body: 'Scans prose, tables and code fences (curl, Python, JS, JSON) on every docs page, with a parent-operation guard against false alarms.',
      stat: `${pagesScanned} pages scanned`,
    },
    {
      title: 'Rank and cite',
      body: 'Orders impacted pages by severity × hits, and cites each stale line as file:line so a reviewer can check it in one click.',
      stat: `${impactedPages} pages impacted`,
    },
    {
      title: 'Draft the fix',
      body: 'A pluggable Drafter writes a unified-diff patch per page. A deterministic rule-based drafter is the default; an LLM drafter is optional.',
      stat: 'empty diff → skip the LLM',
    },
  ]
  return (
    <>
      <motion.h2 className="headline" {...reveal(reduced, 0)}>
        What it does, on every pull request.
      </motion.h2>
      <ol className="how" data-testid="how-steps">
        {steps.map((s, i) => (
          <motion.li key={s.title} className="how__step" {...reveal(reduced, i + 1, 18)}>
            <span className="how__num" aria-hidden="true">{i + 1}</span>
            <h3>{s.title}</h3>
            <p>{s.body}</p>
            <span className="how__stat">{s.stat}</span>
          </motion.li>
        ))}
      </ol>
    </>
  )
}
