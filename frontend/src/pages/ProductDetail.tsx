import { Link, useParams } from 'react-router-dom'
import ProductView from '../components/ProductView.tsx'

/** Full-page fallback, used when a product URL is opened directly or refreshed. */
export default function ProductDetail() {
  const { productId = '' } = useParams()
  return (
    <section className="container section">
      <nav className="breadcrumb" aria-label="Breadcrumb">
        <Link to="/products">← Back to Products</Link>
      </nav>
      <ProductView productId={productId} />
    </section>
  )
}
