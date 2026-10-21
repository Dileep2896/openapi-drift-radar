import { useEffect, useMemo, useState } from 'react'
import { AnimatePresence, motion } from 'motion/react'
import { Link } from 'react-router'
import { analyzeScenario, analyzeSpecs, fetchScenarios } from '../api.ts'
import { ChangeList } from '../components/ChangeList.tsx'
import { CitationView } from '../components/CitationView.tsx'
import { DiffView } from '../components/DiffView.tsx'
import { ImpactList } from '../components/ImpactList.tsx'
import { buildPrDescription } from '../markdown.ts'
import { distance, duration, transition } from '../motion.ts'
import type { Decision, Report, Scenario } from '../types.ts'

const SAMPLE_BEFORE = `openapi: 3.1.0
info: { title: Demo, version: "1" }
paths:
  /v1/users/{id}:
    get:
      operationId: getUser
      parameters:
        - { name: expand, in: query, schema: { type: string } }
`
const SAMPLE_AFTER = `openapi: 3.1.0
info: { title: Demo, version: "2" }
paths:
  /v1/users/{id}:
    get:
      operationId: getUser
      parameters:
        - { name: include, in: query, schema: { type: string } }
`
const SAMPLE_DOC = `# Users

Fetch a user with \`GET /v1/users/{id}\`:

\`\`\`bash
curl "https://api.example.com/v1/users/usr_123?expand=teams"
\`\`\`
`

type Mode = 'scenario' | 'paste'

