export type DashboardKind = 'admin' | 'hospital' | 'hacker'

export type DashboardAlert = {
  type: string
  message: string
  severity: string
}

export type DashboardResponse = {
  role: DashboardKind
  metrics: Record<string, number>
  recent_patients?: Array<{ id: string; name: string; status: string }>
  deception_assets?: Array<{ type: string; label: string }>
  synthetic_records?: Array<{
    synthetic_patient_id: string
    name: string
    disease: string
    diagnosis: string
    medicines: string[]
    age_range?: string
    phone_number?: string
    email?: string
    aadhaar_number?: string
    address?: string
    insurance_details?: string
  }>
  alerts?: DashboardAlert[]
}

export type SecurityOverviewResponse = {
  active_attacks: number
  suspicious_sessions: number
  total_events: number
  watermarked_records: number
  honeytokens: number
}

export type SecurityEvent = {
  id: string
  event_type: string
  details: string
}

export type AttackAlert = {
  attack_id: string
  attack_type: string
  patient_id?: string
  synthetic_patient_id?: string
  session_id: string
  username?: string
  ip_address?: string
  user_agent?: string
  timestamp: string
  risk_score: number
  attack_probability?: number | null
  gateway_decision: string
  watermark_id?: string
  records_returned?: number
  records_requested?: number
  requested_fields?: string[]
  synthetic_patient_ids?: string[]
  data_type?: string
  stolen_categories?: string[]
  blocked_status: boolean
}

export type SecurityAttackRequest = {
  session_id: string
  action: string
  details: string
}

export type BreachRequest = {
  query: string
  target_patient_id: string
  requested_payload: Record<string, unknown>
}

export type BreachResponse = {
  patient_id?: string
  synthetic_patient_id?: string
  name?: string
  age?: string
  disease?: string
  diagnosis?: string
  medicines?: string[] | string
  aadhaar_number?: string
  phone_number?: string
  email?: string
  address?: string
  notes?: string
  original_target_id?: string
  source_type?: string
  watermark_id?: string
  decoy_records?: Array<{
    synthetic_patient_id: string
    name: string
    age: string
    disease: string
    diagnosis: string
    aadhaar_number: string
    phone_number: string
    email: string
    address: string
    medicines: string[] | string
    notes?: string
  }>
}

export type AuditEvent = {
  id: string
  event_type: string
  details: string
  created_at?: string
  severity?: string
  actor?: string
  status?: string
}

export type LabResultResponse = {
  patient_id: string
  test_name: string
  result: string
  reported_at: string
}

export type AnalyticsSummaryResponse = {
  patient_metrics: {
    total_patients: number
    disease_distribution: Record<string, number>
    age_ranges: Record<string, number>
  }
  security_metrics: {
    total_attacks: number
    total_audit_events: number
    total_watermarks: number
  }
}

export type ForensicLeakResponse = {
  report: string
  watermark: {
    id: string
    watermark_id: string
    source_id: string
    source_type: string
    hospital_id: string
    timestamp: string
    session_id: string
    watermark_text: string
    watermark_fingerprint: string
  }
  forensic_record: null | {
    synthetic_patient_id: string
    watermark_fingerprint: string
    name: string
    disease: string
    diagnosis: string
    treatment_pattern: string
  }
  attack_timeline: string[]
}

export type DeceptionSession = {
  session_id: string
  reason: string
  threat_score: number
  activated_at: string
  active: boolean
  decoy_ids: string[]
}

export type DeceptionStatusResponse = {
  sessions: DeceptionSession[]
}

export type LoginResponse = {
  access_token: string
  token_type: 'bearer'
  user: {
    username: string
    role: 'administrator' | 'doctor' | 'receptionist' | 'hacker'
    full_name: string
    email?: string
  }
}

export type PatientCreate = {
  name: string
  age: number
  disease: string
  diagnosis: string
  medicines: string[]
  dosages?: string[]
  treatment_pattern: string
  gender?: string
  date_of_birth?: string
  blood_group?: string
  phone?: string
  email?: string
  address?: string
  aadhaar?: string
  emergency_contact?: string
  symptoms?: string[]
  allergies?: string[]
  doctor_assigned?: string
  department?: string
  admission_date?: string
  discharge_date?: string
  lab_reports?: string[]
  medical_images?: string[]
  patient_id?: number
}

