import React, { useEffect, useState } from 'react'
import { Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom'
import { DashboardCard } from './components/DashboardCard'
import { DashboardList } from './components/DashboardList'
import { DashboardTable } from './components/DashboardTable'
import ChangePassword from './components/ChangePassword'
import type {
  DashboardResponse,
  DeceptionStatusResponse,
  ForensicLeakResponse,
  LoginResponse,
  PatientCreate,
  PatientCreateResponse,
  PatientRecord,
  SecurityAttackRequest,
  SecurityEvent,
  SecurityOverviewResponse,
  AnalyticsSummaryResponse,
  AuditEvent,
  LabResultResponse,
} from './api'
import {
  apiBaseUrl,
  changeEmail,
  createPatient,
  createSecurityAttack,
  fetchAnalyticsSummary,
  fetchAuditEvents,
  fetchDashboard,
  fetchDeceptionStatus,
  fetchForensicLeak,
  fetchLabResults,
  fetchPatients,
  fetchSecurityEvents,
  fetchSecurityOverview,
  login as loginRequest,
  requestPasswordReset,
  verifyResetOtp,
  uploadFiles,
} from './api'

type Notification = {
  id: string
  type: string
  message: string
  timestamp: string
}

function useRealtimeNotifications(
  setNotifications: React.Dispatch<React.SetStateAction<Notification[]>>,
  onEvent?: (type: string, payload: unknown) => void,
) {
  useEffect(() => {
    const wsUrl = apiBaseUrl
      ? apiBaseUrl.replace(/^https?/, apiBaseUrl.startsWith('https') ? 'wss' : 'ws') + '/api/realtime/ws'
      : window.location.origin.replace(/^http/, 'ws') + '/api/realtime/ws'
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
  }, [onEvent, setNotifications])
}

function Layout({ accent, children }: { accent: string; children: React.ReactNode }) {
  return (
    <div className="shell" style={{ ['--accent' as string]: accent }}>
      <aside className="sidebar">
        <div>
          <p className="eyebrow">Active Cyber Deception</p>
          <h1>Healthcare Security Command Center</h1>
          <p className="subtitle">
            Real users and attackers see different systems, with the gateway deciding the route.
          </p>
        </div>
        <nav className="nav">
          <Link to="/hospital">Hospital User Dashboard</Link>
          <Link to="/hacker">Hacker Dashboard</Link>
          <Link to="/admin">Administrator Dashboard</Link>
          <Link to="/profile">Profile</Link>
        </nav>
      </aside>
      <main className="content">{children}</main>
    </div>
  )
}

function LoginPage({ onLogin }: { onLogin: (response: LoginResponse) => void }) {
  const navigate = useNavigate()
  const [username, setUsername] = useState('doctor')
  const [password, setPassword] = useState('doctor123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await loginRequest(username, password)
      onLogin(response)
      navigate(response.user.role === 'hacker' ? '/hacker' : '/hospital', { replace: true })
    } catch {
      setError('Invalid credentials or service unavailable.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout accent="#0f766e">
      <section className="hero login-panel">
        <span className="badge">Authentication</span>
        <h2>Sign in to the healthcare deception platform.</h2>
        <p>
          Use a hospital role to view real data, or a hacker role to enter the deception layer.
        </p>
        <form className="login-form" onSubmit={submit}>
          <label>
            Username
            <input value={username} onChange={(event) => setUsername(event.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
          </label>
          {error ? <p className="error-text">{error}</p> : null}
          <button type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <div className="quick-logins">
          <button type="button" onClick={() => setUsername('doctor')}>
            Doctor
          </button>
          <button type="button" onClick={() => setUsername('admin')}>
            Admin
          </button>
          <button type="button" onClick={() => setUsername('hacker')}>
            Hacker
          </button>
        </div>
      </section>
    </Layout>
  )
}

function HospitalDashboard({ token }: { token: string }) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [patients, setPatients] = useState<PatientRecord[]>([])
  const [form, setForm] = useState<PatientCreate>({
    name: '',
    age: 35,
    disease: '',
    diagnosis: '',
    medicines: [''],
    dosages: [],
    treatment_pattern: 'Standard',
    gender: undefined,
    date_of_birth: undefined,
    blood_group: undefined,
    phone: undefined,
    email: undefined,
    address: undefined,
    aadhaar: undefined,
    emergency_contact: undefined,
    symptoms: [],
    allergies: [],
    doctor_assigned: undefined,
    department: undefined,
    admission_date: undefined,
    discharge_date: undefined,
    lab_reports: [],
    medical_images: [],
    patient_id: undefined,
  })
  const [submitError, setSubmitError] = useState('')
  const [submitResult, setSubmitResult] = useState<PatientCreateResponse | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [sessionId] = useState(() => {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return crypto.randomUUID()
    }
    return `session-${Math.random().toString(36).slice(2)}`
  })

  async function refreshHospitalData() {
    try {
      const [dashboardResponse, patientsResponse] = await Promise.all([
        fetchDashboard('hospital', token),
        fetchPatients(token),
      ])
      setDashboard(dashboardResponse)
      setPatients(patientsResponse.patients)
    } catch {
      // keep existing data if refresh fails
    }
  }

  useEffect(() => {
    refreshHospitalData()
  }, [token])

  useRealtimeNotifications(setNotifications, async (type) => {
    if (type === 'patient_created' || type === 'patient_updated' || type === 'patient_deleted') {
      await refreshHospitalData()
    }
  })

  function calculateAge(dateString: string) {
    const dob = new Date(dateString)
    if (Number.isNaN(dob.getTime())) {
      return 0
    }
    const today = new Date()
    let age = today.getFullYear() - dob.getFullYear()
    const monthDiff = today.getMonth() - dob.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < dob.getDate())) {
      age -= 1
    }
    return Math.max(0, age)
  }

  const metrics = dashboard?.metrics ?? {}

  async function submitPatient(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitError('')
    setIsSubmitting(true)
    setSubmitResult(null)

    try {
      const payload = {
        ...form,
        medicines: form.medicines.filter((item) => item.trim().length > 0),
      }
      const result = await createPatient(payload, token, sessionId)
      setSubmitResult(result)
      setPatients((current) => [result.patient, ...current])
      setForm({
        name: '',
        age: 35,
        disease: '',
        diagnosis: '',
        medicines: [''],
        dosages: [],
        treatment_pattern: 'Standard',
        gender: undefined,
        date_of_birth: undefined,
        blood_group: undefined,
        phone: undefined,
        email: undefined,
        address: undefined,
        aadhaar: undefined,
        emergency_contact: undefined,
        symptoms: [],
        allergies: [],
        doctor_assigned: undefined,
        department: undefined,
        admission_date: undefined,
        discharge_date: undefined,
        lab_reports: [],
        medical_images: [],
        patient_id: undefined,
      })
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'Failed to create patient')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Layout accent="#0f766e">
      <section className="hero">
        <span className="badge">Hospital User</span>
        <h2>Real patient operations stay inside the protected path.</h2>
        <p>
          Register patients, manage appointments, review history, and upload medical records
          through the real database only after the AI Security Gateway approves the session.
        </p>
        <div className="grid cards">
          <DashboardCard label="Total Patients" value={metrics.total_patients ?? patients.length ?? 0} accent="#0f766e" />
          <DashboardCard label="Doctors" value={metrics.doctors ?? 0} accent="#0f766e" />
          <DashboardCard label="Appointments" value={metrics.appointments ?? 0} accent="#0f766e" />
          <DashboardCard label="Synthetic Twins" value={metrics.synthetic_twins ?? 0} accent="#0f766e" />
          <DashboardCard label="Threat Alerts" value={metrics.active_threats ?? 0} accent="#f59e0b" />
        </div>
      </section>
      <div className="grid two-up">
        <DashboardTable
          title="Recent Patients"
          rows={
            patients.length > 0
              ? patients.map((patient) => ({
                  id: patient.id || (patient.patient_id ? `P-${patient.patient_id.toString().padStart(2, '0')}` : 'P-01'),
                  name: patient.name,
                  disease: patient.disease,
                  diagnosis: patient.diagnosis,
                  watermark_id: patient.watermark_id ?? '',
                  watermark_text: (patient.watermark_text ?? '').slice(0, 36),
                  watermark_fingerprint: (patient.watermark_fingerprint ?? '').slice(0, 12),
                }))
              : [
                  { id: 'P-01', name: 'Aarav Mehta', disease: 'Cardiology', diagnosis: 'Admitted', watermark_id: '', watermark_text: '', watermark_fingerprint: '' },
                  { id: 'P-02', name: 'Nisha Patel', disease: 'Neurology', diagnosis: 'Discharged', watermark_id: '', watermark_text: '', watermark_fingerprint: '' },
                ]
          }
        />
        <section className="panel">
          <h3>Hospital Functions</h3>
          <ul className="feature-list">
            <li>Register and update patients</li>
            <li>Upload prescriptions and lab reports</li>
            <li>Schedule appointments</li>
            <li>View discharge summaries</li>
          </ul>
        </section>
      </div>
      {dashboard?.alerts?.length ? (
        <section className="panel">
          <h3>Security Alerts</h3>
          <div className="alert-list">
            {dashboard.alerts.map((alert, index) => (
              <div className={`alert alert-${alert.severity}`} key={`alert-${index}`}>
                <strong>{alert.type}</strong>
                <p>{alert.message}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
      {notifications.length > 0 ? (
        <section className="panel">
          <h3>Realtime Notifications</h3>
          <ul className="list">
            {notifications.map((notification) => (
              <li key={notification.id}>
                <span>{notification.type}</span>
                <strong>{notification.message}</strong>
                <small>{new Date(notification.timestamp).toLocaleTimeString()}</small>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <div className="grid two-up">
        <section className="panel">
          <h3>Register New Patient</h3>
          <form className="login-form" onSubmit={submitPatient}>
            <label>
              Name
              <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
            </label>
            <label>
              Gender
              <select value={form.gender ?? ''} onChange={(event) => setForm({ ...form, gender: event.target.value })}>
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
                <option value="prefer_not_to_say">Prefer not to say</option>
              </select>
            </label>
            <label>
              Date of Birth
              <input
                type="date"
                value={form.date_of_birth ?? ''}
                onChange={(event) => {
                  const dob = event.target.value
                  const age = dob ? calculateAge(dob) : form.age
                  setForm({ ...form, date_of_birth: dob, age })
                }}
              />
            </label>
            <label>
              Age
              <input type="number" min={0} max={130} value={form.age} readOnly />
            </label>
            <label>
              Blood Group
              <input value={form.blood_group ?? ''} onChange={(event) => setForm({ ...form, blood_group: event.target.value })} />
            </label>
            <label>
              Phone
              <input value={form.phone ?? ''} onChange={(event) => setForm({ ...form, phone: event.target.value })} />
            </label>
            <label>
              Email
              <input value={form.email ?? ''} onChange={(event) => setForm({ ...form, email: event.target.value })} />
            </label>
            <label>
              Address
              <input value={form.address ?? ''} onChange={(event) => setForm({ ...form, address: event.target.value })} />
            </label>
            <label>
              Aadhaar / Patient ID
              <input value={form.aadhaar ?? ''} onChange={(event) => setForm({ ...form, aadhaar: event.target.value })} />
            </label>
            <label>
              Disease
              <input value={form.disease} onChange={(event) => setForm({ ...form, disease: event.target.value })} required />
            </label>
            <label>
              Diagnosis
              <input value={form.diagnosis} onChange={(event) => setForm({ ...form, diagnosis: event.target.value })} required />
            </label>
            {submitResult ? (
              <div style={{ marginTop: 16, padding: 12, background: '#f8fafc', borderRadius: 12, color: '#111827' }}>
                <p><strong>Assigned Patient ID:</strong> {submitResult.patient.patient_id ?? submitResult.patient.id}</p>
              </div>
            ) : null}
            <label>
              Symptoms (comma separated)
              <input value={form.symptoms?.join(', ') ?? ''} onChange={(event) => setForm({ ...form, symptoms: event.target.value.split(',').map((s) => s.trim()) })} />
            </label>
            <label>
              Allergies (comma separated)
              <input value={form.allergies?.join(', ') ?? ''} onChange={(event) => setForm({ ...form, allergies: event.target.value.split(',').map((s) => s.trim()) })} />
            </label>
            <label>
              Medicines (comma separated)
              <input
                value={form.medicines.join(', ')}
                onChange={(event) => setForm({ ...form, medicines: event.target.value.split(',').map((item) => item.trim()) })}
              />
            </label>
            <label>
              Dosages (comma separated)
              <input value={form.dosages?.join(', ') ?? ''} onChange={(event) => setForm({ ...form, dosages: event.target.value.split(',').map((s) => s.trim()) })} />
            </label>
            <label>
              Treatment Pattern
              <input
                value={form.treatment_pattern}
                onChange={(event) => setForm({ ...form, treatment_pattern: event.target.value })}
              />
            </label>
            <label>
              Doctor Assigned
              <input value={form.doctor_assigned ?? ''} onChange={(event) => setForm({ ...form, doctor_assigned: event.target.value })} />
            </label>
            <label>
              Department
              <input value={form.department ?? ''} onChange={(event) => setForm({ ...form, department: event.target.value })} />
            </label>
            <label>
              Admission Date
              <input type="date" value={form.admission_date ?? ''} onChange={(event) => setForm({ ...form, admission_date: event.target.value })} />
            </label>
            <label>
              Discharge Date
              <input type="date" value={form.discharge_date ?? ''} onChange={(event) => setForm({ ...form, discharge_date: event.target.value })} />
            </label>
            <label>
              Lab Reports (filenames)
              <input value={form.lab_reports?.join(', ') ?? ''} onChange={(event) => setForm({ ...form, lab_reports: event.target.value.split(',').map((s) => s.trim()) })} />
            </label>
            <label>
              Medical Images (filenames)
              <input value={form.medical_images?.join(', ') ?? ''} onChange={(event) => setForm({ ...form, medical_images: event.target.value.split(',').map((s) => s.trim()) })} />
            </label>
            {submitError ? <p className="error-text">{submitError}</p> : null}
            <button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Registering…' : 'Register patient'}
            </button>
            {submitResult ? (
              <div className="panel" style={{ marginTop: '1rem' }}>
                <h4>Gateway Decision</h4>
                <p>Route: {submitResult.decision.route}</p>
                <p>Threat score: {submitResult.decision.threat_score}</p>
                <p>Reason: {submitResult.decision.reason}</p>
                <div style={{ marginTop: '1rem' }}>
                  <h5>Recorded Patient Watermark</h5>
                  <p>ID: {submitResult.patient.id}</p>
                  <p>Watermark ID: {submitResult.patient.watermark_id ?? 'N/A'}</p>
                  <p>Watermark Text: {submitResult.patient.watermark_text ?? 'N/A'}</p>
                  <p>Fingerprint: {submitResult.patient.watermark_fingerprint ?? 'N/A'}</p>
                </div>
                <div style={{ marginTop: '1rem' }}>
                  <h5>Synthetic Twin</h5>
                  <p>ID: {submitResult.synthetic_twin.synthetic_patient_id}</p>
                  <p>Source Patient: {submitResult.synthetic_twin.real_patient_id}</p>
                  <p>Diagnosis: {submitResult.synthetic_twin.diagnosis}</p>
                </div>
              </div>
            ) : null}
          </form>
        </section>
        <section className="panel">
          <h3>Operational Controls</h3>
          <ul className="feature-list">
            <li>Submit patient records through the secure gateway</li>
            <li>Monitor synthetic twin generation for attack sessions</li>
            <li>Track forensic watermarks alongside patient data</li>
            <li>Use session IDs to isolate hospital access flows</li>
          </ul>
        </section>
      </div>
      <section className="panel">
        <h3>Lab Integration</h3>
        <LabResultsPanel token={token} />
      </section>
    </Layout>
  )
}

function LabResultsPanel({ token }: { token: string }) {
  const [patientId, setPatientId] = useState('')
  const [result, setResult] = useState<LabResultResponse | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function lookup(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const response = await fetchLabResults(patientId, token)
      setResult(response)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Lab results lookup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <form className="login-form" onSubmit={lookup}>
        <label>
          Patient ID
          <input value={patientId} onChange={(event) => setPatientId(event.target.value)} required />
        </label>
        <button type="submit" disabled={loading}>
          {loading ? 'Looking up…' : 'Fetch Lab Results'}
        </button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
      {result ? (
        <div className="panel" style={{ marginTop: '1rem' }}>
          <h4>Lab Result</h4>
          <p>Patient: {result.patient_id}</p>
          <p>Test: {result.test_name}</p>
          <p>Result: {result.result}</p>
          <p>Reported: {new Date(result.reported_at).toLocaleString()}</p>
        </div>
      ) : null}
    </div>
  )
}

function HackerDashboard({ token }: { token: string }) {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null)
  const [attack, setAttack] = useState<SecurityAttackRequest>({
    session_id: 'session-attack-1',
    action: 'explore_fake_records',
    details: 'Probe synthetic patient records with suspicious queries',
  })
  const [attackResult, setAttackResult] = useState<SecurityEvent | null>(null)
  const [attackError, setAttackError] = useState('')
  const [isAttacking, setIsAttacking] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])

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
    refreshHackerData()
  }, [token])

  useRealtimeNotifications(setNotifications, async (type) => {
    if (type === 'attack' || type === 'audit' || type === 'patient_created' || type === 'patient_updated') {
      await refreshHackerData()
    }
  })

  const metrics = dashboard?.metrics ?? {}

  async function submitAttack(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setAttackError('')
    setAttackResult(null)
    setIsAttacking(true)

    try {
      const response = await createSecurityAttack(attack, token)
      setAttackResult(response.event)
    } catch (error) {
      setAttackError(error instanceof Error ? error.message : 'Attack simulation failed')
    } finally {
      setIsAttacking(false)
    }
  }

  return (
    <Layout accent="#b91c1c">
      <section className="hero">
        <span className="badge">Hacker Simulation</span>
        <h2>The attacker only ever reaches synthetic records and monitored honeytokens.</h2>
        <p>
          The deception layer mirrors a real hospital enough to keep the session active while the
          security database records the full attack timeline.
        </p>
        <div className="grid cards">
          <DashboardCard label="Synthetic Records" value={metrics.synthetic_records ?? 0} accent="#b91c1c" />
          <DashboardCard label="Honeytokens" value={metrics.honeytokens ?? 0} accent="#b91c1c" />
          <DashboardCard label="Active Attacks" value={metrics.active_attacks ?? 0} accent="#b91c1c" />
          <DashboardCard label="Threat Score" value={metrics.threat_score ?? 0} accent="#b91c1c" />
        </div>
      </section>
      <div className="grid two-up">
        <DashboardList
          title="Deception Assets"
          items={dashboard?.deception_assets ?? [
            { type: 'Clinical Record', label: 'PID-48291' },
            { type: 'Medical Report', label: 'RAD-10482' },
            { type: 'Secure Token', label: 'INS-78201' },
          ]}
        />
        <section className="panel">
          <h3>Attack Simulator</h3>
          <form className="login-form" onSubmit={submitAttack}>
            <label>
              Session ID
              <input
                value={attack.session_id}
                onChange={(event) => setAttack({ ...attack, session_id: event.target.value })}
              />
            </label>
            <label>
              Action
              <input
                value={attack.action}
                onChange={(event) => setAttack({ ...attack, action: event.target.value })}
              />
            </label>
            <label>
              Details
              <textarea
                value={attack.details}
                onChange={(event) => setAttack({ ...attack, details: event.target.value })}
              />
            </label>
            {attackError ? <p className="error-text">{attackError}</p> : null}
            <button type="submit" disabled={isAttacking}>
              {isAttacking ? 'Simulating…' : 'Run attack simulation'}
            </button>
            {attackResult ? (
              <div className="panel" style={{ marginTop: '1rem' }}>
                <h4>Attack Event Recorded</h4>
                <p>ID: {attackResult.id}</p>
                <p>Type: {attackResult.event_type}</p>
                <p>Details: {attackResult.details}</p>
              </div>
            ) : null}
          </form>
        </section>
      </div>
      {notifications.length > 0 ? (
        <section className="panel">
          <h3>Realtime Notifications</h3>
          <ul className="list">
            {notifications.map((notification) => (
              <li key={notification.id}>
                <span>{notification.type}</span>
                <strong>{notification.message}</strong>
                <small>{new Date(notification.timestamp).toLocaleTimeString()}</small>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      <section className="panel">
        <h3>Hacker Targeted Data</h3>
        <p>
          This view simulates what an attacker sees: synthetic patient records, poison honeytokens,
          and active decoys built to trap unauthorized access.
        </p>
      </section>
    </Layout>
  )
}

function AdminDashboard({ token }: { token: string }) {
  const [overview, setOverview] = useState<SecurityOverviewResponse | null>(null)
  const [events, setEvents] = useState<SecurityEvent[]>([])
  const [deception, setDeception] = useState<DeceptionStatusResponse | null>(null)
  const [analytics, setAnalytics] = useState<AnalyticsSummaryResponse | null>(null)
  const [auditEvents, setAuditEvents] = useState<AuditEvent[]>([])
  const [watermarkId, setWatermarkId] = useState('wm-trace-2')
  const [forensic, setForensic] = useState<ForensicLeakResponse | null>(null)
  const [forensicError, setForensicError] = useState('')
  const [notifications, setNotifications] = useState<Notification[]>([])

  async function refreshAdminData() {
    try {
      const overviewResponse = await fetchSecurityOverview(token)
      setOverview(overviewResponse)
    } catch {
      setOverview(null)
    }
    try {
      const eventsResponse = await fetchSecurityEvents(token)
      setEvents(eventsResponse)
    } catch {
      setEvents([])
    }
    try {
      const deceptionResponse = await fetchDeceptionStatus(token)
      setDeception(deceptionResponse)
    } catch {
      setDeception(null)
    }
    try {
      const analyticsResponse = await fetchAnalyticsSummary(token)
      setAnalytics(analyticsResponse)
    } catch {
      setAnalytics(null)
    }
    try {
      const auditResponse = await fetchAuditEvents(token)
      setAuditEvents(auditResponse)
    } catch {
      setAuditEvents([])
    }
  }

  useEffect(() => {
    refreshAdminData()
  }, [token])

  useRealtimeNotifications(setNotifications, async (type) => {
    if (
      type === 'patient_created' ||
      type === 'patient_updated' ||
      type === 'patient_deleted' ||
      type === 'attack' ||
      type === 'audit' ||
      type === 'session_block' ||
      type === 'ai_decision'
    ) {
      await refreshAdminData()
    }
  })

  async function lookupForensicLeak() {
    setForensicError('')
    try {
      const response = await fetchForensicLeak(watermarkId, token)
      setForensic(response)
    } catch {
      setForensicError('No forensic record found for that watermark ID.')
      setForensic(null)
    }
  }

  useEffect(() => {
    fetchSecurityOverview(token).then(setOverview)
    fetchSecurityEvents(token).then(setEvents)
    fetchDeceptionStatus(token).then(setDeception)
    fetchAnalyticsSummary(token).then(setAnalytics).catch(() => setAnalytics(null))
    fetchAuditEvents(token).then(setAuditEvents).catch(() => setAuditEvents([]))
  }, [token])

  return (
    <Layout accent="#7c3aed">
      <section className="hero">
        <span className="badge">Administrator</span>
        <h2>Security operations view for attacks, watermarks, and deception coverage.</h2>
        <p>
          This dashboard combines the gateway decisions, attack timeline, and leak attribution signals
          into a single operational surface for the hospital security team.
        </p>
        <div className="grid cards">
          <DashboardCard label="Active Attacks" value={overview?.active_attacks ?? 0} accent="#7c3aed" />
          <DashboardCard label="Suspicious Sessions" value={overview?.suspicious_sessions ?? 0} accent="#7c3aed" />
          <DashboardCard label="Watermarked Records" value={overview?.watermarked_records ?? 0} accent="#7c3aed" />
          <DashboardCard label="Honeytokens" value={overview?.honeytokens ?? 0} accent="#7c3aed" />
          <DashboardCard label="Active Decoy Sessions" value={deception?.sessions.length ?? 0} accent="#7c3aed" />
        </div>
      {analytics ? (
        <section className="panel">
          <h3>Analytics Summary</h3>
          <div className="grid two-up">
            <section className="panel">
              <h4>Patient Metrics</h4>
              <p>Total patients: {analytics.patient_metrics.total_patients}</p>
              <p>Disease mix: {Object.entries(analytics.patient_metrics.disease_distribution)
                .map(([disease, count]) => `${disease}: ${count}`)
                .join(', ')}</p>
            </section>
            <section className="panel">
              <h4>Security Metrics</h4>
              <p>Total attacks: {analytics.security_metrics.total_attacks}</p>
              <p>Audit events: {analytics.security_metrics.total_audit_events}</p>
              <p>Total watermarks: {analytics.security_metrics.total_watermarks}</p>
            </section>
          </div>
        </section>
      ) : null}
      {auditEvents.length > 0 ? (
        <section className="panel">
          <h3>Recent Audit Events</h3>
          <div className="table">
            <div className="table-row table-head">
              <span>Type</span>
              <span>ID</span>
              <span>Details</span>
            </div>
            {auditEvents.slice(-10).reverse().map((event) => (
              <div className="table-row" key={event.id}>
                <span>{event.event_type}</span>
                <span>{event.id}</span>
                <span>{event.details}</span>
              </div>
            ))}
          </div>
        </section>
      ) : null}
      {notifications.length > 0 ? (
        <section className="panel">
          <h3>Realtime Notifications</h3>
          <ul className="list">
            {notifications.map((notification) => (
              <li key={notification.id}>
                <span>{notification.type}</span>
                <strong>{notification.message}</strong>
                <small>{new Date(notification.timestamp).toLocaleTimeString()}</small>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      </section>
      <div className="grid two-up">
        <section className="panel">
          <h3>Security Events</h3>
          <div className="table">
            <div className="table-row table-head">
              <span>Type</span>
              <span>Event</span>
              <span>Details</span>
            </div>
            {events.map((event) => (
              <div className="table-row" key={event.id}>
                <span>{event.event_type}</span>
                <span>{event.id}</span>
                <span>{event.details}</span>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <h3>Response Focus</h3>
          <ul className="feature-list">
            <li>Inspect gateway decisions for synthetic routing</li>
            <li>Trace leaks back to watermark IDs</li>
            <li>Review attacker activity and sessions</li>
            <li>Track honeytokens and deception coverage</li>
          </ul>
        </section>
      </div>
      <div className="grid two-up">
        <DashboardList
          title="Active Decoys"
          items={
            deception?.sessions.map((session) => ({
              type: `${session.threat_score}`,
              label: `${session.session_id} • ${session.reason}`,
            })) ?? []
          }
        />
        <section className="panel">
          <h3>Autonomous Deception</h3>
          <ul className="feature-list">
            <li>Threat-triggered decoy activation</li>
            <li>Watermarked synthetic records for attribution</li>
            <li>Automatic teardown after the session normalizes</li>
            <li>Reason-aware security decision tracing</li>
          </ul>
        </section>
      </div>
      <div className="grid two-up">
        <section className="panel">
          <h3>Forensic Leak Lookup</h3>
          <div className="login-form" style={{ marginTop: '1rem' }}>
            <label>
              Watermark ID
              <input value={watermarkId} onChange={(event) => setWatermarkId(event.target.value)} />
            </label>
            <button type="button" onClick={lookupForensicLeak}>
              Lookup forensic record
            </button>
          </div>
          {forensicError ? <p className="error-text">{forensicError}</p> : null}
          {forensic ? (
            <div className="table" style={{ marginTop: '1rem' }}>
              <div className="table-row table-head">
                <span>Field</span>
                <span>Value</span>
              </div>
              <div className="table-row">
                <span>Watermark ID</span>
                <span>{forensic.watermark.watermark_id}</span>
              </div>
              <div className="table-row">
                <span>Source Type</span>
                <span>{forensic.watermark.source_type}</span>
              </div>
              <div className="table-row">
                <span>Source Record ID</span>
                <span>{forensic.watermark.source_id}</span>
              </div>
              <div className="table-row">
                <span>Fingerprint</span>
                <span>{forensic.forensic_record?.watermark_fingerprint ?? 'Unavailable'}</span>
              </div>
              <div className="table-row">
                <span>Synthetic Twin</span>
                <span>{forensic.forensic_record?.synthetic_patient_id ?? 'Unavailable'}</span>
              </div>
              <div className="table-row">
                <span>Decoy Session</span>
                <span>{forensic.watermark.session_id}</span>
              </div>
            </div>
          ) : null}
          <div style={{ marginTop: '1rem' }}>
            <h4>Attach Files</h4>
            <input type="file" id="labFiles" multiple />
            <button
              type="button"
              onClick={async () => {
                const el = document.getElementById('labFiles') as HTMLInputElement | null
                if (!el || !el.files || el.files.length === 0) return
                const fd = new FormData()
                for (const f of Array.from(el.files)) fd.append('files', f)
                try {
                  const res = await uploadFiles(fd, token)
                  alert(`Uploaded ${res.files.length} files: ${res.files.map((f) => f.stored).join(', ')}`)
                } catch (err) {
                  alert(String(err))
                }
              }}
            >
              Upload selected files
            </button>
          </div>
        </section>
        <section className="panel">
          <h3>Forensic Traceability</h3>
          <ul className="feature-list">
            <li>Lookup watermark-linked synthetic fingerprints</li>
            <li>Confirm which decoy session exposed the record</li>
            <li>Correlate synthetic twins with the attack timeline</li>
            <li>Keep real patient data out of the forensic surface</li>
          </ul>
        </section>
      </div>
    </Layout>
  )
}

function ProfilePage({
  session,
  onSessionUpdate,
}: {
  session: LoginResponse
  onSessionUpdate: (session: LoginResponse) => void
}) {
  const [newEmail, setNewEmail] = useState(session.user.email ?? '')
  const [emailMessage, setEmailMessage] = useState('')
  const [emailError, setEmailError] = useState('')
  const [resetEmail, setResetEmail] = useState(session.user.email ?? '')
  const [otp, setOtp] = useState('')
  const [resetPassword, setResetPassword] = useState('')
  const [resetMessage, setResetMessage] = useState('')
  const [resetError, setResetError] = useState('')

  async function updateEmail(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setEmailMessage('')
    setEmailError('')
    try {
      const result = await changeEmail(newEmail, session.access_token)
      setEmailMessage(result.message)
      onSessionUpdate({
        ...session,
        user: {
          ...session.user,
          email: newEmail,
        },
      })
    } catch (err) {
      setEmailError(err instanceof Error ? err.message : 'Failed to update email')
    }
  }

  async function sendPasswordReset(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setResetMessage('')
    setResetError('')
    try {
      const result = await requestPasswordReset(resetEmail)
      setResetMessage(result.message)
    } catch (err) {
      setResetError(err instanceof Error ? err.message : 'Failed to request password reset')
    }
  }

  async function verifyReset(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setResetMessage('')
    setResetError('')
    try {
      const result = await verifyResetOtp(resetEmail, otp, resetPassword)
      setResetMessage(result.message)
      setOtp('')
      setResetPassword('')
    } catch (err) {
      setResetError(err instanceof Error ? err.message : 'Invalid OTP or reset failed')
    }
  }

  return (
    <Layout accent="#0f766e">
      <section className="hero">
        <span className="badge">Profile</span>
        <h2>Manage your account</h2>
        <p>Change your password from your profile page rather than from the dashboard panels.</p>
      </section>
      <div className="grid two-up">
        <section className="panel">
          <h3>Account Details</h3>
          <div className="table">
            <div className="table-row">
              <span>Username</span>
              <span>{session.user.username}</span>
            </div>
            <div className="table-row">
              <span>Full Name</span>
              <span>{session.user.full_name}</span>
            </div>
            <div className="table-row">
              <span>Role</span>
              <span>{session.user.role}</span>
            </div>
            <div className="table-row">
              <span>Email</span>
              <span>{session.user.email ?? 'Not set'}</span>
            </div>
          </div>
        </section>
        <section className="panel">
          <h3>Security</h3>
          <ChangePassword token={session.access_token} />
        </section>
      </div>
      <div className="grid two-up">
        <section className="panel">
          <h3>Update Email</h3>
          <form className="login-form" onSubmit={updateEmail}>
            <label>
              New email
              <input value={newEmail} onChange={(event) => setNewEmail(event.target.value)} type="email" required />
            </label>
            <button type="submit">Update email</button>
            {emailMessage ? <p className="success-text">{emailMessage}</p> : null}
            {emailError ? <p className="error-text">{emailError}</p> : null}
          </form>
        </section>
        <section className="panel">
          <h3>Password Reset via OTP</h3>
          <form className="login-form" onSubmit={sendPasswordReset}>
            <label>
              Email for reset
              <input value={resetEmail} onChange={(event) => setResetEmail(event.target.value)} type="email" required />
            </label>
            <button type="submit">Send OTP</button>
            {resetMessage && !resetError ? <p className="success-text">{resetMessage}</p> : null}
          </form>
          <form className="login-form" onSubmit={verifyReset}>
            <label>
              OTP
              <input value={otp} onChange={(event) => setOtp(event.target.value)} required />
            </label>
            <label>
              New password
              <input type="password" value={resetPassword} onChange={(event) => setResetPassword(event.target.value)} required />
            </label>
            <button type="submit">Verify OTP and reset</button>
            {resetError ? <p className="error-text">{resetError}</p> : null}
            {resetMessage && !resetError ? <p className="success-text">{resetMessage}</p> : null}
          </form>
        </section>
      </div>
    </Layout>
  )
}

export default function App() {
  const [session, setSession] = useState<LoginResponse | null>(() => {
    const stored = localStorage.getItem('ehr-session')
    return stored ? (JSON.parse(stored) as LoginResponse) : null
  })

  useEffect(() => {
    if (session) {
      localStorage.setItem('ehr-session', JSON.stringify(session))
    } else {
      localStorage.removeItem('ehr-session')
    }
  }, [session])

  return (
    <Routes>
      <Route
        path="/"
        element={
          session ? (
            <Navigate
              to={session.user.role === 'hacker' ? '/hacker' : session.user.role === 'administrator' ? '/admin' : '/hospital'}
              replace
            />
          ) : (
            <LoginPage onLogin={setSession} />
          )
        }
      />
      <Route path="/hospital" element={session ? <HospitalDashboard token={session.access_token} /> : <Navigate to="/" replace />} />
      <Route path="/hacker" element={session ? <HackerDashboard token={session.access_token} /> : <Navigate to="/" replace />} />
      <Route path="/admin" element={session ? <AdminDashboard token={session.access_token} /> : <Navigate to="/" replace />} />
      <Route path="/profile" element={session ? <ProfilePage session={session} onSessionUpdate={setSession} /> : <Navigate to="/" replace />} />
    </Routes>
  )
}
