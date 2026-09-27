import React from 'react'
import { createRoot } from 'react-dom/client'
import AppUser from './user/AppUser'
import AppHacker from './hacker/AppHacker'
import './styles.css'

const isHackerPortOrPath =
  window.location.port === '5174' || window.location.pathname.startsWith('/hacker')

const root = createRoot(document.getElementById('root')!)
root.render(
  <React.StrictMode>
    {isHackerPortOrPath ? <AppHacker /> : <AppUser />}
  </React.StrictMode>,
)

