import { distance, duration, stagger, transition } from '../motion.ts'

/** Entrance props for a scroll-revealed element; under reduced motion it renders in its final state. */
export function reveal(reduced: boolean, index = 0, y: number = distance.lg) {
  if (reduced) return { initial: false as const }
  return {
    initial: { opacity: 0, y },
    whileInView: { opacity: 1, y: 0 },
    viewport: { once: true, amount: 0.3 },
    transition: transition(duration.normal, index * stagger),
  }
}
