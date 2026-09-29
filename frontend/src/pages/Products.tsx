import { useNavigate, useSearchParams } from 'react-router-dom'
import Banner from '../components/Banner.tsx'
import ProductCard from '../components/ProductCard.tsx'
import { useChatResults } from '../chat-results-context.ts'
import { CATEGORIES, categoryOf } from '../format.ts'
import { useProducts } from '../hooks.ts'

export default function Products() {
  const products = useProducts()
  const [params, setParams] = useSearchParams()
  const { results, setResults } = useChatResults()
  const navigate = useNavigate()
  const category = params.get('category') ?? ''
  const search = params.get('q') ?? ''
  const showChatResults = params.get('results') === 'chat' && results !== null

  function returnToFullMenu() {
    setResults(null)
    navigate('/products')
  }

  if (showChatResults) {
    return (
      <section className="container section">
        <div className="chat-results-banner">
          <div>
            <p className="eyebrow">From Your Chat</p>
            <h1>{results.title}</h1>
            <p className="muted">
              {results.total} {results.total === 1 ? 'item matches' : 'items match'} &ldquo;{results.query}&rdquo;
            </p>
          </div>
          <button type="button" className="btn btn-outline" onClick={returnToFullMenu}>
            ← Return to Full Menu
          </button>
        </div>
        <div className="product-grid">
          {results.products.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>
    )
  }

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(params)
    next.delete('results')
    if (value) next.set(key, value)
    else next.delete(key)
    setParams(next, { replace: true })
  }

  const words = search.toLowerCase().split(/\s+/).filter(Boolean)
  const visible =
    products.status === 'ready'
      ? products.data.filter((p) => {
          if (category && categoryOf(p.garment_type) !== category) return false
          const haystack = [p.name, p.garment_type, p.description, ...p.colors, ...p.search_tags]
            .join(' ')
            .toLowerCase()
          return words.every((w) => haystack.includes(w))
        })
      : []

  return (
    <>
    <Banner image="/images/friends-walking.jpg" alt="Friends in Yale tees walking together" focus="60% 30%" size="slim">
      <p className="eyebrow">The Collection</p>
      <h1>{category || 'All Products'}</h1>
    </Banner>
    <section className="container section">
      <div className="filters">
        <input
          type="search"
          className="search-input"
          placeholder="Search by name, color, sport, college…"
          value={search}
          onChange={(e) => updateParam('q', e.target.value)}
          aria-label="Search products"
        />
        <div className="chips" role="group" aria-label="Filter by category">
          <button type="button" className={`chip${category === '' ? ' active' : ''}`} onClick={() => updateParam('category', '')}>
            All
          </button>
          {CATEGORIES.map((c) => (
            <button
              key={c}
              type="button"
              className={`chip${category === c ? ' active' : ''}`}
              onClick={() => updateParam('category', c)}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {products.status === 'loading' && <p className="muted">Loading products…</p>}
      {products.status === 'error' && (
        <p className="error-text">We couldn&apos;t load products ({products.message}). Is the backend running?</p>
      )}
      {products.status === 'ready' && (
        <>
          <p className="muted result-count">
            {visible.length} {visible.length === 1 ? 'Item' : 'Items'}
          </p>
          {visible.length === 0 ? (
            <p>No products match your search. Try a different word or category.</p>
          ) : (
            <div className="product-grid">
              {visible.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
    </>
  )
}
