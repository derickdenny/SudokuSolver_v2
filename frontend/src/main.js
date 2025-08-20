// main.jsx (or main.js)
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.js' // <-- This line imports your App component

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App /> // <-- This renders your App component
  </StrictMode>,
)