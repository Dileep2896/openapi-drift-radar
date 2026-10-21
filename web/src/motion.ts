// Motion tokens (PLAN.md §7): transform + opacity only, one easing curve, 0.4-0.8s, 60-90ms stagger.
export const ease = [0.22, 1, 0.36, 1] as const
export const duration = { fast: 0.4, normal: 0.6, slow: 0.8 } as const
export const stagger = 0.07
export const distance = { sm: 8, md: 16, lg: 28 } as const
export const springs = { count: { type: 'spring', stiffness: 60, damping: 18 } } as const

export const transition = (d: number = duration.normal, delay = 0) => ({ duration: d, delay, ease })
