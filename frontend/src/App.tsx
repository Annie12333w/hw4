import { useEffect } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation, useNavigationType } from 'react-router-dom'
import NavBar from './components/NavBar.tsx'
import Footer from './components/Footer.tsx'
import ChatWidget from './components/ChatWidget.tsx'
import ProductModal from './components/ProductModal.tsx'
import type { ModalState } from './hooks.ts'
import Home from './pages/Home.tsx'
import Products from './pages/Products.tsx'
import ProductDetail from './pages/ProductDetail.tsx'
import About from './pages/About.tsx'
import Login from './pages/Login.tsx'
import CreateAccount from './pages/CreateAccount.tsx'

function ScrollToTop({ modalOpen }: { modalOpen: boolean }) {
  const { pathname } = useLocation()
  const navigationType = useNavigationType()
  useEffect(() => {
    // Keep the background page in place when opening or closing the product modal.
    if (navigationType === 'PUSH' && !modalOpen) window.scrollTo(0, 0)
  }, [pathname, navigationType, modalOpen])
  return null
}

function NotFound() {
  return (
    <section className="container narrow center">
      <h1>Page Not Found</h1>
      <p>We couldn&apos;t find that page. It may have moved, or the link might be out of date.</p>
      <Link to="/products" className="btn btn-primary">
        Shop All Products
      </Link>
    </section>
  )
}

function AppRoutes() {
  const location = useLocation()
  const background = (location.state as ModalState | null)?.backgroundLocation

  return (
    <>
      <ScrollToTop modalOpen={Boolean(background)} />
      <NavBar />
      <main className="site-main">
        <Routes location={background ?? location}>
          <Route path="/" element={<Home />} />
          <Route path="/products" element={<Products />} />
          <Route path="/products/:productId" element={<ProductDetail />} />
          <Route path="/about" element={<About />} />
          <Route path="/login" element={<Login />} />
          <Route path="/create-account" element={<CreateAccount />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
      {background && (
        <Routes>
          <Route path="/products/:productId" element={<ProductModal />} />
        </Routes>
      )}
      <ChatWidget />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