export type PatientRecord = {
  patient_id?: number
  id: string
  name: string
  age: number
  disease: string
  diagnosis: string
  medicines: string[]
  treatment_pattern: string
  watermark_id?: string
  watermark_text?: string
  watermark_fingerprint?: string
  dosages?: string[]
  gender?: string
  date_of_birth?: string
  blood_group?: string
  phone?: string
  email?: string
  address?: string
  aadhaar?: string
  emergency_contact?: string
  symptoms?: string[]
  allergies?: string[]
  doctor_assigned?: string
  department?: string
  admission_date?: string
  discharge_date?: string
  lab_reports?: string[]
  medical_images?: string[]
  forensic_record?: {
    synthetic_patient_id: string
    watermark_fingerprint: string
    name: string
    disease: string
    diagnosis: string
    treatment_pattern: string
    aadhaar_number?: string
    phone_number?: string
    email?: string
    age_range?: string
  }

  watermark_record?: any
}


export type PatientCreateResponse = {
  decision: {
    route: string
    threat_score: number
    reason: string
  }
  patient: PatientRecord
  synthetic_twin: {
    synthetic_patient_id: string
    real_patient_id: string
    name: string
    address: string
    phone_number: string
    aadhaar_number: string
    email: string
    insurance_details: string
    emergency_contact: string
    disease: string
    diagnosis: string
    medicines: string[]
    treatment_pattern: string
    age_range: string
    watermark_fingerprint: string
  }
}

export type RoleName = LoginResponse['user']['role']

const configuredApiBaseUrl = (import.meta.env.VITE_API_BASE_URL ?? '').trim()
const internalDockerHostPattern = /^(https?:\/\/)?(backend|gateway|ai-engine)(:\d+)?\/?$/i
export const apiBaseUrl = configuredApiBaseUrl && !internalDockerHostPattern.test(configuredApiBaseUrl)
  ? configuredApiBaseUrl.replace(/\/$/, '')
  : ''

export function websocketBaseUrl(): string {
  if (configuredApiBaseUrl && !internalDockerHostPattern.test(configuredApiBaseUrl)) {
    return configuredApiBaseUrl.replace(/^http/, 'ws').replace(/\/$/, '')
  }
  if (typeof window === 'undefined') return 'ws://127.0.0.1:8000'
  return window.location.origin.replace(/^http/, 'ws')
}

export async function safeFetch(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch (err: any) {
    if (err instanceof TypeError || String(err).includes('fetch') || String(err).includes('NetworkError')) {
      const url = typeof input === 'string' ? input : input.toString()
      throw new Error(`Unable to reach the backend at ${url}. Start the local backend and verify the frontend proxy is running.`)
    }
    throw err
  }
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const u = (username || '').toLowerCase().trim()
  const p = (password || '').trim()

  try {
    const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ username: u, password: p }),
    })

    if (response.ok) {
      return (await response.json()) as LoginResponse
    }
  } catch (err) {
    console.warn('Backend server not reachable, using client-side fallback authentication:', err)
  }

  // Fallback authentication for static Vercel deployment or standalone frontend access
  const roleMap: Record<string, LoginResponse['user']['role']> = {
    admin: 'administrator',
    administrator: 'administrator',
    doctor: 'doctor',
    reception: 'receptionist',
    receptionist: 'receptionist',
    hacker: 'hacker',
  }

  if (u.length > 0) {
    const role = roleMap[u] || 'doctor'
    const nameMap: Record<string, string> = {
      administrator: 'System Administrator',
      doctor: 'Dr. Priya Nair',
      receptionist: 'Reception Desk',
      hacker: 'Simulated Attacker',
    }
    return {
      access_token: `demo-access-token-${Date.now()}`,
      token_type: 'bearer',
      user: {
        username: u,
        role: role,
        full_name: nameMap[role] || (u.charAt(0).toUpperCase() + u.slice(1)),
        email: `${u}@stjude.org`,
      },
    }
  }

  throw new Error('Login failed. Invalid username or password.')
}


