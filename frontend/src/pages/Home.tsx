import { Link } from 'react-router-dom'
import Banner from '../components/Banner.tsx'
import Editorial from '../components/Editorial.tsx'
import ProductCard from '../components/ProductCard.tsx'
import { CATEGORIES, categoryOf } from '../format.ts'
import { useProducts } from '../hooks.ts'

const FEATURED_IDS = [
  'hype-and-vice-yale-university-premium-crewneck',
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'yale-mom-crewneck',
]

export default function Home() {
  const products = useProducts()
  const all = products.status === 'ready' ? products.data : []
  const featured = FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter((p) => p !== undefined)
  const categoryTiles = CATEGORIES.map((category) => ({
    category,
    cover: all.find((p) => categoryOf(p.garment_type) === category),
  }))

  return (
    <>
      <Banner image="/images/campus-walk.jpg" alt="Friends walking to class on a leafy campus path" focus="50% 40%" size="hero">
        <p className="eyebrow">Campus Customs · New Haven</p>
        <h1>Wear Your Bulldog Pride Every Day</h1>
        <p className="banner-copy">
          Soft hoodies, easy crewnecks, and game-day tees in true Yale blue, all officially licensed.
        </p>
        <div className="banner-actions">
          <Link to="/products" className="btn btn-light">
            Shop the Collection
          </Link>
          <Link to="/about" className="text-link light">
            Our Story
          </Link>
        </div>
      </Banner>

      <section className="intro narrow center">
        <p className="eyebrow">Our Promise</p>
        <p className="intro-copy">
          Picked for the people who call New Haven home, even if only for four years: first-years, seniors, alumni,
          and every proud parent in the stands.
        </p>
      </section>

      <section className="container section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Just Landed</p>
            <h2>New Arrivals</h2>
          </div>
          <Link to="/products" className="text-link">
            View All
          </Link>
        </div>
        {products.status === 'loading' && <p className="muted">Loading new arrivals…</p>}
        {products.status === 'error' && <p className="error-text">We couldn&apos;t load products right now.</p>}
        <div className="product-grid">
          {featured.map((p) => (
            <ProductCard key={p.product_id} product={p} />
          ))}
        </div>
      </section>

      <Editorial image="/images/study-session.jpg" alt="Two students studying together with a Yale mug" focus="50% 45%">
        <p className="eyebrow">Study Hall Staples</p>
        <h2>Made for Late Nights and Early Classes</h2>
        <p>
          Crewnecks and quarter-zips that go from the library to the dining hall without a second thought. Soft,
          warm, and easy to live in.
        </p>
        <Link to="/products?category=Crewnecks%20%26%20Sweatshirts" className="text-link">
          Shop Crewnecks
        </Link>
      </Editorial>

      <Banner image="/images/campus-steps.jpg" alt="Students gathered on campus steps" focus="50% 35%" size="large" align="center">
        <p className="eyebrow">Tailgate Ready</p>
        <h2>Dressed for The Game, Comfortable All Season</h2>
        <Link to="/products?category=T-Shirts" className="btn btn-light">
          Shop T-Shirts
        </Link>
      </Banner>

      <section className="container section">
        <div className="section-head">
          <div>
            <p className="eyebrow">Find Your Fit</p>
            <h2>Shop by Category</h2>
          </div>
        </div>
        <div className="category-grid">
          {categoryTiles.map(({ category, cover }) => (
            <Link key={category} to={`/products?category=${encodeURIComponent(category)}`} className="category-tile">
              <div className="category-image">{cover && <img src={cover.image_url} alt="" loading="lazy" />}</div>
              <span>{category}</span>
            </Link>
          ))}
        </div>
      </section>

      <Editorial
        image="/images/hoodie-portrait.jpg"
        alt="Student in a navy Yale zip hoodie"
        focus="50% 30%"
        reverse
      >
        <p className="eyebrow">Layer Up</p>
        <h2>Built for New England Autumns</h2>
        <p>
          Heavyweight hoodies, fleece jackets, and full-zips for crisp walks across Old Campus and cold nights at the
          rink.
        </p>
        <Link to="/products?category=Hoodies" className="text-link">
          Shop Hoodies
        </Link>
      </Editorial>

      <section className="container section">
        <div className="info-row">
          <div className="info-card">
            <h3>For the Whole Family</h3>
            <p>Mom, Dad, Grandpa, Aunt, and more. There&apos;s a Yale piece for everyone cheering you on.</p>
          </div>
          <div className="info-card">
            <h3>Colleges, Schools &amp; Teams</h3>
            <p>Show off your residential college, your professional school, or the varsity team you never miss.</p>
          </div>
          <div className="info-card">
            <h3>Personal Shopping, Online</h3>
            <p>Open the chat in the corner to ask about sizes, prices, and what&apos;s in stock today.</p>
          </div>
        </div>
      </section>
    </>
  )
}
