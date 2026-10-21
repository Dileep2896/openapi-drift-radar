import { forwardRef, type ReactNode } from 'react'

interface Props {
  id: string
  index: number
  eyebrow: string
  children: ReactNode
}

export const Scene = forwardRef<HTMLElement, Props>(function Scene({ id, index, eyebrow, children }, ref) {
  return (
    <section ref={ref} className={`scene scene--${id}`} data-testid="scene" data-scene={id} data-index={index}
      aria-label={eyebrow}>
      <div className="scene__inner">
        <p className="eyebrow">{`0${index + 1} · ${eyebrow}`}</p>
        {children}
      </div>
    </section>
  )
})
