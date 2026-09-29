import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth-context.ts'
import Logo from './Logo.tsx'

const MAIN_LINKS = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products', end: false },
  { to: '/about', label: 'About Us', end: false },
]

const linkClass = ({ isActive }: { isActive: boolean }) => (isActive ? 'nav-link active' : 'nav-link')

/** Three-part header: shop links on the left, centered logo, account links on the right. */
export default function NavBar() {
  const { user, loading, logOut } = useAuth()
  const navigate = useNavigate()

  async function handleLogOut() {
    await logOut()
    navigate('/')
  }

  return (
    <header className="site-header">
      <div className="announcement">Officially Licensed Yale Apparel · 57 Broadway, New Haven</div>
      <nav className="navbar" aria-label="Main">
        <ul className="nav-links nav-left">
          {MAIN_LINKS.map((link) => (
            <li key={link.to}>
              <NavLink to={link.to} end={link.end} className={linkClass}>
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <Link to="/" className="brand" aria-label="Campus Customs home">
          <Logo size={40} />
          <span className="brand-text">
            <strong>Campus Customs</strong>
            <small>New Haven · Connecticut</small>
          </span>
        </Link>

        <div className="nav-links nav-right">
          {user ? (
            <>
              <span className="nav-greeting">Hi, {user.first_name ?? user.name}</span>
              <button type="button" className="nav-link nav-button" onClick={handleLogOut}>
                Log Out
              </button>
            </>
          ) : (
            !loading && (
              <>
                <NavLink to="/login" className={linkClass}>
                  Log In
                </NavLink>
                <NavLink to="/create-account" className={linkClass}>
                  Create Account
                </NavLink>
              </>
            )
          )}
        </div>
      </nav>
    </header>
  )
}
