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
    <section style={{ background: 'rgba(15, 23, 42, 0.95)', border: '1px solid rgba(255, 255, 255, 0.1)', borderRadius: 12, padding: 18, color: '#f8fafc' }}>
      <h4>Change Password</h4>
      <form onSubmit={submit} style={{ display: 'grid', gap: 8 }}>
        <input type="password" placeholder="Current password" value={oldPassword} onChange={(e) => setOldPassword(e.target.value)} />
        <input type="password" placeholder="New password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
        <input type="password" placeholder="Confirm new password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
        <button type="submit">Change password</button>
      </form>
      {message ? <p style={{ color: '#064e3b' }}>{message}</p> : null}
      {error ? <p style={{ color: '#991b1b' }}>{error}</p> : null}
    </section>
  )
}

export default ChangePassword
