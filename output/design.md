# Campus Customs — Design Refresh (Problem 10)

**Goal:** make the shop feel like a quiet-luxury fashion site (modeled on jpress.com) so shoppers trust it, stay longer, and buy.

| Change | What we did | Why it helps customers stay and buy |
|---|---|---|
| **Centered-logo menu** | Home · Products · About Us on the left, the Campus Customs crest and wordmark centered, Log In · Create Account on the right. Small uppercase, widely spaced labels with a thin underline on hover and on the current page. | Mirrors premium retailers, so the store looks established and trustworthy. Shopping links and account links sit in predictable places, so there's less hunting. |
| **Bigger, wider product grid** | Up to 1,680 px wide with narrow side margins; 4 columns on desktop (3 on tablets, 2 on phones); tall 4:5 image frames. | The garment becomes the hero: shoppers see more detail and more items per screen, which leads to more product views and more chances to find "the one". |
| **Invisible card borders** | No borders, boxes, or shadows. Each product sits on a soft stone backdrop with its name, price, and a one-line description below; the image zooms slightly on hover. | Removes visual clutter so the products read as a curated collection, not a spreadsheet. The hover zoom invites clicks. |
| **Quiet-luxury palette and type** | Ivory background, ink-black text, one deep-navy accent; Cormorant Garamond serif headings with Jost sans-serif body text; square buttons and thin dividing lines instead of rounded "app" styling. | Calm, consistent styling signals quality and justifies the price points ($32–$98). A restrained palette keeps attention on the merchandise. |
| **Collegiate lifestyle banners** | Six campus photos (friends on a leafy path, students on steps, a study session, a hoodie portrait, a Yale mug, friends walking) used as the home hero, full-width banners, image-and-text sections, the Products header, the About page, and the login/sign-up pages. Every photo is cropped to fit (never stretched); the store logo was cropped out of one banner. | Shows the product *being worn by students like them*. That emotional, "this is my campus" context builds belonging and makes the gear feel like part of the Yale experience, not just a T-shirt. |
| **Editorial storytelling on Home** | Hero, then a short brand promise, New Arrivals, "Made for Late Nights and Early Classes" (crewnecks), a "Tailgate Ready" banner (T-shirts), Shop by Category, "Built for New England Autumns" (hoodies), and a three-point value row. Each block links to a filtered shop page. | Guides visitors down the page with a reason to click at each stop (study, game day, cold weather), turning browsing into shopping paths. |
| **Photo login/sign-up pages** | Split layout: a campus photo on one side, a clean form with underline-style fields on the other. | Makes creating an account feel inviting rather than bureaucratic, and more accounts means saved chat memory and repeat visits. |

**Unchanged on purpose:** the product pop-up (you keep your scroll position), "Return to Full Menu" after chat searches, and the chat assistant. They now match the new styling.

**Files:** `index.css` (full rewrite), `NavBar.tsx`, new `Banner.tsx` / `Editorial.tsx` / `AuthLayout.tsx`, `Home.tsx`, `About.tsx`, `Products.tsx`, the Log In / Create Account pages, `public/images/*.jpg`, and the fonts in `index.html`.

**Checked in the browser (1440 px wide):**
- Menu: links on the left, logo centered, account links on the right.
- Products: 4 per row, no card borders, tall 4:5 image frames.
- Photos: all banners use `object-fit: cover`, so they are cropped, never stretched.
- The product pop-up and the Log In page still work.
- `tsc` and `lint` pass.