export async function fetchDashboard(kind: DashboardKind, token: string): Promise<DashboardResponse> {
  const response = await safeFetch(`${apiBaseUrl}/api/dashboard/${kind}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Dashboard fetch failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json() as Promise<DashboardResponse>
}

export async function fetchPatients(token: string): Promise<{ patients: PatientRecord[] }> {
  const response = await safeFetch(`${apiBaseUrl}/api/patients`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Patients fetch failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json() as Promise<{ patients: PatientRecord[] }>
}

export async function deletePatient(patientId: string, token: string): Promise<{ status: string; message: string }> {
  const response = await safeFetch(`${apiBaseUrl}/api/patients/${patientId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Delete patient failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json()
}

export async function fetchPatientHistory(token: string): Promise<{ history: (PatientRecord & { archived_at?: string; status?: string })[] }> {
  const response = await safeFetch(`${apiBaseUrl}/api/patients/history`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Patient history fetch failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json()
}

export async function deletePatientHistory(historyId: string, token: string): Promise<{ status: string; message: string }> {
  const response = await safeFetch(`${apiBaseUrl}/api/patients/history/${historyId}`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Delete history record failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json()
}

export async function clearPatientHistory(token: string): Promise<{ status: string; message: string; count: number }> {
  const response = await safeFetch(`${apiBaseUrl}/api/patients/history`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Clear history failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json()
}

export async function purgeAllPatients(token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/patients/purge/all`, {
    method: 'DELETE',
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Purge all patients failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json()
}


export async function fetchSecurityOverview(token: string): Promise<SecurityOverviewResponse> {
  const response = await fetch(`${apiBaseUrl}/api/security/overview`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'active-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || `Security overview fetch failed (HTTP ${response.status})`
    throw new Error(msg)
  }

  return response.json() as Promise<SecurityOverviewResponse>
}


export async function fetchSecurityEvents(token: string): Promise<SecurityEvent[]> {
  const response = await fetch(`${apiBaseUrl}/api/security/events`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Security events fetch failed')
  }

  const payload = (await response.json()) as { events: SecurityEvent[] }
  return payload.events
}

export async function fetchDeceptionStatus(token: string): Promise<DeceptionStatusResponse> {
  const response = await fetch(`${apiBaseUrl}/api/security/deception/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Deception status fetch failed')
  }

  return response.json() as Promise<DeceptionStatusResponse>
}

export async function createSecurityAttack(payload: SecurityAttackRequest, token: string): Promise<{ event: SecurityEvent }> {
  const response = await fetch(`${apiBaseUrl}/api/security/attacks`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error('Security attack creation failed')
  }

  return response.json() as Promise<{ event: SecurityEvent }>
}

export async function createBreachRequest(payload: BreachRequest, token: string): Promise<BreachResponse> {
  const response = await safeFetch(`${apiBaseUrl}/api/security/breach`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Breach request failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<BreachResponse>
}

export async function uploadFiles(formData: FormData, token: string): Promise<{ files: { original: string; stored: string; path: string }[] }> {
  const response = await fetch(`${apiBaseUrl}/api/integration/upload`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`File upload failed: ${body || response.statusText}`)
  }

  return response.json()
}

export async function createPatient(patient: PatientCreate, token: string, sessionId: string): Promise<PatientCreateResponse> {
  const response = await fetch(`${apiBaseUrl}/api/patients`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-Session-Id': sessionId,
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
      'X-OS': 'windows',
      'X-Forwarded-For': '127.0.0.1',
      'X-Country': 'in',
    },
    body: JSON.stringify(patient),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Patient creation failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<PatientCreateResponse>
}

export async function updatePatient(patientId: string, patient: PatientCreate, token: string, sessionId: string): Promise<PatientCreateResponse> {
  const response = await fetch(`${apiBaseUrl}/api/patients/${patientId}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
      'X-Session-Id': sessionId,
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
      'X-OS': 'windows',
      'X-Forwarded-For': '127.0.0.1',
      'X-Country': 'in',
    },
    body: JSON.stringify(patient),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Patient update failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<PatientCreateResponse>
}

export async function fetchAnalyticsSummary(token: string): Promise<AnalyticsSummaryResponse> {
  const response = await fetch(`${apiBaseUrl}/api/analytics/summary`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Analytics fetch failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<AnalyticsSummaryResponse>
}

export async function fetchAuditEvents(token: string): Promise<AuditEvent[]> {
  const response = await fetch(`${apiBaseUrl}/api/audit/events`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Audit events fetch failed: ${body || response.statusText}`)
  }

  const payload = await response.json()
  return payload.events as AuditEvent[]
}

export async function fetchLabResults(patientId: string, token: string): Promise<LabResultResponse> {
  const response = await fetch(`${apiBaseUrl}/api/integration/lab-results/${patientId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
      'X-Session-Id': 'doc-user-session',
      'X-Device': 'trusted',
      'X-Browser': 'chrome',
    },
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    const msg = errorData.detail || response.statusText || 'Lab results fetch failed'
    throw new Error(msg)
  }

  return response.json() as Promise<LabResultResponse>
}


export async function fetchForensicLeak(watermarkId: string, token: string): Promise<ForensicLeakResponse> {
  const response = await fetch(`${apiBaseUrl}/api/security/leaks/${watermarkId}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Forensic leak fetch failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<ForensicLeakResponse>
}

export async function changePassword(oldPassword: string, newPassword: string, token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/auth/change-password`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Change password failed: ${body || response.statusText}`)
  }

  return response.json()
}

export async function changeEmail(newEmail: string, token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/auth/change-email`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ new_email: newEmail }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Change email failed: ${body || response.statusText}`)
  }

  return response.json()
}

