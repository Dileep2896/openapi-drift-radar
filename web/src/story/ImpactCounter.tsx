import { animate, useInView } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { ease } from '../motion.ts'

interface Props {
  id: string
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
  reduced: boolean
  from?: number
}

/** Counts up to `value` when scrolled into view; renders the final number immediately under reduced motion. */
export function ImpactCounter({ id, value, decimals = 0, prefix = '', suffix = '', reduced, from = 0 }: Props) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true, amount: 0.6 })
  const [shown, setShown] = useState(reduced ? value : from)

  useEffect(() => {
    if (reduced || !inView) return
    const controls = animate(from, value, { duration: 1.4, ease, onUpdate: setShown })
    return () => controls.stop()
  }, [inView, reduced, value, from])

  const display = reduced ? value : shown
  return (
    <span ref={ref} className="counter" data-testid={`counter-${id}`}>
      {`${prefix}${display.toFixed(decimals)}${suffix}`}
    </span>
  )
}
