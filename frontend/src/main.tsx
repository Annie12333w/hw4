import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import AuthProvider from './components/AuthProvider.tsx'
import ChatResultsProvider from './components/ChatResultsProvider.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <ChatResultsProvider>
        <App />
      </ChatResultsProvider>
    </AuthProvider>
  </StrictMode>,
)
