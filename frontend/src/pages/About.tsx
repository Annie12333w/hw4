import { Link } from 'react-router-dom'
import Banner from '../components/Banner.tsx'
import Editorial from '../components/Editorial.tsx'

export default function About() {
  return (
    <>
      <Banner image="/images/campus-steps.jpg" alt="Students talking on campus steps" focus="50% 40%" size="large">
        <p className="eyebrow">About Us</p>
        <h1>New Haven&apos;s Home for Yale Gear</h1>
      </Banner>

      <section className="container section narrow prose">
        <h2>Who We Are</h2>
        <p>
          Campus Customs is a shop for officially licensed Yale apparel and gifts. We work out of 57 Broadway in New
          Haven, a few steps from campus. That means we see the same crowd you do: first-years hunting for their first
          hoodie, seniors picking up something to remember the place by, and families visiting for the weekend.
        </p>

        <h2>What We Carry</h2>
        <p>
          Our racks cover the whole Yale community. You&apos;ll find classic wordmark hoodies and crewnecks, pieces
          for each of the residential colleges, gear for more than twenty varsity sports, and designs for the graduate
          and professional schools. We also stock a family line, so Mom, Dad, Grandma, and the rest of the cheering
          section can match you on game day.
        </p>

        <h2>What We Care About</h2>
        <ul>
          <li>
            <strong>Officially licensed:</strong> every logo and crest is licensed, so you know you&apos;re getting
            the real thing.
          </li>
          <li>
            <strong>Comfort first:</strong> we choose soft fleece, relaxed tees, and easy layers that hold up to New
            England winters.
          </li>
          <li>
            <strong>Real help:</strong> not sure about a size or whether something is in stock? Our chat assistant
            checks the shop&apos;s live inventory for you.
          </li>
        </ul>
      </section>

      <Editorial image="/images/morning-mug.jpg" alt="Hands holding a Yale mug" focus="50% 55%" reverse>
        <p className="eyebrow">Visit the Shop</p>
        <h2>Come Say Hello</h2>
        <p>
          Stop by 57 Broadway, New Haven, CT 06511, for a coffee-in-hand browse, or shop online any time.
        </p>
        <Link to="/products" className="btn btn-primary">
          Shop the Collection
        </Link>
      </Editorial>
    </>
  )
}