export async function requestPasswordReset(email: string, username?: string): Promise<{ status: string; message: string; otp?: string; email_dispatch?: { to: string; subject: string; body: string; otp: string } }> {
  const response = await fetch(`${apiBaseUrl}/api/auth/request-password-reset`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, username }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Request password reset failed: ${body || response.statusText}`)
  }

  return response.json()
}


export async function verifyResetOtp(email: string, otp: string, newPassword: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/auth/verify-reset-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, otp, new_password: newPassword }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Verify OTP failed: ${body || response.statusText}`)
  }

  return response.json()
}

export async function requestEmailVerification(email: string, token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/auth/request-email-verification`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ email }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Request email verification failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<{ status: string; message: string }>
}

export async function verifyEmailOtp(email: string, otp: string, token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/auth/verify-email-otp`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ email, otp }),
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Verify email OTP failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<{ status: string; message: string }>
}

export async function fetchSentEmails(email?: string): Promise<{ logs: string[] }> {
  const url = email ? `${apiBaseUrl}/api/auth/sent-emails?email=${encodeURIComponent(email)}` : `${apiBaseUrl}/api/auth/sent-emails`
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('Failed to fetch sent email logs')
  }
  return response.json()
}

export async function fetchForensicRecords(token: string, limit: number = 50): Promise<{ records: AttackAlert[] }> {
  const response = await fetch(`${apiBaseUrl}/api/security/forensic-records?limit=${limit}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch forensic records')
  }

  return response.json()
}
export async function fetchWatermarks(token: string): Promise<{ watermarks: any[] }> {
  const response = await fetch(`${apiBaseUrl}/api/security/watermarks`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    const body = await response.text()
    throw new Error(`Watermarks fetch failed: ${body || response.statusText}`)
  }

  return response.json() as Promise<{ watermarks: any[] }>
}

export async function fetchAIDecisions(token: string): Promise<{ decisions: any[] }> {
  const response = await fetch(`${apiBaseUrl}/api/security/ai-decisions`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    return { decisions: [] }
  }

  return response.json()
}

export async function fetchHoneytokens(token: string): Promise<{ honeytokens: any[] }> {
  const response = await fetch(`${apiBaseUrl}/api/security/honeytokens`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    return { honeytokens: [] }
  }

  return response.json()
}

export async function toggleAttackMode(enabled: boolean, token: string): Promise<{ status: string; attack_mode: boolean }> {
  const response = await fetch(`${apiBaseUrl}/api/security/toggle-attack-mode`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ enabled }),
  })

  if (!response.ok) {
    throw new Error('Failed to toggle attack mode')
  }

  return response.json()
}

export async function blockIP(ipAddress: string, reason: string, token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/security/block-ip`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ ip_address: ipAddress, reason }),
  })

  if (!response.ok) {
    throw new Error('Failed to block IP')
  }

  return response.json()
}

export async function unblockIP(ipAddress: string, token: string): Promise<{ status: string; message: string }> {
  const response = await fetch(`${apiBaseUrl}/api/security/unblock-ip`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ ip_address: ipAddress }),
  })

  if (!response.ok) {
    throw new Error('Failed to unblock IP')
  }

  return response.json()
}

