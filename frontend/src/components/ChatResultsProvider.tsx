import { useCallback, useMemo, useState, type ReactNode } from 'react'
import { ChatResultsContext } from '../chat-results-context.ts'
import type { PageResults } from '../types.ts'

const STORAGE_KEY = 'cc-chat-results'

function loadStored(): PageResults | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as PageResults) : null
  } catch {
    return null
  }
}

/** Holds the latest chat search results; kept in sessionStorage so a refresh doesn't lose them. */
export default function ChatResultsProvider({ children }: { children: ReactNode }) {
  const [results, setResultsState] = useState<PageResults | null>(loadStored)

  const setResults = useCallback((next: PageResults | null) => {
    setResultsState(next)
    try {
      if (next) sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
      else sessionStorage.removeItem(STORAGE_KEY)
    } catch {
      // Storage unavailable (private mode); results still work for this page view.
    }
  }, [])

  const value = useMemo(() => ({ results, setResults }), [results, setResults])
  return <ChatResultsContext.Provider value={value}>{children}</ChatResultsContext.Provider>
}
