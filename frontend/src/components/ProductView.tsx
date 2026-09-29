import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ApiError, getProduct } from '../api.ts'
import { formatPrice, stockLabel, titleCase } from '../format.ts'
import type { LoadState } from '../hooks.ts'
import type { Product } from '../types.ts'

/** Full product details: large image on the left, info, sizes, and stock on the right. */
export default function ProductView({ productId }: { productId: string }) {
  const [state, setState] = useState<LoadState<Product>>({ status: 'loading' })
  const [selectedSize, setSelectedSize] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    setState({ status: 'loading' })
    setSelectedSize(null)
    getProduct(productId)
      .then((data) => active && setState({ status: 'ready', data }))
      .catch((err: unknown) => {
        if (!active) return
        const message =
          err instanceof ApiError && err.status === 404
            ? "We couldn't find that product."
            : 'We could not load this product right now.'
        setState({ status: 'error', message })
      })
    return () => {
      active = false
    }
  }, [productId])

  if (state.status === 'loading') {
    return <p className="muted detail-loading">Loading product…</p>
  }
  if (state.status === 'error') {
    return (
      <div className="narrow center detail-loading">
        <h1>Product Unavailable</h1>
        <p>{state.message}</p>
        <Link to="/products" className="btn btn-primary">
          Back to Products
        </Link>
      </div>
    )
  }

  const product = state.data
  const selected = product.inventory.find((s) => s.size === selectedSize)

  return (
    <div className="detail">
      <div className="detail-image">
        <img src={product.image_url} alt={product.name} />
      </div>

      <div className="detail-info">
        <p className="eyebrow">{titleCase(product.garment_type)}</p>
        <h1>{product.name}</h1>
        <p className="detail-price">{formatPrice(product.price)}</p>
        <p className="detail-description">{product.description}</p>

        <h2 className="detail-label">Colors</h2>
        <ul className="color-list">
          {product.colors.map((c) => (
            <li key={c}>{titleCase(c)}</li>
          ))}
        </ul>

        <h2 className="detail-label">Sizes &amp; Stock</h2>
        {product.inventory.length === 0 ? (
          <p className="muted">Size information is not available for this item.</p>
        ) : (
          <>
            <div className="size-grid" role="group" aria-label="Choose a size">
              {product.inventory.map((s) => (
                <button
                  key={s.size}
                  type="button"
                  className={`size-option${selectedSize === s.size ? ' active' : ''}${s.quantity === 0 ? ' sold-out' : ''}`}
                  onClick={() => setSelectedSize(s.size)}
                  aria-pressed={selectedSize === s.size}
                >
                  <strong>{s.size}</strong>
                  <small>{stockLabel(s.quantity)}</small>
                </button>
              ))}
            </div>
            <p className="stock-note">
              {selected
                ? selected.quantity === 0
                  ? `Size ${selected.size} is sold out right now.`
                  : `Size ${selected.size}: ${selected.quantity} available.`
                : `${product.total_stock} available across all sizes. Select a size to check stock.`}
            </p>
          </>
        )}

        <p className="muted small">Questions about fit or availability? Ask our assistant using the chat in the corner.</p>
      </div>
    </div>
  )
}
