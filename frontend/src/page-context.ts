import type { PageContext, PageResults } from './types.ts'

const SIMPLE_PAGES: Record<string, PageContext['page_type']> = {
  '/': 'home',
  '/about': 'about',
  '/login': 'login',
  '/create-account': 'create_account',
}

/** Describe the current page for the shop assistant (sent with each chat message). */
export function buildPageContext(
  location: { pathname: string; search: string },
  chatResults: PageResults | null,
): PageContext {
  const { pathname, search } = location
  const path = pathname + search
  const params = new URLSearchParams(search)

  // The product pop-up and the full product page share the /products/<id> URL.
  const productMatch = pathname.match(/^\/products\/([^/]+)$/)
  if (productMatch) {
    return { path, page_type: 'product', product_id: decodeURIComponent(productMatch[1]) }
  }
  if (pathname === '/products') {
    if (params.get('results') === 'chat' && chatResults) {
      return {
        path,
        page_type: 'chat_results',
        results_title: chatResults.title,
        results_count: chatResults.total,
      }
    }
    return {
      path,
      page_type: 'products',
      category: params.get('category') || undefined,
      search: params.get('q') || undefined,
    }
  }
  return { path, page_type: SIMPLE_PAGES[pathname] ?? 'other' }
}
