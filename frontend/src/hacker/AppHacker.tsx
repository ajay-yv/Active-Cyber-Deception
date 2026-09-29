import React, { useEffect, useMemo, useState } from 'react'
import { DashboardCard } from '../components/DashboardCard'
import { DashboardList } from '../components/DashboardList'
import type { BreachResponse, DashboardResponse, LoginResponse, PatientRecord } from '../api'
import { createBreachRequest, fetchDashboard, fetchPatients, login, requestPasswordReset, verifyResetOtp } from '../api'
import { executeHackMode, fetchHackModes } from '../api_extra'

type Notification = {
  id: string
  type: string
  message: string
  timestamp: string
}

function useRealtimeNotifications(
  token: string | null,
  setNotifications: React.Dispatch<React.SetStateAction<Notification[]>>,
  onEvent?: (type: string, payload: unknown) => void,
) {
  useEffect(() => {
    if (!token) return

    const wsUrl = window.location.origin.replace(/^http/, 'ws') + '/api/realtime/ws'
    const socket = new WebSocket(wsUrl)

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        const payload = data.payload ?? {}
        const notification: Notification = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          type: data.type ?? 'event',
          message: payload.details || payload.action || payload.reason || JSON.stringify(payload),
          timestamp: new Date().toISOString(),
        }
        setNotifications((current) => [notification, ...current].slice(0, 6))
        if (onEvent) {
          onEvent(data.type ?? 'event', payload)
        }
      } catch {
        // ignore malformed messages
      }
    }

    socket.onclose = () => {
      setNotifications((current) => [
        {
          id: `closed-${Date.now()}`,
          type: 'system',
          message: 'Realtime connection closed',
          timestamp: new Date().toISOString(),
        },
        ...current,
      ].slice(0, 6))
    }

    socket.onerror = () => {
      setNotifications((current) => [
        {
          id: `error-${Date.now()}`,
          type: 'system',
          message: 'Realtime connection error',
          timestamp: new Date().toISOString(),
        },
        ...current,
      ].slice(0, 6))
    }

    return () => socket.close()
  }, [token, onEvent, setNotifications])
}

