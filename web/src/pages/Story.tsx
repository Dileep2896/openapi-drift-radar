import { MotionConfig } from 'motion/react'
import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router'
import { BeforeAfter } from '../story/BeforeAfter.tsx'
import { DecisionScene } from '../story/DecisionScene.tsx'
import { Hero } from '../story/Hero.tsx'
import { HowScene } from '../story/HowScene.tsx'
import { ImpactScene } from '../story/ImpactScene.tsx'
import { PainScene } from '../story/PainScene.tsx'
import { Scene } from '../story/Scene.tsx'
import metrics from '../story/story-metrics.json'
import { useReducedMotion } from '../story/useReducedMotion.ts'

export const SCENE_MS = 4000
const SCENES = [
  { id: 'problem', eyebrow: 'The problem' },
  { id: 'pain', eyebrow: 'The pain' },
  { id: 'decision', eyebrow: 'Why this feature' },
  { id: 'how', eyebrow: 'What it does' },
  { id: 'before-after', eyebrow: 'Before → after' },
  { id: 'impact', eyebrow: 'The impact' },
]

export function Story() {
  const reduced = useReducedMotion()
  const [params] = useSearchParams()
  const autoplay = params.get('autoplay') === '1'
  const [active, setActive] = useState(0)
  const refs = useRef<(HTMLElement | null)[]>([])

  // Autoplay: advance one scene every SCENE_MS so the brag recorder can capture it hands-free.
  useEffect(() => {
    if (!autoplay) return
    const timer = setInterval(() => setActive((a) => Math.min(a + 1, SCENES.length - 1)), SCENE_MS)
    return () => clearInterval(timer)
  }, [autoplay])

  useEffect(() => {
    if (!autoplay) return
    refs.current[active]?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth', block: 'start' })
  }, [active, autoplay, reduced])

  // Manual scrolling keeps the progress rail in sync.
  useEffect(() => {
    if (autoplay) return
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) {
          if (e.isIntersecting) setActive(Number((e.target as HTMLElement).dataset.index))
        }
      },
      { threshold: 0.55 },
    )
    refs.current.forEach((el) => el && io.observe(el))
    return () => io.disconnect()
  }, [autoplay])

  const body = [
    <Hero reduced={reduced} />,
    <PainScene reduced={reduced} staleRefs={metrics.stale_refs} />,
    <DecisionScene reduced={reduced} />,
    <HowScene reduced={reduced} changes={metrics.changes} breaking={metrics.breaking}
      pagesScanned={metrics.pages_scanned} impactedPages={metrics.impacted_pages} />,
    <BeforeAfter reduced={reduced} pages={metrics.pages} />,
    <ImpactScene reduced={reduced} metrics={metrics} />,
  ]

  return (
    <MotionConfig reducedMotion={reduced ? 'always' : 'never'}>
      <div className={`story ${autoplay ? 'story--autoplay' : ''}`}>
        <nav className="progress" data-testid="story-progress" data-active={active} aria-label="Story progress">
          {SCENES.map((s, i) => (
            <button
              key={s.id}
              type="button"
              aria-label={`Go to scene ${i + 1}: ${s.eyebrow}`}
              aria-current={i === active ? 'step' : undefined}
              className={`progress__dot ${i === active ? 'progress__dot--active' : ''}`}
              onClick={() => {
                setActive(i)
                refs.current[i]?.scrollIntoView({ behavior: reduced ? 'auto' : 'smooth' })
              }}
            />
          ))}
        </nav>
        {SCENES.map((s, i) => (
          <Scene key={s.id} id={s.id} index={i} eyebrow={s.eyebrow} ref={(el) => { refs.current[i] = el }}>
            {body[i]}
          </Scene>
        ))}
      </div>
    </MotionConfig>
  )
}
