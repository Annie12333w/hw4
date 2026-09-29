import type { ReactNode } from 'react'

/** Log In / Create Account layout: a campus photo on one side, the form on the other. */
export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <section className="auth-layout">
      <div className="auth-visual">
        <img src="/images/hoodie-portrait.jpg" alt="Student wearing a navy Yale zip hoodie" style={{ objectPosition: '50% 30%' }} />
      </div>
      <div className="auth-panel">{children}</div>
    </section>
  )
}
