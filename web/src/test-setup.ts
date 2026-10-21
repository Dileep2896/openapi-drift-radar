import '@testing-library/jest-dom/vitest'
import { afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'

// jsdom lacks these browser APIs that motion and the story page rely on.
class IO {
  observe() {}
  unobserve() {}
  disconnect() {}
  takeRecords() { return [] }
  root = null
  rootMargin = ''
  thresholds = []
}
;(globalThis as unknown as { IntersectionObserver: unknown }).IntersectionObserver = IO

export const motionPref = { reduced: false }
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: query.includes('prefers-reduced-motion') ? motionPref.reduced : false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})
Element.prototype.scrollIntoView = vi.fn()

afterEach(() => {
  cleanup()
  motionPref.reduced = false
})