export default function AppHacker() {
  const [username, setUsername] = useState('hacker@stjude.org')
  const [password, setPassword] = useState('hacker123')
  const [isForgotPasswordView, setIsForgotPasswordView] = useState(false)
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<LoginResponse['user'] | null>(null)
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [attackMessage, setAttackMessage] = useState('')
  const [error, setError] = useState('')
  const [resetEmail, setResetEmail] = useState('')
  const [otp, setOtp] = useState('')
  const [resetPassword, setResetPassword] = useState('')
  const [resetStatus, setResetStatus] = useState('')
  const [resetError, setResetError] = useState('')
  const [resetLink, setResetLink] = useState('')
  const [sessionId, setSessionId] = useState('session-001')
  const [attackDetail, setAttackDetail] = useState('Probe synthetic records and trigger watermark response')
  const [breachQuery, setBreachQuery] = useState('Retrieve patient record')
  const [targetPatientId, setTargetPatientId] = useState('ALL_PATIENTS')
  const [customPatientInput, setCustomPatientInput] = useState('')
  const [activePatients, setActivePatients] = useState<PatientRecord[]>([])
  const [breachResponse, setBreachResponse] = useState<BreachResponse | null>(null)
  const [modeResult, setModeResult] = useState<string>('')
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [modes, setModes] = useState<Array<{ id: string; label: string; description: string }>>([])
  const [selectedMode, setSelectedMode] = useState<string | null>(null)

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const urlEmail = params.get('email')
    const urlToken = params.get('reset_token')
    if (urlEmail || urlToken) {
      setIsForgotPasswordView(true)
      if (urlEmail) setResetEmail(urlEmail)
      if (urlToken) setOtp(urlToken)
    }
  }, [])

  async function refreshHackerData() {
    if (!token) return
    try {
      const response = await fetchDashboard('hacker', token)
      setDashboard(response)
    } catch {
      // keep current dashboard if refresh fails
    }
  }

  useEffect(() => {
    if (!token) {
      return
    }

    refreshHackerData()
    fetchPatients(token)
      .then((res) => setActivePatients(res.patients || []))
      .catch(() => {})

    // fetch available simulated hack modes
    fetchHackModes(token)
      .then((r) => {
        setModes(r.modes)
        setSelectedMode(r.modes?.[0]?.id ?? null)
      })
      .catch(() => {})
  }, [token])

  useRealtimeNotifications(token, setNotifications, async (type) => {
    if (type === 'attack' || type === 'audit' || type === 'patient_created' || type === 'patient_updated' || type === 'patient_deleted') {
      await refreshHackerData()
    }
  })

  const metrics = useMemo(() => dashboard?.metrics ?? {}, [dashboard])

  function handleLogin(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setAttackMessage('')

    login(username, password)
      .then((result) => {
        if (result.user.role !== 'hacker') {
          setError('Please sign in with the hacker account for this dashboard.')
          return
        }
        setToken(result.access_token)
        setUser(result.user)
      })
      .catch(() => setError('Login failed. Please check your username and passcode.'))
  }

  async function handleRequestPasswordReset(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setResetStatus('')
    setResetError('')
    setResetLink('')

    if (!resetEmail.trim()) {
      setResetError('Please enter a valid email address.')
      return
    }

    try {
      const result = await requestPasswordReset(resetEmail)
      setResetStatus(result.message || `Password reset link sent to ${resetEmail}! Check your email inbox.`)
      if ((result as any).reset_link) {
        setResetLink((result as any).reset_link)
      }
      if ((result as any).otp) {
        setOtp((result as any).otp)
      }
    } catch (err) {
      setResetError(err instanceof Error ? err.message : String(err))
    }
  }

  async function handleVerifyResetOtp(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setResetStatus('')
    setResetError('')

    try {
      const result = await verifyResetOtp(resetEmail, otp, resetPassword)
      setResetStatus(result.message || 'Passcode updated successfully!')
      setOtp('')
      setResetPassword('')
    } catch (err) {
      setResetError(err instanceof Error ? err.message : String(err))
    }
  }

  async function handleAttack(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setAttackMessage('')
    setBreachResponse(null)

    if (!token) {
      setError('Login first to launch attacks.')
      return
    }

    try {
      const isExfiltration = selectedMode === 'exfiltrate_synthetic' || selectedMode === 'exfiltrate_original'
      const result = await executeHackMode(
        {
          session_id: sessionId,
          mode: selectedMode ?? 'probe_api',
          details: attackDetail,
          target_patient_id: isExfiltration ? targetPatientId : undefined,
          requested_payload: isExfiltration
            ? { requested_fields: ['name', 'disease', 'diagnosis', 'medicines'], reason: 'simulated exfiltration' }
            : undefined,
        },
        token,
      )
      setModeResult(JSON.stringify(result, null, 2))
      setAttackMessage('Attack mode executed successfully.')
    } catch (err) {
      setError(String(err))
    }
  }

  function handleBreach(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setAttackMessage('')
    setBreachResponse(null)

    if (!token) {
      setError('Login first to issue breach requests.')
      return
    }

    const effectiveTargetId = targetPatientId === 'CUSTOM' ? (customPatientInput.trim() || 'ALL_PATIENTS') : targetPatientId

    createBreachRequest(
      {
        query: breachQuery,
        target_patient_id: effectiveTargetId,
        requested_payload: {
          requested_fields: ['name', 'disease', 'diagnosis', 'medicines'],
          reason: 'attacker probe',
        },
      },
      token,
    )
      .then((result) => setBreachResponse(result))
      .catch((err) => setError(String(err)))
  }

  const [activeTab, setActiveTab] = useState<'overview' | 'attack' | 'decoys' | 'breach' | 'timeline'>('overview')

  return (
    <div style={{ fontFamily: 'JetBrains Mono, Fira Code, monospace', minHeight: '100vh', background: '#020617', color: '#22c55e' }}>
      {!token ? (
        /* UNAUTHENTICATED MATRIX LOGIN */
        <div style={{ display: 'grid', placeItems: 'center', minHeight: '100vh', padding: 24, background: 'radial-gradient(circle at 50% 0%, #0f172a 0%, #020617 100%)' }}>
          <div style={{ width: '100%', maxWidth: 460, background: 'rgba(15, 23, 42, 0.95)', borderRadius: 24, padding: 36, border: '1px solid rgba(34, 197, 94, 0.3)', boxShadow: '0 0 40px rgba(34, 197, 94, 0.15)' }}>
            
            <div style={{ textAlign: 'center', marginBottom: 28 }}>
              <div style={{ width: 56, height: 56, borderRadius: 16, background: 'linear-gradient(135deg, #15803d, #22c55e)', display: 'grid', placeItems: 'center', fontWeight: 900, fontSize: 28, color: '#000', margin: '0 auto 14px', boxShadow: '0 0 25px rgba(34, 197, 94, 0.4)' }}>
                ☣️
              </div>
              <h2 style={{ margin: '0 0 6px', fontSize: '1.65rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
                Hacker Terminal Portal
              </h2>
              <p style={{ margin: 0, fontSize: '0.85rem', color: '#22c55e' }}>
                [CYBER DECEPTION ADVERSARY CONSOLE v2.4]
              </p>
            </div>

            {!isForgotPasswordView ? (
              <form onSubmit={handleLogin} style={{ display: 'grid', gap: 18 }}>
                <label style={{ display: 'grid', gap: 6, fontSize: '0.85rem', color: '#cbd5e1', fontWeight: 600 }}>
                  Attacker Handle / Email ID
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="hacker"
                    style={{ padding: '12px 16px', borderRadius: 10, border: '1px solid rgba(34, 197, 94, 0.3)', background: '#090d16', color: '#4ade80', fontSize: '0.95rem' }}
                    required
                  />
                </label>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <label style={{ fontSize: '0.85rem', color: '#cbd5e1', fontWeight: 600 }}>
                      Passcode
                    </label>
                    <button
                      type="button"
                      onClick={() => {
                        setIsForgotPasswordView(true)
                        setError('')
                        setResetStatus('')
                        setResetError('')
                        if (username && username.includes('@')) setResetEmail(username)
                      }}
                      style={{ background: 'none', border: 'none', color: '#22c55e', fontSize: '0.8rem', cursor: 'pointer', textDecoration: 'underline' }}
                    >
                      Reset Passcode?
                    </button>
                  </div>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    style={{ width: '100%', padding: '12px 16px', borderRadius: 10, border: '1px solid rgba(34, 197, 94, 0.3)', background: '#090d16', color: '#4ade80', fontSize: '0.95rem' }}
                    required
                  />
                </div>

                {error ? (
                  <div style={{ padding: '12px', borderRadius: 10, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', fontSize: '0.85rem' }}>
                    ⚠ {error}
                  </div>
                ) : null}

                <button
                  type="submit"
                  style={{ padding: '14px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg, #16a34a, #22c55e)', color: '#020617', fontSize: '1rem', fontWeight: 800, cursor: 'pointer', boxShadow: '0 0 20px rgba(34, 197, 94, 0.4)' }}
                >
                  INITIALIZE MATRIX SESSION →
                </button>
              </form>
            ) : (
              <div>
                <h3 style={{ color: '#f8fafc', margin: '0 0 8px' }}>{otp ? 'Set New Passcode' : 'Request Password Reset'}</h3>
                <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: 20 }}>
                  {otp ? `Enter new credentials for ${resetEmail}` : 'Enter your email ID to receive a password reset link.'}
                </p>

                {!otp ? (
                  <form onSubmit={handleRequestPasswordReset} style={{ display: 'grid', gap: 14 }}>
                    <input
                      type="email"
                      value={resetEmail}
                      onChange={(e) => setResetEmail(e.target.value)}
                      placeholder="Enter your email address"
                      style={{ padding: '12px 16px', borderRadius: 10, border: '1px solid rgba(34, 197, 94, 0.3)', background: '#090d16', color: '#4ade80', fontSize: '0.95rem' }}
                      required
                    />
                    <button type="submit" style={{ padding: '12px', borderRadius: 10, border: 'none', background: '#16a34a', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>
                      Send Reset Link
                    </button>
                  </form>
                ) : (
                  <form onSubmit={handleVerifyResetOtp} style={{ display: 'grid', gap: 14 }}>
                    <input
                      type="password"
                      value={resetPassword}
                      onChange={(e) => setResetPassword(e.target.value)}
                      placeholder="New password"
                      style={{ padding: '12px 16px', borderRadius: 10, border: '1px solid rgba(34, 197, 94, 0.3)', background: '#090d16', color: '#4ade80', fontSize: '0.95rem' }}
                      required
                    />
                    <button type="submit" style={{ padding: '12px', borderRadius: 10, border: 'none', background: '#2563eb', color: '#fff', fontWeight: 700, cursor: 'pointer' }}>
                      Update Passcode
                    </button>
                  </form>
                )}

                {resetStatus ? (
                  <div style={{ padding: '12px', borderRadius: 10, background: 'rgba(34, 197, 94, 0.15)', border: '1px solid #22c55e', color: '#4ade80', marginTop: 14, fontSize: '0.85rem' }}>
                    <p style={{ margin: '0 0 6px', fontWeight: 700 }}>✓ {resetStatus}</p>
                    {resetLink ? (
                      <div style={{ marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(34, 197, 94, 0.3)' }}>
                        <span style={{ fontSize: '0.78rem', color: '#cbd5e1', display: 'block', marginBottom: 4 }}>
                          🔑 Direct Password Reset Link:
                        </span>
                        <a
                          href={resetLink}
                          target="_blank"
                          rel="noreferrer"
                          style={{ color: '#38bdf8', fontWeight: 700, fontSize: '0.82rem', wordBreak: 'break-all', textDecoration: 'underline' }}
                        >
                          {resetLink}
                        </a>
                      </div>
                    ) : null}
                  </div>
                ) : null}
                {resetError ? <p style={{ color: '#fca5a5', marginTop: 12, fontSize: '0.85rem' }}>⚠ {resetError}</p> : null}

                <button
                  onClick={() => setIsForgotPasswordView(false)}
                  style={{ marginTop: 16, background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '0.85rem' }}
                >
                  ← Back to Login
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* AUTHENTICATED MATRIX HACKER CONSOLE */
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', minHeight: '100vh' }}>
          
          {/* STICKY MATRIX SIDEBAR */}
          <aside style={{ position: 'sticky', top: 0, height: '100vh', overflowY: 'auto', padding: '24px 16px', background: 'rgba(5, 10, 20, 0.95)', borderRight: '1px solid rgba(34, 197, 94, 0.2)', backdropFilter: 'blur(16px)', display: 'flex', flexDirection: 'column', zIndex: 50 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 28, padding: '0 6px' }}>
              <div style={{ width: 38, height: 38, borderRadius: 10, background: 'linear-gradient(135deg, #15803d, #22c55e)', display: 'grid', placeItems: 'center', fontSize: 18, color: '#000', fontWeight: 900 }}>
                ☣️
              </div>
              <div>
                <span style={{ fontSize: '0.65rem', color: '#22c55e', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.1em' }}>
                  ADVERSARY PORTAL
                </span>
                <h2 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc' }}>
                  Matrix Console
                </h2>
              </div>
            </div>

            {/* TAB NAV BUTTONS */}
            <nav style={{ display: 'grid', gap: 6 }}>
              <button onClick={() => setActiveTab('overview')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', borderRadius: 10, border: activeTab === 'overview' ? '1px solid #22c55e' : '1px solid rgba(255,255,255,0.05)', background: activeTab === 'overview' ? 'rgba(34, 197, 94, 0.15)' : 'transparent', color: activeTab === 'overview' ? '#4ade80' : '#94a3b8', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>
                📊 Overview & Stats
              </button>

              <button onClick={() => setActiveTab('attack')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', borderRadius: 10, border: activeTab === 'attack' ? '1px solid #ef4444' : '1px solid rgba(255,255,255,0.05)', background: activeTab === 'attack' ? 'rgba(239, 68, 68, 0.15)' : 'transparent', color: activeTab === 'attack' ? '#fca5a5' : '#94a3b8', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>
                🎯 Attack Console
              </button>

              <button onClick={() => setActiveTab('decoys')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', borderRadius: 10, border: activeTab === 'decoys' ? '1px solid #a855f7' : '1px solid rgba(255,255,255,0.05)', background: activeTab === 'decoys' ? 'rgba(168, 85, 247, 0.15)' : 'transparent', color: activeTab === 'decoys' ? '#c084fc' : '#94a3b8', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>
                📁 Target Patient Records
              </button>

              <button onClick={() => setActiveTab('breach')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', borderRadius: 10, border: activeTab === 'breach' ? '1px solid #f97316' : '1px solid rgba(255,255,255,0.05)', background: activeTab === 'breach' ? 'rgba(249, 115, 22, 0.15)' : 'transparent', color: activeTab === 'breach' ? '#fdba74' : '#94a3b8', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>
                💥 Breach Simulator
              </button>

              <button onClick={() => setActiveTab('timeline')} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 14px', borderRadius: 10, border: activeTab === 'timeline' ? '1px solid #06b6d4' : '1px solid rgba(255,255,255,0.05)', background: activeTab === 'timeline' ? 'rgba(6, 182, 212, 0.15)' : 'transparent', color: activeTab === 'timeline' ? '#67e8f9' : '#94a3b8', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}>
                📡 Live Terminal Log
              </button>
            </nav>

            {/* SIDEBAR FOOTER */}
            <div style={{ marginTop: 'auto', paddingTop: 20, borderTop: '1px solid rgba(255,255,255,0.08)' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div>
                  <strong style={{ display: 'block', fontSize: '0.8rem', color: '#f8fafc' }}>{user?.full_name}</strong>
                  <span style={{ fontSize: '0.7rem', color: '#ef4444' }}>HOSTILE THREAT ACTOR</span>
                </div>
                <button
                  onClick={() => {
                    setToken(null)
                    setUser(null)
                  }}
                  style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', padding: '6px 10px', borderRadius: 8, fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  Exit
                </button>
              </div>
            </div>
          </aside>

          {/* MAIN CONTENT AREA */}
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
            
            {/* TOP HEADER */}
            <header style={{ height: 64, borderBottom: '1px solid rgba(34, 197, 94, 0.2)', background: 'rgba(5, 10, 20, 0.8)', padding: '0 28px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backdropFilter: 'blur(12px)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: '0.8rem', color: '#ef4444', background: 'rgba(239, 68, 68, 0.15)', padding: '4px 10px', borderRadius: 999, border: '1px solid rgba(239, 68, 68, 0.3)', fontWeight: 800 }}>
                  ● ATTACK MODE ACTIVE
                </span>
                <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Session ID: {sessionId}</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <span style={{ fontSize: '0.78rem', color: '#22c55e' }}>DECEPTION PIPELINE: ONLINE ●</span>
              </div>
            </header>

            {/* TAB CONTENT WRAPPER */}
            <main style={{ padding: 28, flex: 1 }}>

              {/* OVERVIEW TAB */}
              {activeTab === 'overview' ? (
                <div style={{ display: 'grid', gap: 24 }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
                    <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: 20, borderRadius: 16, border: '1px solid rgba(34, 197, 94, 0.2)' }}>
                      <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Total Patient Records</span>
                      <h2 style={{ fontSize: '2rem', margin: '6px 0 0', color: '#4ade80' }}>{metrics.synthetic_records ?? 0}</h2>
                    </div>
                    <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: 20, borderRadius: 16, border: '1px solid rgba(239, 68, 68, 0.2)' }}>
                      <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Active Cyber Attacks</span>
                      <h2 style={{ fontSize: '2rem', margin: '6px 0 0', color: '#fca5a5' }}>{metrics.active_attacks ?? 0}</h2>
                    </div>
                    <div style={{ background: 'rgba(15, 23, 42, 0.8)', padding: 20, borderRadius: 16, border: '1px solid rgba(236, 72, 153, 0.2)' }}>
                      <span style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Attacker Threat Score</span>
                      <h2 style={{ fontSize: '2rem', margin: '6px 0 0', color: '#f472b6' }}>{metrics.threat_score ?? 75}/100</h2>
                    </div>
                  </div>
                </div>
              ) : null}

              {/* ATTACK CONSOLE TAB */}
              {activeTab === 'attack' ? (
                <div style={{ display: 'grid', gap: 24 }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.9)', padding: 24, borderRadius: 16, border: '1px solid rgba(239, 68, 68, 0.3)' }}>
                    <h3 style={{ margin: '0 0 16px', color: '#fca5a5' }}>🎯 Launch Simulated Cyber Attack Vector</h3>
                    
                    <form onSubmit={handleAttack} style={{ display: 'grid', gap: 16 }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                          Session ID
                          <input value={sessionId} onChange={(e) => setSessionId(e.target.value)} style={{ width: '100%', padding: 10, marginTop: 6, borderRadius: 8, background: '#090d16', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }} />
                        </label>
                        <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                          Attack Vector Mode
                          <select value={selectedMode ?? ''} onChange={(e) => setSelectedMode(e.target.value)} style={{ width: '100%', padding: 10, marginTop: 6, borderRadius: 8, background: '#090d16', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }}>
                            {modes.map((m) => (
                              <option key={m.id} value={m.id}>{m.label}</option>
                            ))}
                          </select>
                        </label>
                      </div>

                      <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                        Attack Details / Injection Payload
                        <textarea value={attackDetail} onChange={(e) => setAttackDetail(e.target.value)} rows={3} style={{ width: '100%', padding: 10, marginTop: 6, borderRadius: 8, background: '#090d16', border: '1px solid rgba(255,255,255,0.1)', color: '#4ade80' }} />
                      </label>

                      <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                        Target Patient ID (For Exfiltration Attacks)
                        <input value={targetPatientId} onChange={(e) => setTargetPatientId(e.target.value)} style={{ width: '100%', padding: 10, marginTop: 6, borderRadius: 8, background: '#090d16', border: '1px solid rgba(255,255,255,0.1)', color: '#fff' }} />
                      </label>

                      <button type="submit" style={{ padding: '14px', borderRadius: 10, border: 'none', background: 'linear-gradient(135deg, #dc2626, #ef4444)', color: '#fff', fontWeight: 800, cursor: 'pointer', boxShadow: '0 0 20px rgba(239, 68, 68, 0.4)' }}>
                        🚀 EXECUTE ATTACK VECTOR
                      </button>
                    </form>

                    {attackMessage ? <p style={{ color: '#4ade80', marginTop: 14 }}>✓ {attackMessage}</p> : null}

                    {modeResult ? (
                      <div style={{ marginTop: 20 }}>
                        <h4 style={{ color: '#4ade80', margin: '0 0 8px' }}>💻 AI Gateway Execution Telemetry Result:</h4>
                        <pre style={{ padding: 16, background: '#020617', borderRadius: 12, border: '1px solid rgba(34, 197, 94, 0.3)', color: '#4ade80', fontSize: '0.85rem', overflowX: 'auto' }}>
                          {modeResult}
                        </pre>
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : null}

              {/* DECOY ASSETS TAB */}
              {activeTab === 'decoys' ? (
                <div style={{ display: 'grid', gap: 24 }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.9)', padding: 24, borderRadius: 16, border: '1px solid rgba(168, 85, 247, 0.3)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <h3 style={{ margin: 0, color: '#c084fc' }}>📁 Patient Records Database</h3>
                      <span style={{ fontSize: '0.75rem', background: 'rgba(168, 85, 247, 0.2)', border: '1px solid #a855f7', color: '#c084fc', padding: '4px 10px', borderRadius: 999, fontWeight: 700 }}>
                        ACTIVE RECORD REPOSITORY
                      </span>
                    </div>

                    {dashboard?.synthetic_records && dashboard.synthetic_records.length > 0 ? (
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                          <thead>
                            <tr style={{ background: 'rgba(255,255,255,0.03)' }}>
                              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>Patient ID</th>
                              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>Patient Name & Age</th>
                              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>Disease & Diagnosis</th>
                              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>Aadhaar & Mobile Number</th>
                              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>Email & Location</th>
                              <th style={{ padding: '12px', textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>Prescriptions</th>
                            </tr>
                          </thead>
                          <tbody>
                            {dashboard.synthetic_records.map((r) => (
                              <tr key={r.synthetic_patient_id}>
                                <td style={{ padding: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#c084fc', fontWeight: 700 }}>{r.synthetic_patient_id}</td>
                                <td style={{ padding: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#f8fafc', fontWeight: 600 }}>
                                  {r.name}
                                  <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>{r.age_range || '42 yrs'}</span>
                                </td>
                                <td style={{ padding: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#cbd5e1' }}>
                                  <strong style={{ color: '#f59e0b', display: 'block' }}>{r.disease}</strong>
                                  <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>{r.diagnosis}</span>
                                </td>
                                <td style={{ padding: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#cbd5e1' }}>
                                  <div style={{ fontSize: '0.8rem', color: '#4ade80' }}>🆔 {r.aadhaar_number}</div>
                                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>📞 {r.phone_number}</div>
                                </td>
                                <td style={{ padding: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#cbd5e1' }}>
                                  <div style={{ fontSize: '0.8rem', color: '#38bdf8' }}>✉️ {r.email}</div>
                                  <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>📍 {r.address}</div>
                                </td>
                                <td style={{ padding: '12px', borderBottom: '1px solid rgba(255,255,255,0.05)', color: '#38bdf8' }}>
                                  {Array.isArray(r.medicines) ? r.medicines.join(', ') : r.medicines}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div style={{ padding: 24, textAlign: 'center', background: 'rgba(255,255,255,0.02)', borderRadius: 12, border: '1px dashed rgba(255,255,255,0.1)' }}>
                        <p style={{ color: '#94a3b8', margin: 0, fontSize: '0.9rem' }}>
                          📁 No patient records exfiltrated yet. Issue an exfiltration probe in the <strong>Breach Simulator</strong> tab to retrieve patient database records.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              ) : null}

              {/* BREACH SIMULATOR TAB */}
              {activeTab === 'breach' ? (
                <div style={{ display: 'grid', gap: 24 }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.9)', padding: 24, borderRadius: 16, border: '1px solid rgba(249, 115, 22, 0.3)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                      <h3 style={{ margin: 0, color: '#fdba74' }}>💥 Issue Targeted Patient Breach & Data Theft Probe</h3>
                      <span style={{ fontSize: '0.75rem', background: 'rgba(239, 68, 68, 0.2)', color: '#fca5a5', border: '1px solid #ef4444', padding: '4px 10px', borderRadius: 999, fontWeight: 800 }}>
                        THREAT SCORE: 92/100 (HIGH RISK)
                      </span>
                    </div>

                    <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: 20 }}>
                      Send an exfiltration query to extract patient records directly from the database schema.
                    </p>
                    
                    {/* Single vs Bulk Quick Selectors */}
                    <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
                      <button
                        type="button"
                        onClick={() => {
                          setTargetPatientId('P-01')
                          setBreachQuery("SELECT * FROM patients WHERE id='P-01'")
                        }}
                        style={{
                          padding: '10px 16px',
                          borderRadius: 10,
                          border: targetPatientId === 'P-01' ? '2px solid #22c55e' : '1px solid rgba(255,255,255,0.1)',
                          background: targetPatientId === 'P-01' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(255,255,255,0.04)',
                          color: targetPatientId === 'P-01' ? '#4ade80' : '#cbd5e1',
                          fontWeight: 700,
                          fontSize: '0.85rem',
                          cursor: 'pointer',
                        }}
                      >
                        🎯 Hack 1 Patient (Target: P-01)
                      </button>

                      <button
                        type="button"
                        onClick={() => {
                          setTargetPatientId('ALL_PATIENTS')
                          setBreachQuery('SELECT * FROM patients')
                        }}
                        style={{
                          padding: '10px 16px',
                          borderRadius: 10,
                          border: targetPatientId === 'ALL_PATIENTS' ? '2px solid #f97316' : '1px solid rgba(255,255,255,0.1)',
                          background: targetPatientId === 'ALL_PATIENTS' ? 'rgba(249, 115, 22, 0.2)' : 'rgba(255,255,255,0.04)',
                          color: targetPatientId === 'ALL_PATIENTS' ? '#fdba74' : '#cbd5e1',
                          fontWeight: 700,
                          fontSize: '0.85rem',
                          cursor: 'pointer',
                        }}
                      >
                        🌐 Bulk Exfiltrate All Records
                      </button>
                    </div>

                    {/* Terminal Command Cheat Sheet */}
                    <div style={{ background: '#020617', border: '1px solid rgba(34, 197, 94, 0.3)', borderRadius: 12, padding: '12px 16px', marginBottom: 18 }}>
                      <span style={{ fontSize: '0.75rem', color: '#4ade80', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        💻 Terminal Commands to Hack from Command Prompt / PowerShell:
                      </span>
                      <div style={{ display: 'grid', gap: 6, marginTop: 8, fontSize: '0.82rem', fontFamily: 'monospace' }}>
                        <div style={{ color: '#f8fafc' }}>
                          <span style={{ color: '#eab308' }}>hack.bat 1</span> <span style={{ color: '#94a3b8' }}>&nbsp;— Hack exactly 1 patient record</span>
                        </div>
                        <div style={{ color: '#f8fafc' }}>
                          <span style={{ color: '#eab308' }}>hack.bat patient P-01</span> <span style={{ color: '#94a3b8' }}>&nbsp;— Hack specific patient P-01</span>
                        </div>
                        <div style={{ color: '#f8fafc' }}>
                          <span style={{ color: '#eab308' }}>hack.bat exfiltration 5</span> <span style={{ color: '#94a3b8' }}>&nbsp;— Exfiltrate multiple patient records</span>
                        </div>
                      </div>
                    </div>

                    <form onSubmit={handleBreach} style={{ display: 'grid', gap: 16 }}>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                        <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                          Target Patient(s) Selection
                          <select
                            value={targetPatientId}
                            onChange={(e) => setTargetPatientId(e.target.value)}
                            style={{ width: '100%', padding: 12, marginTop: 6, borderRadius: 10, background: '#090d16', border: '1px solid rgba(249, 115, 22, 0.5)', color: '#fdba74', fontWeight: 700 }}
                          >
                            <option value="P-01">🎯 P-01 - 1 Patient Data (Targeted Hack)</option>
                            <option value="ALL_PATIENTS">🌐 ALL_PATIENTS (All Patient Records - Database Bulk Dump)</option>
                            {activePatients.map((p) => (
                              <option key={p.id} value={p.id}>
                                🆔 {p.id} - {p.name} ({p.department || p.disease || 'Clinical Record'})
                              </option>
                            ))}
                            <option value="CUSTOM">✏️ Custom Patient ID / Multiple Range</option>
                          </select>

                          {targetPatientId === 'CUSTOM' ? (
                            <input
                              value={customPatientInput}
                              onChange={(e) => setCustomPatientInput(e.target.value)}
                              placeholder="e.g. P-01 or P-02"
                              style={{ width: '100%', padding: 10, marginTop: 8, borderRadius: 8, background: '#020617', border: '1px solid #f97316', color: '#fff', fontSize: '0.85rem' }}
                            />
                          ) : null}
                        </label>

                        <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
                          Breach Attack Vector / Query
                          <input value={breachQuery} onChange={(e) => setBreachQuery(e.target.value)} style={{ width: '100%', padding: 12, marginTop: 6, borderRadius: 10, background: '#090d16', border: '1px solid rgba(249, 115, 22, 0.3)', color: '#4ade80', fontWeight: 600 }} />
                        </label>
                      </div>

                      <div style={{ padding: 14, background: 'rgba(9, 13, 22, 0.8)', borderRadius: 12, border: '1px solid rgba(255,255,255,0.08)' }}>
                        <span style={{ fontSize: '0.8rem', color: '#f97316', fontWeight: 800, display: 'block', marginBottom: 8 }}>
                          🎯 Target Patient Data Categories to Steal:
                        </span>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, fontSize: '0.8rem', color: '#cbd5e1' }}>
                          <span style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '4px 10px', borderRadius: 8 }}>🆔 Aadhaar Card Number</span>
                          <span style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '4px 10px', borderRadius: 8 }}>📞 Phone & Address Details</span>
                          <span style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '4px 10px', borderRadius: 8 }}>🩺 Clinical Diagnosis & Notes</span>
                          <span style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '4px 10px', borderRadius: 8 }}>💊 Prescription Medicines</span>
                          <span style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', padding: '4px 10px', borderRadius: 8 }}>🏦 Insurance Account Policy</span>
                        </div>
                      </div>

                      <button type="submit" style={{ padding: '14px', borderRadius: 12, border: 'none', background: 'linear-gradient(135deg, #ea580c, #f97316)', color: '#fff', fontWeight: 800, fontSize: '0.95rem', cursor: 'pointer', boxShadow: '0 0 20px rgba(249, 115, 22, 0.4)' }}>
                        🚀 EXECUTE HACKER EXFILTRATION PROBE & SEND ALERT TO ADMIN →
                      </button>
                    </form>

                    {error ? (
                      <div style={{ padding: '12px 16px', borderRadius: 10, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', marginTop: 14, fontSize: '0.85rem' }}>
                        ⚠ {error}
                      </div>
                    ) : null}

                    {breachResponse ? (
                      <div style={{ marginTop: 24, padding: 20, background: '#020617', borderRadius: 14, border: '1px solid #22c55e' }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, paddingBottom: 10, borderBottom: '1px solid rgba(34, 197, 94, 0.2)' }}>
                          <span style={{ color: '#4ade80', fontWeight: 800, fontSize: '0.9rem' }}>
                            🛡️ EXFILTRATED PATIENT DATA RESPONSE
                          </span>
                          <span style={{ fontSize: '0.75rem', background: 'rgba(34, 197, 94, 0.2)', color: '#4ade80', padding: '3px 8px', borderRadius: 6, fontWeight: 700 }}>
                            DATABASE QUERY SUCCESSFUL
                          </span>
                        </div>

                        <div style={{ padding: 12, background: 'rgba(34, 197, 94, 0.15)', border: '1px solid #22c55e', color: '#4ade80', borderRadius: 8, fontSize: '0.82rem', marginBottom: 14 }}>
                          ⚡ <strong>PATIENT RECORDS EXFILTRATED FROM DATABASE:</strong> Query executed on target {targetPatientId}. Patient Aadhaar, Contact, Diagnosis, and Prescriptions retrieved.
                        </div>

                        {breachResponse.decoy_records ? (
                          <div style={{ display: 'grid', gap: 12 }}>
                            <div style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 700 }}>
                              📦 Exfiltrated Synthetic Twin Decoy Records ({breachResponse.decoy_records.length} Decoys):
                            </div>
                            {breachResponse.decoy_records.map((rec: any, idx: number) => (
                              <div key={idx} style={{ padding: 14, background: 'rgba(168, 85, 247, 0.05)', borderRadius: 12, border: '1px solid rgba(168, 85, 247, 0.3)', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, fontSize: '0.8rem' }}>
                                <div><strong style={{ color: '#94a3b8' }}>Synthetic Patient ID:</strong> <span style={{ color: '#c084fc', fontWeight: 700 }}>{rec.patient_id ?? rec.synthetic_patient_id ?? 'UNRESOLVED_ATTACK_TARGET'}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Synthetic Decoy Name:</strong> <span style={{ color: '#f8fafc', fontWeight: 700 }}>{rec.name}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Decoy Disease:</strong> <span style={{ color: '#c084fc', fontWeight: 600 }}>{rec.disease}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Decoy Diagnosis:</strong> <span style={{ color: '#cbd5e1' }}>{rec.diagnosis}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Synthetic Aadhaar:</strong> <span style={{ color: '#4ade80' }}>{rec.aadhaar_number}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Synthetic Phone:</strong> <span style={{ color: '#94a3b8' }}>{rec.phone_number}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Synthetic Email:</strong> <span style={{ color: '#38bdf8' }}>{rec.email}</span></div>
                                <div><strong style={{ color: '#94a3b8' }}>Location Address:</strong> <span style={{ color: '#94a3b8' }}>{rec.address}</span></div>
                                <div style={{ gridColumn: '1 / -1' }}><strong style={{ color: '#94a3b8' }}>Prescriptions:</strong> <span style={{ color: '#38bdf8' }}>{Array.isArray(rec.medicines) ? rec.medicines.join(', ') : rec.medicines}</span></div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, fontSize: '0.85rem', padding: 14, background: 'rgba(168, 85, 247, 0.05)', borderRadius: 12, border: '1px solid rgba(168, 85, 247, 0.3)' }}>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Synthetic Patient ID:</strong> <span style={{ color: '#c084fc', fontWeight: 700 }}>{breachResponse.patient_id ?? breachResponse.synthetic_patient_id ?? 'UNRESOLVED_ATTACK_TARGET'}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Synthetic Decoy Name:</strong> <span style={{ color: '#f8fafc', fontWeight: 700 }}>{breachResponse.name}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Decoy Disease:</strong> <span style={{ color: '#c084fc', fontWeight: 600 }}>{breachResponse.disease}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Decoy Diagnosis:</strong> <span style={{ color: '#cbd5e1' }}>{breachResponse.diagnosis}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Synthetic Aadhaar:</strong> <span style={{ color: '#4ade80' }}>{breachResponse.aadhaar_number}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Synthetic Phone:</strong> <span style={{ color: '#94a3b8' }}>{breachResponse.phone_number}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Synthetic Email:</strong> <span style={{ color: '#38bdf8' }}>{breachResponse.email}</span></p>
                            <p style={{ margin: 0 }}><strong style={{ color: '#94a3b8' }}>Location Address:</strong> <span style={{ color: '#94a3b8' }}>{breachResponse.address}</span></p>
                            <p style={{ margin: 0, gridColumn: '1 / -1' }}><strong style={{ color: '#94a3b8' }}>Prescriptions:</strong> <span style={{ color: '#38bdf8' }}>{Array.isArray(breachResponse.medicines) ? breachResponse.medicines.join(', ') : breachResponse.medicines}</span></p>
                          </div>
                        )}
                      </div>
                    ) : null}
                  </div>
                </div>
              ) : null}

              {/* TIMELINE TAB */}
              {activeTab === 'timeline' ? (
                <div style={{ display: 'grid', gap: 24 }}>
                  <div style={{ background: 'rgba(15, 23, 42, 0.9)', padding: 24, borderRadius: 16, border: '1px solid rgba(6, 182, 212, 0.3)' }}>
                    <h3 style={{ margin: '0 0 16px', color: '#67e8f9' }}>📡 Real-Time Matrix Event Log Stream</h3>
                    <div style={{ display: 'grid', gap: 10, background: '#020617', padding: 16, borderRadius: 12, border: '1px solid rgba(34, 197, 94, 0.2)', maxHeight: 400, overflowY: 'auto' }}>
                      {notifications.length > 0 ? (
                        notifications.map((n) => (
                          <div key={n.id} style={{ fontSize: '0.8rem', display: 'flex', gap: 12, borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: 6 }}>
                            <span style={{ color: '#64748b' }}>[{new Date(n.timestamp).toLocaleTimeString()}]</span>
                            <span style={{ color: '#22c55e', fontWeight: 700 }}>[{n.type.toUpperCase()}]</span>
                            <span style={{ color: '#f8fafc' }}>{n.message}</span>
                          </div>
                        ))
                      ) : (
                        <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No events logged yet.</span>
                      )}
                    </div>
                  </div>
                </div>
              ) : null}

            </main>
          </div>
        </div>
      )}
    </div>
  )
}
