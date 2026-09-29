export interface StockLevel {
  size: string
  quantity: number
}

export interface Product {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors: string[]
  search_tags: string[]
  image_file_path: string
  image_url: string
  price: number
  inventory: StockLevel[]
  total_stock: number
}

/** Chat search results that the Products page shows as a full grid. */
export interface PageResults {
  title: string
  query: string
  total: number
  products: Product[]
}

export interface ChatReply {
  reply: string
  products: Product[]
  page_results: PageResults | null
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatHistoryResponse {
  messages: {
    id: number
    role: 'user' | 'assistant'
    content: string
    products: Product[]
    page_results: PageResults | null
    created_at: string
  }[]
}

/** What the customer is looking at, sent with every chat message so "this" can be resolved. */
export interface PageContext {
  path: string
  page_type: 'home' | 'products' | 'chat_results' | 'product' | 'about' | 'login' | 'create_account' | 'other'
  product_id?: string
  category?: string
  search?: string
  results_title?: string
  results_count?: number
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  products?: Product[]
  pageResults?: PageResults
  error?: boolean
}

export interface User {
  id: number
  email: string
  name: string
  first_name: string | null
  last_name: string | null
  created_at: string
}

export interface AuthResponse {
  user: User
}
