import { useEffect, useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ApiError, clearChatHistory, getChatHistory, sendChatMessage } from '../api.ts'
import { useAuth } from '../auth-context.ts'
import { CHAT_RESULTS_PATH, useChatResults } from '../chat-results-context.ts'
import { formatPrice } from '../format.ts'
import { useProductModalLink } from '../hooks.ts'
import { buildPageContext } from '../page-context.ts'
import type { ChatMessage, PageResults } from '../types.ts'

const HISTORY_TURNS = 12

function greeting(firstName?: string | null, returning = false): ChatMessage {
  const hello = firstName ? (returning ? `Welcome back, ${firstName}!` : `Hi ${firstName}!`) : 'Hi!'
  return {
    role: 'assistant',
    content: `${hello} I'm the Campus Customs assistant. Ask me about our Yale merch, prices, sizes, or what's in stock.`,
  }
}

/** Render **bold** spans; everything else stays plain text. */
function renderInline(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
  )
}

function ChatIcon() {
  return (
    <svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true">
      <path
        fill="currentColor"
        d="M4 3h16a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H8l-4.5 3.6A.9.9 0 0 1 2 20.9V5a2 2 0 0 1 2-2Zm3 6.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Z"
      />
    </svg>
  )
}

export default function ChatWidget() {
  const { user } = useAuth()
  const userId = user?.id
  const firstName = user?.first_name
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<ChatMessage[]>([greeting()])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const modalLink = useProductModalLink()
  const { results: chatResults, setResults } = useChatResults()
  const navigate = useNavigate()
  const location = useLocation()
  const pageContext = buildPageContext(location, chatResults)

  /** Put chat search results on the Products page as a full product grid. */
  function showOnPage(results: PageResults) {
    setResults(results)
    navigate(CHAT_RESULTS_PATH)
  }

  // Logged-in customers get their saved conversation back; guests start fresh (nothing is stored for them).
  useEffect(() => {
    let active = true
    if (userId === undefined) {
      setMessages([greeting()])
      return
    }
    getChatHistory()
      .then(({ messages: saved }) => {
        if (!active) return
        setMessages([
          greeting(firstName, saved.length > 0),
          ...saved.map((m) => ({
            role: m.role,
            content: m.content,
            products: m.products,
            pageResults: m.page_results ?? undefined,
          })),
        ])
      })
      .catch(() => active && setMessages([greeting(firstName)]))
    return () => {
      active = false
    }
  }, [userId, firstName])

  useEffect(() => {
    const list = listRef.current
    if (list) list.scrollTo({ top: list.scrollHeight, behavior: 'smooth' })
  }, [messages, sending, open])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  async function send() {
    const text = draft.trim()
    if (!text || sending) return
    // Guests: recent turns give the agent context. Logged in: the server reads history from the database instead.
    const history = user
      ? []
      : messages
          .slice(1)
          .filter((m) => !m.error)
          .slice(-HISTORY_TURNS)
          .map(({ role, content }) => ({ role, content }))
    setDraft('')
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setSending(true)
    try {
      const reply = await sendChatMessage(text, history, pageContext)
      const pageResults = reply.page_results ?? undefined
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: reply.reply, products: reply.products, pageResults },
      ])
      if (pageResults) showOnPage(pageResults)
    } catch (err) {
      const content =
        err instanceof ApiError && (err.status === 502 || err.status === 503)
          ? err.message
          : "Sorry, I couldn't reach the shop server just now. Please try again in a moment."
      setMessages((prev) => [...prev, { role: 'assistant', content, error: true }])
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  async function clearChat() {
    if (!window.confirm(user ? 'Delete your saved chat history?' : 'Start a new chat?')) return
    try {
      if (user) await clearChatHistory()
      setMessages([greeting(firstName)])
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: "Sorry, I couldn't clear your history just now.", error: true },
      ])
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      void send()
    }
  }

  const placeholder =
    pageContext.page_type === 'product' ? 'Ask about this item…' : 'Ask about hoodies, sizes, prices…'

  return (
    <div className="chat-widget">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <div>
              <strong>Campus Customs Assistant</strong>
              <small>{user ? 'Your Chat Is Saved to Your Account' : 'Guest Chat · Not Saved'}</small>
            </div>
            <div className="chat-header-actions">
              {messages.length > 1 && (
                <button type="button" className="chat-clear" onClick={() => void clearChat()}>
                  Clear Chat
                </button>
              )}
              <button type="button" className="chat-close" onClick={() => setOpen(false)} aria-label="Close chat">
                ×
              </button>
            </div>
          </header>

          <div className="chat-messages" ref={listRef} aria-live="polite">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-bubble ${msg.role}${msg.error ? ' error' : ''}`}>
                <p>{renderInline(msg.content)}</p>
                {msg.products && msg.products.length > 0 && (
                  <ul className="chat-products">
                    {msg.products.map((p) => (
                      <li key={p.product_id}>
                        <Link to={`/products/${p.product_id}`} {...modalLink}>
                          <img src={p.image_url} alt="" />
                          <span>
                            {p.name}
                            <small>{formatPrice(p.price)}</small>
                          </span>
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
                {msg.pageResults && (
                  <button
                    type="button"
                    className="btn btn-outline btn-sm chat-view-results"
                    onClick={() => showOnPage(msg.pageResults!)}
                  >
                    View {msg.pageResults.total} {msg.pageResults.total === 1 ? 'Item' : 'Items'} on Page
                  </button>
                )}
              </div>
            ))}
            {sending && (
              <div className="chat-bubble assistant thinking" aria-label="Assistant is typing">
                <span />
                <span />
                <span />
              </div>
            )}
          </div>

          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault()
              void send()
            }}
          >
            <textarea
              ref={inputRef}
              rows={1}
              value={draft}
              placeholder={placeholder}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={handleKeyDown}
              aria-label="Chat message"
            />
            <button type="submit" className="btn btn-primary btn-sm" disabled={!draft.trim() || sending}>
              Send
            </button>
          </form>
        </section>
      )}

      <button
        type="button"
        className="chat-launcher"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label={open ? 'Close chat' : 'Open chat'}
      >
        {open ? <span className="chat-launcher-x">×</span> : <ChatIcon />}
      </button>
    </div>
  )
}
