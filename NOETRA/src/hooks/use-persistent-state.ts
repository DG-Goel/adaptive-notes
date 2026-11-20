import { useCallback, useState } from 'react'

/**
 * `useState` that mirrors its value into browser storage.
 *
 * Reading and writing both tolerate a hostile environment (private mode,
 * disabled storage, quota errors, hand-edited values), in which case the hook
 * simply behaves like ordinary component state. No server persistence is
 * implied anywhere — this only remembers reading preferences on the device.
 */
export function usePersistentState<T>(key: string, initial: T): [T, (value: T | ((prev: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => {
    if (typeof window === 'undefined') return initial
    try {
      const stored = window.localStorage.getItem(key)
      return stored === null ? initial : (JSON.parse(stored) as T)
    } catch {
      return initial
    }
  })

  const update = useCallback(
    (next: T | ((prev: T) => T)) => {
      setValue((prev) => {
        const resolved = typeof next === 'function' ? (next as (p: T) => T)(prev) : next
        try {
          window.localStorage.setItem(key, JSON.stringify(resolved))
        } catch {
          // Storage unavailable or full: the value still lives in React state.
        }
        return resolved
      })
    },
    [key],
  )

  return [value, update]
}
