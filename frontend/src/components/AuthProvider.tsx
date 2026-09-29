import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { getCurrentUser, logOut as logOutRequest } from '../api.ts'
import { AuthContext } from '../auth-context.ts'
import type { User } from '../types.ts'

/** Restores the logged-in user from the session cookie and shares it with the app. */
export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    getCurrentUser()
      .then(({ user }) => active && setUser(user))
      .catch(() => {
        // Not logged in (401) or server unavailable: stay logged out.
      })
      .finally(() => active && setLoading(false))
    return () => {
      active = false
    }
  }, [])

  const logOut = useCallback(async () => {
    try {
      await logOutRequest()
    } finally {
      setUser(null)
    }
  }, [])

  const value = useMemo(() => ({ user, loading, setUser, logOut }), [user, loading, logOut])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
