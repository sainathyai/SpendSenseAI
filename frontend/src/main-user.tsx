import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import AppUser from './AppUser.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppUser />
  </StrictMode>,
)

