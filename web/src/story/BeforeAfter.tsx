import { motion } from 'motion/react'
import { duration, stagger, transition } from '../motion.ts'
import { reveal } from './reveal.ts'

interface Page {
  path: string
  hits: number
  lines: number[]
}

const W = 960
const CARD_X = 600
const CARD_W = 340
const CARD_H = 50
const GAP = 14

export function BeforeAfter({ reduced, pages }: { reduced: boolean; pages: Page[] }) {
  const height = pages.length * (CARD_H + GAP) + 20
  const originY = height / 2
  return (
    <>
      <motion.h2 className="headline" {...reveal(reduced, 0)}>
        Diff the spec. Trace every reference. Draft the fix.
      </motion.h2>
      <motion.div className="diagram" {...reveal(reduced, 1, 12)}>
        <svg viewBox={`0 0 ${W} ${height}`} role="img"
          aria-label={`A spec diff fans out to ${pages.length} impacted docs pages, each cited by file and line`}>
          <defs>
            <linearGradient id="wire" x1="0" x2="1">
              <stop offset="0" stopColor="var(--accent)" stopOpacity="0.9" />
              <stop offset="1" stopColor="var(--accent-2)" stopOpacity="0.9" />
            </linearGradient>
          </defs>
          <g transform={`translate(20 ${originY - 90})`}>
            <rect width="300" height="180" rx="14" className="svg-box" />
            <text x="18" y="32" className="svg-file">openapi.yaml · PR #482</text>
            <text x="18" y="74" className="svg-code svg-del">- source:</text>
            <text x="18" y="102" className="svg-code svg-add">+ payment_method:</text>
            <text x="18" y="130" className="svg-code svg-del">- default_source:</text>
            <text x="18" y="158" className="svg-code svg-muted">  deprecated: true</text>
          </g>
          {pages.map((p, i) => {
            const cy = 10 + i * (CARD_H + GAP) + CARD_H / 2
            const d = `M320 ${originY} C 460 ${originY}, 460 ${cy}, ${CARD_X} ${cy}`
            const delay = 0.5 + i * stagger * 1.4
            return (
              <g key={p.path}>
                <motion.path
                  d={d}
                  fill="none"
                  stroke="url(#wire)"
                  strokeWidth="2"
                  initial={reduced ? false : { pathLength: 0, opacity: 0 }}
                  whileInView={{ pathLength: 1, opacity: 1 }}
                  viewport={{ once: true }}
                  transition={transition(duration.slow, delay)}
                />
                <motion.g
                  initial={reduced ? false : { opacity: 0, x: 24 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  viewport={{ once: true }}
                  transition={transition(duration.fast, delay + 0.45)}
                >
                  <rect x={CARD_X} y={cy - CARD_H / 2} width={CARD_W} height={CARD_H} rx="10" className="svg-card" />
                  <text x={CARD_X + 16} y={cy + 5} className="svg-path">{p.path}</text>
                  <rect x={CARD_X + CARD_W - 112} y={cy - 13} width="98" height="26" rx="13" className="svg-badge" />
                  <text x={CARD_X + CARD_W - 63} y={cy + 5} textAnchor="middle" className="svg-badge-text">
                    {`${p.hits} × L${p.lines[0]}`}
                  </text>
                </motion.g>
              </g>
            )
          })}
        </svg>
      </motion.div>
      <div className="ba">
        <motion.div className="ba__panel ba__panel--before" {...reveal(reduced, 3, 16)}>
          <p className="ba__label">Before · grep + hope</p>
          <ul>
            <li><code>faq.md</code> “open source”: false alarm</li>
            <li><code>webhooks.mdx</code> payload: false alarm</li>
            <li><code>default_source</code>, <code>duplicate_charge</code>: never searched</li>
          </ul>
        </motion.div>
        <motion.div className="ba__panel ba__panel--after" {...reveal(reduced, 4, 16)}>
          <p className="ba__label">After · ranked, cited, drafted</p>
          <ol>
            {pages.slice(0, 4).map((p, i) => (
              <motion.li
                key={p.path}
                initial={reduced ? false : { opacity: 0, x: 30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={transition(duration.fast, 1.2 + i * stagger * 2)}
              >
                <code>{`${p.path}:${p.lines[0]}`}</code>
                <span className="ba__hits">{`${p.hits} hits`}</span>
                <span className="ba__patch">patch drafted</span>
              </motion.li>
            ))}
          </ol>
        </motion.div>
      </div>
    </>
  )
}
