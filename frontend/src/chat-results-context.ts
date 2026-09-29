import { createContext, useContext } from 'react'
import type { PageResults } from './types.ts'

/** URL that tells the Products page to show the chat's results instead of the full menu. */
export const CHAT_RESULTS_PATH = '/products?results=chat'

export interface ChatResultsContextValue {
  results: PageResults | null
  setResults: (results: PageResults | null) => void
}

export const ChatResultsContext = createContext<ChatResultsContextValue | null>(null)

export function useChatResults(): ChatResultsContextValue {
  const ctx = useContext(ChatResultsContext)
  if (!ctx) throw new Error('useChatResults must be used inside <ChatResultsProvider>')
  return ctx
}
