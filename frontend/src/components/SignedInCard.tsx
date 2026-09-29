import { Link } from 'react-router-dom'
import { useAuth } from '../auth-context.ts'
import type { User } from '../types.ts'
import AuthLayout from './AuthLayout.tsx'

/** Shown on the Log In / Create Account pages when someone is already signed in. */
export default function SignedInCard({ user, heading }: { user: User; heading: string }) {
  const { logOut } = useAuth()
  return (
    <AuthLayout>
      <div className="auth-card">
        <h1>{heading}</h1>
        <p className="form-success">
          You&apos;re logged in as <strong>{user.first_name ?? user.name}</strong> ({user.email}).
        </p>
        <Link to="/products" className="btn btn-primary btn-block">
          Start Shopping
        </Link>
        <button type="button" className="btn btn-outline btn-block" onClick={() => void logOut()}>
          Log Out
        </button>
      </div>
    </AuthLayout>
  )
}