export function Radar() {
  const [scenarios, setScenarios] = useState<Scenario[]>([])
  const [scenarioId, setScenarioId] = useState('acme-payments')
  const [mode, setMode] = useState<Mode>('scenario')
  const [before, setBefore] = useState(SAMPLE_BEFORE)
  const [after, setAfter] = useState(SAMPLE_AFTER)
  const [docPath, setDocPath] = useState('users.mdx')
  const [docContent, setDocContent] = useState(SAMPLE_DOC)
  const [report, setReport] = useState<Report | null>(null)
  const [selected, setSelected] = useState<string | null>(null)
  const [decisions, setDecisions] = useState<Record<string, Decision>>({})
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchScenarios()
      .then(setScenarios)
      .catch(() => setError('Could not reach the radar API. Is the Flask server running on :5001?'))
  }, [])

  const scenario = scenarios.find((s) => s.id === scenarioId)
  const impact = useMemo(() => report?.impacts.find((i) => i.path === selected) ?? null, [report, selected])

  async function run() {
    setScanning(true)
    setError(null)
    setCopied(false)
    try {
      const minDelay = new Promise((r) => setTimeout(r, 450)) // let the sweep read as a scan, not a flicker
      const next =
        mode === 'scenario'
          ? await analyzeScenario(scenarioId)
          : await analyzeSpecs(before, after, [{ path: docPath || 'page.md', content: docContent }])
      await minDelay
      setReport(next)
      setDecisions({})
      setSelected(next.impacts[0]?.path ?? null)
    } catch (e) {
      setReport(null)
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setScanning(false)
    }
  }

  function decide(decision: Decision) {
    if (!impact) return
    setDecisions((d) => ({ ...d, [impact.path]: decision }))
  }

  async function exportPr() {
    if (!report) return
    await navigator.clipboard.writeText(buildPrDescription(report, decisions))
    setCopied(true)
  }

  return (
    <div className="radar">
      <header className="topbar">
        <Link to="/" className="brand">
          <span className="brand__dot" aria-hidden="true" />
          Drift Radar
          <span className="brand__tag">OpenAPI → docs drift check</span>
        </Link>
        <nav>
          <Link to="/story" className="link">Why this feature →</Link>
        </nav>
      </header>

      <main className="radar__main">
        <section className="panel input" aria-label="Radar input">
          <h1 className="radar__title">Which docs does this PR break?</h1>
          <p className="muted">
            Diff the OpenAPI spec, trace every reference in the docs, cite it by <code>file:line</code>, draft the fix.
          </p>

          <div role="tablist" className="tabs">
            <button role="tab" aria-selected={mode === 'scenario'} onClick={() => setMode('scenario')}>
              Seed scenario
            </button>
            <button role="tab" aria-selected={mode === 'paste'} onClick={() => setMode('paste')}>
              Paste specs
            </button>
          </div>

          {mode === 'scenario' ? (
            <div className="field">
              <label htmlFor="scenario">Scenario</label>
              <select id="scenario" value={scenarioId} onChange={(e) => setScenarioId(e.target.value)}>
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.title}
                  </option>
                ))}
              </select>
              {scenario && <p className="muted small">{scenario.description}</p>}
            </div>
          ) : (
            <div className="paste">
              <div className="field">
                <label htmlFor="before">Before spec</label>
                <textarea id="before" value={before} onChange={(e) => setBefore(e.target.value)} rows={9} spellCheck={false} />
              </div>
              <div className="field">
                <label htmlFor="after">After spec</label>
                <textarea id="after" value={after} onChange={(e) => setAfter(e.target.value)} rows={9} spellCheck={false} />
              </div>
              <div className="field field--wide">
                <label htmlFor="docpath">Docs page</label>
                <input id="docpath" value={docPath} onChange={(e) => setDocPath(e.target.value)} />
                <textarea aria-label="Docs page content" value={docContent} onChange={(e) => setDocContent(e.target.value)}
                  rows={7} spellCheck={false} />
              </div>
            </div>
          )}

          <button className="btn btn--primary run" onClick={run} disabled={scanning}>
            <span className="sweep" aria-hidden="true">
              {scanning && (
                <motion.span
                  className="sweep__arm"
                  animate={{ rotate: 360 }}
                  transition={{ repeat: Infinity, duration: 0.9, ease: 'linear' }}
                />
              )}
            </span>
            {scanning ? 'Scanning…' : 'Run radar'}
          </button>
          {error && (
            <p role="alert" className="error">
              {error}
            </p>
          )}
        </section>

        <AnimatePresence mode="wait">
          {report && (
            <motion.section
              key={`${report.summary.total_hits}-${report.summary.change_count}-${report.summary.scan_ms}`}
              className="results"
              initial={{ opacity: 0, y: distance.md }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -distance.sm }}
              transition={transition(duration.fast)}
            >
              {report.summary.skip_llm ? (
                <div className="panel noop">
                  <h2>No API contract changes.</h2>
                  <p>Skip the agent run: 0 LLM tokens spent on this PR.</p>
                </div>
              ) : (
                <>
                  <div className="summary panel">
                    <div>
                      <strong className="summary__big">{`${report.summary.total_hits} stale references`}</strong>
                      <span className="summary__sub">{`across ${report.summary.impacted_pages} pages`}</span>
                    </div>
                    <dl className="summary__stats">
                      <div><dt>Contract changes</dt><dd>{report.summary.change_count}</dd></div>
                      <div><dt>Breaking</dt><dd>{report.summary.breaking_count}</dd></div>
                      <div><dt>Pages scanned</dt><dd>{report.summary.pages_scanned}</dd></div>
                      <div><dt>Scan time</dt><dd>{`${report.summary.scan_ms.toFixed(1)} ms`}</dd></div>
                    </dl>
                    <button className="btn" onClick={exportPr}>
                      {copied ? 'Copied ✓' : 'Export as PR description'}
                    </button>
                  </div>

                  <div className="grid">
                    <div className="col">
                      <h2 className="h-label">Contract changes</h2>
                      <ChangeList changes={report.changes} />
                      <h2 className="h-label">Impacted pages · ranked</h2>
                      <ImpactList impacts={report.impacts} selected={selected} decisions={decisions} onSelect={setSelected} />
                      {!report.impacts.length && <p className="muted">No docs page references the changed operations.</p>}
                    </div>
                    <div className="col col--detail">
                      {impact && (
                        <motion.div
                          key={impact.path}
                          initial={{ opacity: 0, x: distance.md }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={transition(duration.fast)}
                        >
                          <div className="detail__head">
                            <h2 className="detail__title">{impact.path}</h2>
                            <div className="detail__actions">
                              <button className="btn btn--accept" aria-pressed={decisions[impact.path] === 'accepted'}
                                onClick={() => decide('accepted')}>Accept patch</button>
                              <button className="btn btn--reject" aria-pressed={decisions[impact.path] === 'rejected'}
                                onClick={() => decide('rejected')}>Reject</button>
                            </div>
                          </div>
                          <h3 className="h-label">Cited lines</h3>
                          <CitationView impact={impact} changes={report.changes} />
                          <h3 className="h-label">{`Suggested patch · ${report.summary.drafter}`}</h3>
                          <DiffView patch={impact.suggested_patch} />
                        </motion.div>
                      )}
                    </div>
                  </div>
                </>
              )}
            </motion.section>
          )}
        </AnimatePresence>
      </main>
    </div>
  )
}
