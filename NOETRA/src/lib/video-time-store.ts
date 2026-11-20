/**
 * Tiny external store for playback position.
 *
 * Playback time updates far more often than the rest of the player state, so it
 * lives outside React and is read through `useSyncExternalStore` by only the few
 * components that need it (timeline, chapters, transcript). Updates are
 * throttled so consumers re-render at most ~10×/second.
 */

export interface VideoTimeStore {
  subscribe(listener: () => void): () => void
  getSnapshot(): number
  /** Latest observed time, including any pending throttled value. */
  peek(): number
  push(time: number, immediate?: boolean): void
  reset(): void
  dispose(): void
}

const DEFAULT_INTERVAL_MS = 100

export function createVideoTimeStore(
  intervalMs: number = DEFAULT_INTERVAL_MS,
): VideoTimeStore {
  let emitted = 0
  let pending = 0
  let lastEmit = 0
  let timer: ReturnType<typeof setTimeout> | null = null
  const listeners = new Set<() => void>()

  const notify = () => {
    listeners.forEach((listener) => listener())
  }

  const flush = () => {
    if (timer !== null) {
      clearTimeout(timer)
      timer = null
    }
    lastEmit = Date.now()
    if (pending !== emitted) {
      emitted = pending
      notify()
    }
  }

  return {
    subscribe(listener) {
      listeners.add(listener)
      return () => {
        listeners.delete(listener)
      }
    },
    getSnapshot() {
      return emitted
    },
    peek() {
      return pending
    },
    push(time, immediate = false) {
      if (!Number.isFinite(time)) return
      pending = time
      if (immediate) {
        flush()
        return
      }
      const elapsed = Date.now() - lastEmit
      if (elapsed >= intervalMs) {
        flush()
        return
      }
      if (timer === null) {
        timer = setTimeout(flush, intervalMs - elapsed)
      }
    },
    reset() {
      pending = 0
      flush()
    },
    dispose() {
      if (timer !== null) {
        clearTimeout(timer)
        timer = null
      }
      listeners.clear()
    },
  }
}
