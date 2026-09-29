import { Link } from 'react-router-dom'
import Logo from './Logo.tsx'

export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-grid">
        <div>
          <div className="footer-brand">
            <Logo size={40} inverted />
            <h4>Campus Customs</h4>
          </div>
          <p>Officially licensed Yale apparel for students, alumni, families, and fans.</p>
        </div>
        <div>
          <h4>Shop</h4>
          <ul>
            <li>
              <Link to="/products">All Products</Link>
            </li>
            <li>
              <Link to="/products?category=Hoodies">Hoodies</Link>
            </li>
            <li>
              <Link to="/products?category=T-Shirts">T-Shirts</Link>
            </li>
          </ul>
        </div>
        <div>
          <h4>Visit Us</h4>
          <p>
            57 Broadway
            <br />
            New Haven, CT 06511
          </p>
        </div>
        <div>
          <h4>Account</h4>
          <ul>
            <li>
              <Link to="/login">Log In</Link>
            </li>
            <li>
              <Link to="/create-account">Create Account</Link>
            </li>
            <li>
              <Link to="/about">About Us</Link>
            </li>
          </ul>
        </div>
      </div>
      <p className="footer-copy">© {new Date().getFullYear()} Campus Customs · 57 Broadway, New Haven</p>
    </footer>
  )
}
