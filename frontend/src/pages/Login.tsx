import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { authErrorMessage, logIn } from '../api.ts'
import { useAuth } from '../auth-context.ts'
import AuthLayout from '../components/AuthLayout.tsx'
import SignedInCard from '../components/SignedInCard.tsx'

export default function Login() {
  const { user, setUser } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (user) return <SignedInCard user={user} heading="Welcome Back!" />

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)
    try {
      const { user } = await logIn(email.trim(), password)
      setPassword('')
      setUser(user)
    } catch (err) {
      setError(authErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Log In</h1>
        <p className="muted">Welcome back! Sign in to your Campus Customs account.</p>

        <label>
          Email
          <input
            name="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Logging In…' : 'Log In'}
        </button>
        <p className="muted center small">
          New to Campus Customs? <Link to="/create-account">Create Account</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
