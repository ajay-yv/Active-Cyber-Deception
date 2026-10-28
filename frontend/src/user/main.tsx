import React from 'react'
import { createRoot } from 'react-dom/client'
import '../styles.css'
import AppUser from './AppUser'

const root = createRoot(document.getElementById('root')!)
root.render(<AppUser />)
