import { useCallback, useEffect, useRef } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ProductView from './ProductView.tsx'

/** Product details floating over the shaded previous page; closing returns to that page. */
export default function ProductModal() {
  const { productId = '' } = useParams()
  const navigate = useNavigate()
  const closeRef = useRef<HTMLButtonElement>(null)
  const close = useCallback(() => navigate(-1), [navigate])

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
    }
    document.addEventListener('keydown', onKey)
    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    closeRef.current?.focus()
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = previousOverflow
    }
  }, [close])

  return (
    <div
      className="modal-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) close()
      }}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-label="Product details">
        <button ref={closeRef} type="button" className="modal-close" onClick={close} aria-label="Close product details">
          ×
        </button>
        <ProductView productId={productId} />
      </div>
    </div>
  )
}
