import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { authErrorMessage, createAccount } from '../api.ts'
import { useAuth } from '../auth-context.ts'
import AuthLayout from '../components/AuthLayout.tsx'
import SignedInCard from '../components/SignedInCard.tsx'

const MIN_PASSWORD = 8
const EMPTY_FORM = { first_name: '', last_name: '', email: '', password: '', confirm: '' }

export default function CreateAccount() {
  const { user, setUser } = useAuth()
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (user) return <SignedInCard user={user} heading="Account Ready!" />

  const update = (field: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((f) => ({ ...f, [field]: e.target.value }))

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (form.password.length < MIN_PASSWORD) {
      setError(`Password must be at least ${MIN_PASSWORD} characters.`)
      return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match.')
      return
    }
    setSubmitting(true)
    setError(null)
    try {
      const { user } = await createAccount({
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        password: form.password,
        confirm_password: form.confirm,
      })
      setForm(EMPTY_FORM)
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
        <h1>Create Account</h1>
        <p className="muted">Join Campus Customs to save your chats and get help finding the right fit.</p>

        <div className="form-row">
          <label>
            First Name
            <input name="first_name" autoComplete="given-name" required value={form.first_name} onChange={update('first_name')} />
          </label>
          <label>
            Last Name
            <input name="last_name" autoComplete="family-name" required value={form.last_name} onChange={update('last_name')} />
          </label>
        </div>
        <label>
          Email
          <input name="email" type="email" autoComplete="email" required value={form.email} onChange={update('email')} />
        </label>
        <label>
          Password
          <input
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={MIN_PASSWORD}
            value={form.password}
            onChange={update('password')}
          />
          <span className="field-hint">At least {MIN_PASSWORD} characters.</span>
        </label>
        <label>
          Confirm Password
          <input
            name="confirm_password"
            type="password"
            autoComplete="new-password"
            required
            value={form.confirm}
            onChange={update('confirm')}
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? 'Creating Account…' : 'Create Account'}
        </button>
        <p className="muted center small">
          Already have an account? <Link to="/login">Log In</Link>
        </p>
      </form>
    </AuthLayout>
  )
}
