import { createContext, useContext } from 'react'
import type { User } from './types.ts'

export interface AuthContextValue {
  user: User | null
  loading: boolean
  setUser: (user: User | null) => void
  logOut: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
