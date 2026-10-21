import { motion } from 'motion/react'
import { duration, transition } from '../motion.ts'
import { ImpactCounter } from './ImpactCounter.tsx'
import { reveal } from './reveal.ts'

// Lines 18-22 of seed/acme-payments/docs/quickstart.mdx, as shipped before the API change.
const SNIPPET = [
  { n: 18, text: 'curl https://api.acmepay.dev/v1/charges \\', stale: false },
  { n: 19, text: '  -u sk_test_acme_demo_key: \\', stale: false },
  { n: 20, text: '  -d amount=2000 \\', stale: false },
  { n: 21, text: '  -d currency=usd \\', stale: false },
  { n: 22, text: '  -d source=tok_visa', stale: true },
]

export function PainScene({ reduced, staleRefs }: { reduced: boolean; staleRefs: number }) {
  return (
    <div className="split">
      <div>
        <motion.h2 className="headline" data-testid="pain-headline" {...reveal(reduced, 0)}>
          One API change. <span className="accent-red">{`${staleRefs} stale docs lines`}</span>. Nobody notices.
        </motion.h2>
        <motion.div className="ticker" {...reveal(reduced, 2)}>
          <span className="ticker__label">PRs / dev / week</span>
          <ImpactCounter id="prs" from={1} value={10} reduced={reduced} />
          <span className="ticker__note">with AI coding assistants</span>
        </motion.div>
      </div>
      <motion.figure className="mockdoc" {...reveal(reduced, 1)}>
        <figcaption className="mockdoc__bar">
          <span /><span /><span />
          <code>docs/quickstart.mdx</code>
        </figcaption>
        <pre className="mockdoc__code">
          {SNIPPET.map((line, i) => (
            <div key={line.n} className={`mockdoc__line ${line.stale ? 'mockdoc__line--stale' : ''}`}>
              {line.stale && (
                <motion.span
                  className="mockdoc__pulse"
                  aria-hidden="true"
                  initial={reduced ? false : { opacity: 0 }}
                  whileInView={reduced ? undefined : { opacity: [0, 1, 0.35, 1] }}
                  viewport={{ once: true }}
                  transition={transition(duration.slow * 2, 0.6 + i * 0.09)}
                />
              )}
              <span className="ln">{line.n}</span>
              {line.text}
            </div>
          ))}
        </pre>
        <p className="mockdoc__caption">
          <code>source</code> was renamed to <code>payment_method</code>. These docs still say <code>source</code>.
        </p>
      </motion.figure>
    </div>
  )
}
