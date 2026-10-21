import { motion } from 'motion/react'
import { duration, transition } from '../motion.ts'
import { reveal } from './reveal.ts'

const REASONS = ['Runs first, on every PR', 'Deterministic + cited', 'Skips no-op LLM runs']

export function DecisionScene({ reduced }: { reduced: boolean }) {
  return (
    <>
      <motion.h2 className="headline" {...reveal(reduced, 0)}>
        Why this feature?
      </motion.h2>
      <div className="cards">
        <motion.article
          className="card card--loser"
          initial={reduced ? false : { opacity: 0, x: -40 }}
          whileInView={{ opacity: 0.45, x: 0 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={transition(duration.normal, 0.2)}
        >
          <h3>Risk-ranked review queue</h3>
          <p>Sort suggestions by customer impact.</p>
          <motion.span
            className="strike"
            aria-hidden="true"
            initial={reduced ? false : { scaleX: 0 }}
            whileInView={{ scaleX: 1 }}
            viewport={{ once: true }}
            transition={transition(duration.normal, 0.9)}
          />
          <p className="card__verdict">✕ needs real usage data to prove</p>
        </motion.article>
        <motion.article
          className="card card--winner"
          initial={reduced ? false : { opacity: 0, x: 40, y: 0 }}
          whileInView={{ opacity: 1, x: 0, y: -10 }}
          viewport={{ once: true, amount: 0.4 }}
          transition={transition(duration.slow, 0.35)}
        >
          <h3>
            <span className="check" aria-hidden="true">✓</span> OpenAPI Drift Radar
          </h3>
          <ul>
            {REASONS.map((r, i) => (
              <motion.li key={r} {...reveal(reduced, i + 10, 10)}>
                {r}
              </motion.li>
            ))}
          </ul>
        </motion.article>
      </div>
    </>
  )
}
