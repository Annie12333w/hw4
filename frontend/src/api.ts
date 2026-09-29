import type { AuthResponse, ChatHistoryResponse, ChatReply, ChatTurn, PageContext, Product } from './types.ts'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    let detail = `Request failed (${res.status})`
    try {
      const body = await res.json()
      if (typeof body.detail === 'string') detail = body.detail
    } catch {
      // Response was not JSON; keep the generic message.
    }
    throw new ApiError(res.status, detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export function getProducts(query?: string): Promise<Product[]> {
  const params = query ? `?q=${encodeURIComponent(query)}` : ''
  return request<Product[]>(`/api/products${params}`)
}

export function getProduct(productId: string): Promise<Product> {
  return request<Product>(`/api/products/${encodeURIComponent(productId)}`)
}

export function sendChatMessage(message: string, history: ChatTurn[], pageContext: PageContext): Promise<ChatReply> {
  return request<ChatReply>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, history, page_context: pageContext }),
  })
}

export function getChatHistory(): Promise<ChatHistoryResponse> {
  return request<ChatHistoryResponse>('/api/chat/history')
}

export function clearChatHistory(): Promise<void> {
  return request<void>('/api/chat/history', { method: 'DELETE' })
}

export function logIn(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function createAccount(details: {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(details),
  })
}

export function getCurrentUser(): Promise<AuthResponse> {
  return request<AuthResponse>('/api/auth/me')
}

export function logOut(): Promise<void> {
  return request<void>('/api/auth/logout', { method: 'POST' })
}

export function authErrorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message
  return 'We could not reach the shop server. Please try again in a moment.'
}
