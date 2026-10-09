import React, { useState } from 'react'
import type { LoginResponse } from '../api'
import { login as loginRequest } from '../api'

export interface DoctorProfile {
  id: string
  username: string
  altUsername?: string
  name: string
  title: string
  dept: string
  license: string
  icon: string
  accent: string
  defaultPassword?: string
}

export interface DoctorLoginPageProps {
  onLogin: (session: LoginResponse) => void
  onCancel?: () => void
  initialDoctorId?: string
}

export const DOCTORS_LIST: DoctorProfile[] = [
  {
    id: 'doctor_priya',
    username: 'doctor_priya',
    altUsername: 'doctor',
    name: 'Dr. Priya Nair',
    title: 'Senior Cardiologist & Head of Internal Medicine',
    dept: 'Cardiology',
    license: 'MCI-84920',
    icon: '🫀',
    accent: '#0284c7',
    defaultPassword: 'Priya@1432',
  },
  {
    id: 'doctor_ramesh',
    username: 'doctor_ramesh',
    name: 'Dr. Ramesh Kumar',
    title: 'Consultant Neurologist & Neuro-ICU Director',
    dept: 'Neurology',
    license: 'MCI-92314',
    icon: '🧠',
    accent: '#a855f7',
    defaultPassword: 'Ramesh@1432',
  },
  {
    id: 'doctor_sarah',
    username: 'doctor_sarah',
    name: 'Dr. Sarah Jenkins',
    title: 'Pediatric Specialist & Neonatal Director',
    dept: 'Pediatrics',
    license: 'MCI-71089',
    icon: '👶',
    accent: '#ec4899',
    defaultPassword: 'Sarah@1432',
  },
  {
    id: 'doctor_rajesh',
    username: 'doctor_rajesh',
    name: 'Dr. Rajesh Patel',
    title: 'Orthopedic Surgeon & Joint Reconstruction',
    dept: 'Orthopedics',
    license: 'MCI-65432',
    icon: '🦴',
    accent: '#f59e0b',
    defaultPassword: 'Rajesh@1432',
  },
  {
    id: 'doctor_anita',
    username: 'doctor_anita',
    name: 'Dr. Anita Sharma',
    title: 'General Clinical Physician & Emergency Lead',
    dept: 'General Medicine',
    license: 'MCI-54321',
    icon: '🩺',
    accent: '#10b981',
    defaultPassword: 'Anita@1432',
  },
]

