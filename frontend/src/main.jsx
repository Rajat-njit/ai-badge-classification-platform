import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ReviewerProvider } from './context/ReviewerContext.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ReviewerProvider>
      <App />
    </ReviewerProvider>
  </StrictMode>,
)
