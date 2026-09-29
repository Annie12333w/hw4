export const CATEGORIES = [
  'Hoodies',
  'Crewnecks & Sweatshirts',
  'T-Shirts',
  'Quarter-Zips',
  'Jackets & Fleece',
  'Long Sleeve',
] as const

export type Category = (typeof CATEGORIES)[number]

/** The database uses many spellings of garment_type; group them into shop categories. */
export function categoryOf(garmentType: string): Category {
  const t = garmentType.toLowerCase()
  if (t.includes('t-shirt')) return 'T-Shirts'
  if (t.includes('quarter-zip')) return 'Quarter-Zips'
  if (t.includes('jacket')) return 'Jackets & Fleece'
  if (t.includes('hood')) return 'Hoodies'
  if (t.includes('long-sleeve')) return 'Long Sleeve'
  return 'Crewnecks & Sweatshirts'
}

const currency = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

export function formatPrice(price: number): string {
  return currency.format(price)
}

/** First sentence of the description, trimmed to fit on a product card. */
export function shortDescription(text: string, max = 90): string {
  const firstSentence = text.split(/(?<=\.)\s/)[0]
  const base = firstSentence.length <= max ? firstSentence : text
  if (base.length <= max) return base
  const cut = base.lastIndexOf(' ', max)
  return base.slice(0, cut > 0 ? cut : max).replace(/[,;:]$/, '') + '…'
}

export function titleCase(text: string): string {
  return text.replace(/\b([a-z])/g, (_, c: string) => c.toUpperCase())
}

export function stockLabel(quantity: number): string {
  if (quantity === 0) return 'Sold Out'
  if (quantity <= 5) return `Only ${quantity} Left`
  return `${quantity} in Stock`
}
