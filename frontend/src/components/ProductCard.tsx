import { Link } from 'react-router-dom'
import type { Product } from '../types.ts'
import { formatPrice, shortDescription } from '../format.ts'
import { useProductModalLink } from '../hooks.ts'

export default function ProductCard({ product }: { product: Product }) {
  const modalLink = useProductModalLink()
  return (
    <Link to={`/products/${product.product_id}`} {...modalLink} className="product-card">
      <div className="product-card-image">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        {product.total_stock === 0 && <span className="badge">Sold Out</span>}
      </div>
      <div className="product-card-body">
        <h3>{product.name}</h3>
        <p className="price">{formatPrice(product.price)}</p>
        <p className="muted">{shortDescription(product.description)}</p>
      </div>
    </Link>
  )
}
