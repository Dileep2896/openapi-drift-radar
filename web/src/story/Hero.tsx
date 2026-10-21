import { motion } from 'motion/react'
import { duration, stagger, transition } from '../motion.ts'
import { reveal } from './reveal.ts'

const TAGLINE = 'Keeping API docs in sync with the code that changes them'.split(' ')
const STEPS = ['Spec change', 'Detect', 'Draft', 'Review']
const FOCUS = 1

export function Hero({ reduced }: { reduced: boolean }) {
  return (
    <>
      <motion.h1 className="wordmark" {...reveal(reduced, 0, 12)}>
        Drift Radar
      </motion.h1>
      <p className="tagline" aria-label={TAGLINE.join(' ')}>
        {TAGLINE.map((word, i) => (
          <motion.span key={i} className="tagline__word" aria-hidden="true" {...reveal(reduced, i + 2, 14)}>
            {word}
          </motion.span>
        ))}
        <motion.span className="badge" {...reveal(reduced, TAGLINE.length + 2, 10)}>
          open source
        </motion.span>
      </p>
      <div className="loop" role="list" aria-label="Docs maintenance loop">
        <motion.span
          className="loop__line"
          aria-hidden="true"
          initial={reduced ? false : { scaleX: 0 }}
          whileInView={{ scaleX: 1 }}
          viewport={{ once: true }}
          transition={transition(duration.slow * 2, 0.9)}
        />
        {STEPS.map((step, i) => (
          <motion.div
            key={step}
            role="listitem"
            className={`loop__step ${i === FOCUS ? 'loop__step--focus' : ''}`}
            initial={reduced ? false : { opacity: 0, scale: 0.85 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={transition(duration.fast, 1.0 + i * stagger * 4)}
          >
            <span className="loop__dot" />
            {step}
          </motion.div>
        ))}
      </div>
      <motion.p className="fineprint" {...reveal(reduced, 14, 0)}>
        Independent open-source project · built with Claude Code
      </motion.p>
    </>
  )
}