export async function exportAuditLogs(token: string): Promise<Blob> {
  const response = await fetch(`${apiBaseUrl}/api/audit/export`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to export audit logs')
  }

  return response.blob()
}

export async function scanForensicsLeak(
  content: string,
  token: string,
  sourceType?: string,
): Promise<{
  matched: boolean
  watermark?: any
  source_type?: string
  is_invisible_watermark?: boolean
  message: string
  dossier?: {
    watermark_id: string
    source_type: string
    source_id: string
    hospital_id: string
    session_id: string
    watermark_fingerprint: string
    watermark_text: string
    attribution_confidence: number
    is_synthetic_decoy: boolean
    is_invisible_watermark: boolean
    leak_source: Record<string, any>
    timeline: Array<{
      timestamp: string
      phase: string
      event_type: string
      description: string
      threat_score: number
      actor: string
    }>
    forensic_summary: string
    forensic_certificate: string
    forensic_record?: Record<string, any>
  }
}> {
  const response = await fetch(`${apiBaseUrl}/api/security/forensics/scan`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content, source_type: sourceType }),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Forensics scan failed: ${text || response.statusText}`)
  }

  return response.json()
}

export async function fetchADOTelemetry(token: string): Promise<{
  ado_engine_status: string
  active_deception_sessions: number
  total_autonomous_teardowns: number
  total_attractive_lures_deployed: number
  real_patient_data_exposure: string
  adversary_deception_rate: string
  active_sessions: Array<{
    session_id: string
    state: string
    threat_score: number
    reason: string
    activated_at: string
    last_activity_at: string
    decoy_ids: string[]
    lure_type: string
    interactions_count: number
  }>
}> {
  const response = await fetch(`${apiBaseUrl}/api/security/ado/status`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch ADO telemetry')
  }

  return response.json()
}

export async function triggerADOTeardown(sessionId: string, reason: string, token: string): Promise<any> {
  const response = await fetch(`${apiBaseUrl}/api/security/ado/teardown`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ session_id: sessionId, reason }),
  })

  if (!response.ok) {
    throw new Error('Failed to trigger autonomous teardown')
  }

  return response.json()
}

export async function deployADOLure(sessionId: string, lureType: string, token: string): Promise<any> {
  const response = await fetch(`${apiBaseUrl}/api/security/ado/lures/deploy`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ session_id: sessionId, lure_type: lureType }),
  })

  if (!response.ok) {
    throw new Error('Failed to deploy attractive lure')
  }

  return response.json()
}

export async function recoverPatientFromLeak(rawContent: string, token: string): Promise<{
  status: string
  matched: boolean
  message?: string
  leak_classification?: string
  patient_safety_status?: string
  recovered_real_patient?: Record<string, any> | null
  decoy_patient?: Record<string, any> | null
  watermark?: {
    watermark_id: string
    watermark_fingerprint: string
    source_type: string
    source_id: string
    session_id: string
    hospital_id: string
    is_invisible_watermark: boolean
  }
  attribution?: {
    attacker_session_id: string
    hospital_origin: string
    confidence_score: number
    attribution_confidence: string
    real_patient_pii_exposed: boolean
  }
  timeline?: Array<{
    timestamp: string
    phase: string
    event_type: string
    description: string
    threat_score: number
    actor: string
  }>
  forensic_certificate?: string
  forensic_summary?: string
  recommended_actions?: string[]
  dossier?: any
}> {
  const response = await fetch(`${apiBaseUrl}/api/security/forensics/recover`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ raw_content: rawContent }),
  })

  if (!response.ok) {
    const text = await response.text()
    throw new Error(`Forensics recovery failed: ${text || response.statusText}`)
  }

  return response.json()
}

export async function fetchPatternEvolutionProfile(token: string): Promise<{
  total_patients_observed: number
  top_diseases: string[]
  top_departments: string[]
  average_age_distribution: number
  active_pattern_rules: number
  realism_fidelity_score: number
  last_updated: string
}> {
  const response = await fetch(`${apiBaseUrl}/api/security/twins/evolution`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!response.ok) {
    throw new Error('Failed to fetch pattern evolution profile')
  }

  return response.json()
}