export const DoctorLoginPage: React.FC<DoctorLoginPageProps> = ({ onLogin, onCancel, initialDoctorId }) => {
  const [selectedDocId, setSelectedDocId] = useState<string>(initialDoctorId || 'doctor_priya')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const activeDoc = DOCTORS_LIST.find((d) => d.id === selectedDocId) || DOCTORS_LIST[0]

  async function handleLoginSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError('')

    const trimmedPassword = password.trim()
    if (!trimmedPassword) {
      setError(`Please enter the password for ${activeDoc.name}.`)
      setLoading(false)
      return
    }

    try {
      // Authenticate with specific doctor account credentials
      let response: LoginResponse
      try {
        response = await loginRequest(activeDoc.username, trimmedPassword)
      } catch (err) {
        if (activeDoc.altUsername) {
          response = await loginRequest(activeDoc.altUsername, trimmedPassword)
        } else {
          throw err
        }
      }

      onLogin(response)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Invalid password for ${activeDoc.name}. Please verify doctor credentials.`
      )
    } finally {
      setLoading(false)
    }
  }

  function handleSelectDoctor(docId: string) {
    setSelectedDocId(docId)
    setPassword('')
    setError('')
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        background: 'radial-gradient(circle at 50% 20%, #0f172a 0%, #020617 100%)',
        color: '#f1f5f9',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '36px 16px',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          maxWidth: 620,
          width: '100%',
          background: 'rgba(15, 23, 42, 0.96)',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          borderRadius: 24,
          padding: '40px 36px',
          boxShadow: '0 25px 65px rgba(0, 0, 0, 0.85)',
          backdropFilter: 'blur(16px)',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <h2 style={{ margin: 0, fontSize: '1.65rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            Doctor Clinical Portal Login
          </h2>
          <p style={{ margin: '8px auto 0', color: '#94a3b8', fontSize: '0.88rem', maxWidth: 500, lineHeight: 1.5 }}>
            Select doctor option and enter your password to unlock your isolated patient records.
          </p>
        </div>

        {/* Option: Doctor Option (Dropdown Selector) */}
        <div
          style={{
            background: 'rgba(30, 41, 59, 0.6)',
            border: '1px solid rgba(56, 189, 248, 0.25)',
            borderRadius: 16,
            padding: '18px 22px',
            marginBottom: 20,
          }}
        >
          <label
            htmlFor="doctor-selector"
            style={{
              display: 'block',
              fontSize: '0.85rem',
              fontWeight: 700,
              color: '#38bdf8',
              marginBottom: 8,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            🩺 Select Doctor Option:
          </label>
          <select
            id="doctor-selector"
            value={selectedDocId}
            onChange={(e) => handleSelectDoctor(e.target.value)}
            style={{
              width: '100%',
              padding: '14px 16px',
              borderRadius: 12,
              border: `2px solid ${activeDoc.accent}`,
              background: '#0f172a',
              color: '#f8fafc',
              fontSize: '0.98rem',
              fontWeight: 700,
              outline: 'none',
              cursor: 'pointer',
              boxShadow: `0 4px 14px ${activeDoc.accent}26`,
            }}
          >
            {DOCTORS_LIST.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.icon} {doc.name} — {doc.dept} (License {doc.license})
              </option>
            ))}
          </select>
        </div>

        {/* Respective Doctor Password Form */}
        <form
          onSubmit={handleLoginSubmit}
          style={{
            background: 'rgba(30, 41, 59, 0.75)',
            border: `1.5px solid ${activeDoc.accent}88`,
            borderRadius: 18,
            padding: '24px',
            boxShadow: `0 8px 30px rgba(0, 0, 0, 0.5)`,
          }}
        >
          {/* Active Doctor Identity Banner */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 12,
              marginBottom: 18,
              paddingBottom: 14,
              borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <span style={{ fontSize: '2rem' }}>{activeDoc.icon}</span>
              <div>
                <strong style={{ fontSize: '1.1rem', color: '#f8fafc', display: 'block' }}>
                  Authenticating Doctor: {activeDoc.name}
                </strong>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>
                  Department: <strong style={{ color: activeDoc.accent }}>{activeDoc.dept}</strong> | License: <strong>{activeDoc.license}</strong>
                </span>
              </div>
            </div>
          </div>

          {/* Password Input Field */}
          <div style={{ display: 'grid', gap: 8, marginBottom: 20 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label
                htmlFor="doctor-password"
                style={{ fontSize: '0.86rem', color: '#cbd5e1', fontWeight: 700 }}
              >
                Password for {activeDoc.name}:
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#38bdf8',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                  padding: 0,
                }}
              >
                {showPassword ? '🙈 Hide' : '👁️ Show'} Password
              </button>
            </div>

            <input
              id="doctor-password"
              type={showPassword ? 'text' : 'password'}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={`Enter password for ${activeDoc.name}`}
              required
              autoFocus
              style={{
                width: '100%',
                padding: '13px 16px',
                borderRadius: 12,
                border: '1px solid rgba(255, 255, 255, 0.2)',
                background: '#0b1120',
                color: '#fff',
                fontSize: '0.98rem',
                outline: 'none',
                transition: 'border-color 0.2s',
              }}
            />
          </div>

          {/* Error Message */}
          {error && (
            <div
              style={{
                padding: '12px 16px',
                borderRadius: 10,
                background: 'rgba(239, 68, 68, 0.15)',
                border: '1px solid #ef4444',
                color: '#fca5a5',
                fontSize: '0.86rem',
                fontWeight: 600,
                marginBottom: 18,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}
            >
              <span>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end', alignItems: 'center', flexWrap: 'wrap' }}>
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                style={{
                  padding: '12px 20px',
                  borderRadius: 12,
                  border: '1px solid rgba(255, 255, 255, 0.15)',
                  background: 'rgba(255, 255, 255, 0.05)',
                  color: '#cbd5e1',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                }}
              >
                ← Return to Portal Login
              </button>
            )}

            <button
              type="submit"
              disabled={loading}
              style={{
                padding: '13px 28px',
                borderRadius: 12,
                border: 'none',
                background: `linear-gradient(135deg, ${activeDoc.accent}, #0891b2)`,
                color: '#fff',
                fontWeight: 800,
                fontSize: '0.98rem',
                cursor: loading ? 'not-allowed' : 'pointer',
                boxShadow: `0 6px 20px ${activeDoc.accent}55`,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                transition: 'transform 0.1s, box-shadow 0.2s',
              }}
            >
              {loading ? (
                <>⏳ Verifying Credentials…</>
              ) : (
                <>🔓 Login to {activeDoc.name.replace(/^Dr\.\s*/i, '')}&apos;s Dashboard &rarr;</>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
