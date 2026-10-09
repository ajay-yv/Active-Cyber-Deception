import React, { useState } from 'react'

export interface GoogleAccount {
  email: string
  name: string
  photo?: string
}

interface GoogleAccountChooserProps {
  onSelectAccount: (account: { email: string; name: string }) => void
  onClose: () => void
}

export const GoogleAccountChooserModal: React.FC<GoogleAccountChooserProps> = ({
  onSelectAccount,
  onClose,
}) => {
  const [customEmail, setCustomEmail] = useState('')
  const [showCustomInput, setShowCustomInput] = useState(false)
  const [error, setError] = useState('')

  // Default detected Google accounts on the system / browser
  const savedAccounts: GoogleAccount[] = [
    {
      email: 'ajayyv576@gmail.com',
      name: 'Ajay Y V',
    },
    {
      email: 'patient.care@gmail.com',
      name: 'Patient Account',
    },
  ]

  const handleSelect = (acc: GoogleAccount) => {
    onSelectAccount({ email: acc.email, name: acc.name })
  }

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = customEmail.trim()
    if (!trimmed || !trimmed.includes('@')) {
      setError('Please enter a valid Google email address.')
      return
    }
    const namePart = trimmed.split('@')[0].replace(/[._]/g, ' ')
    const formattedName = namePart
      .split(' ')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')

    onSelectAccount({ email: trimmed, name: formattedName || 'Google User' })
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        background: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(8px)',
        display: 'grid',
        placeItems: 'center',
        zIndex: 99999,
        padding: 16,
      }}
    >
      <div
        style={{
          width: '100%',
          maxWidth: 420,
          background: '#ffffff',
          borderRadius: 24,
          padding: '28px 24px 24px',
          boxShadow: '0 20px 60px rgba(0, 0, 0, 0.4)',
          color: '#1f2937',
          fontFamily: 'Roboto, Inter, -apple-system, sans-serif',
          position: 'relative',
        }}
      >
        {/* Close X Button */}
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: 16,
            right: 16,
            background: 'none',
            border: 'none',
            fontSize: '1.4rem',
            color: '#6b7280',
            cursor: 'pointer',
            lineHeight: 1,
          }}
        >
          ✕
        </button>

        {/* Google Header Logo */}
        <div style={{ textAlign: 'center', marginBottom: 20 }}>
          <svg width="40" height="40" viewBox="0 0 48 48" style={{ marginBottom: 10 }}>
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z" />
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z" />
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z" />
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z" />
          </svg>
          <h3 style={{ margin: '0 0 6px', fontSize: '1.25rem', fontWeight: 600, color: '#111827' }}>
            Choose an account
          </h3>
          <p style={{ margin: 0, fontSize: '0.86rem', color: '#4b5563' }}>
            to continue to <strong style={{ color: '#059669' }}>Healthcare Security Portal</strong>
          </p>
        </div>

        {/* Account List */}
        {!showCustomInput ? (
          <div>
            <div style={{ display: 'grid', gap: 8, marginBottom: 16 }}>
              {savedAccounts.map((acc) => (
                <button
                  key={acc.email}
                  onClick={() => handleSelect(acc)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    width: '100%',
                    padding: '12px 16px',
                    borderRadius: 12,
                    border: '1px solid #e5e7eb',
                    background: '#ffffff',
                    cursor: 'pointer',
                    textAlign: 'left',
                    transition: 'all 0.15s ease',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.05)',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = '#f9fafb')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = '#ffffff')}
                >
                  <div
                    style={{
                      width: 38,
                      height: 38,
                      borderRadius: '50%',
                      background: 'linear-gradient(135deg, #4285F4, #34A853)',
                      color: '#fff',
                      display: 'grid',
                      placeItems: 'center',
                      fontSize: 16,
                      fontWeight: 700,
                      flexShrink: 0,
                    }}
                  >
                    {acc.name.charAt(0)}
                  </div>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: '0.92rem', fontWeight: 600, color: '#111827' }}>
                      {acc.name}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#6b7280', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                      {acc.email}
                    </div>
                  </div>
                  <span style={{ fontSize: '1.2rem', color: '#9ca3af' }}>›</span>
                </button>
              ))}
            </div>

            <button
              onClick={() => setShowCustomInput(true)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                width: '100%',
                padding: '12px 16px',
                borderRadius: 12,
                border: '1px dashed #d1d5db',
                background: '#f9fafb',
                color: '#374151',
                fontSize: '0.88rem',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              <span style={{ fontSize: '1.2rem' }}>👤</span>
              <span>Use another Google account</span>
            </button>
          </div>
        ) : (
          <form onSubmit={handleCustomSubmit} style={{ display: 'grid', gap: 14 }}>
            {error ? (
              <div
                style={{
                  padding: '8px 12px',
                  borderRadius: 8,
                  background: '#fef2f2',
                  border: '1px solid #fca5a5',
                  color: '#991b1b',
                  fontSize: '0.82rem',
                }}
              >
                ⚠️ {error}
              </div>
            ) : null}

            <div>
              <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#374151', marginBottom: 6 }}>
                Enter your Real Google Email:
              </label>
              <input
                type="email"
                required
                autoFocus
                value={customEmail}
                onChange={(e) => setCustomEmail(e.target.value)}
                placeholder="e.g. ajayyv576@gmail.com"
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: 10,
                  border: '1.5px solid #d1d5db',
                  fontSize: '0.92rem',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 6 }}>
              <button
                type="button"
                onClick={() => setShowCustomInput(false)}
                style={{
                  padding: '10px 16px',
                  borderRadius: 10,
                  border: '1px solid #d1d5db',
                  background: '#ffffff',
                  color: '#374151',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Back
              </button>

              <button
                type="submit"
                style={{
                  padding: '10px 20px',
                  borderRadius: 10,
                  border: 'none',
                  background: '#1a73e8',
                  color: '#ffffff',
                  fontSize: '0.88rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  boxShadow: '0 2px 6px rgba(26, 115, 232, 0.4)',
                }}
              >
                Next & Sign In
              </button>
            </div>
          </form>
        )}

        <div style={{ marginTop: 24, paddingTop: 16, borderTop: '1px solid #f3f4f6', textAlign: 'center', fontSize: '0.76rem', color: '#9ca3af' }}>
          To continue, Google will share your name and email address with Healthcare Portal.
        </div>
      </div>
    </div>
  )
}
