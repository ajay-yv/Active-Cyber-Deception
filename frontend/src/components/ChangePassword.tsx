import React, { useState } from 'react'

type Props = {
  token: string
}

import { changePassword } from '../api'

export function ChangePassword({ token }: Props) {
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setMessage('')
    setError('')
    if (newPassword !== confirm) {
      setError('New password and confirmation do not match')
      return
    }
    try {
      const res = await changePassword(oldPassword, newPassword, token)
      setMessage(res.message)
      setOldPassword('')
      setNewPassword('')
      setConfirm('')
    } catch (err) {
      setError(String(err))
    }
  }

  return (
    <section style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 14, padding: 22, color: '#0f172a', boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)' }}>
      <h4 style={{ margin: '0 0 14px', color: '#0f172a', fontSize: '1.05rem', fontWeight: 800 }}>Change Password</h4>
      <form onSubmit={submit} style={{ display: 'grid', gap: 12 }}>
        <input type="password" placeholder="Current password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }} />
        <input type="password" placeholder="New password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }} />
        <input type="password" placeholder="Confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }} />
        <button type="submit" style={{ padding: '10px 16px', borderRadius: 8, border: 'none', background: 'linear-gradient(135deg, #0284c7, #0369a1)', color: '#ffffff', fontWeight: 700, cursor: 'pointer' }}>Change password</button>
      </form>
      {message ? <p style={{ color: '#059669', marginTop: 10, fontWeight: 600 }}>✓ {message}</p> : null}
      {error ? <p style={{ color: '#dc2626', marginTop: 10, fontWeight: 600 }}>⚠ {error}</p> : null}
    </section>
  )
}

export default ChangePassword
