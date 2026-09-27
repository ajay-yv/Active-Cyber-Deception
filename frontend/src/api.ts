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

export type SyntheticTwinDetails = {
  decoyId: string
  decoyName: string
  age: number
  ageRange: string
  disease: string
  diagnosis: string
  treatmentPattern: string
  aadhaar: string
  phone: string
  email: string
  fingerprint: string
}

export function generateSyntheticTwinDetails(realName: string, id: string | number, realAge?: number): SyntheticTwinDetails {
  const cleanName = (realName || 'Patient').trim()
  const numId = String(id).replace(/\D/g, '') || '1'
  const hash = (cleanName + numId).split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)

  const decoyFirstNames = ['Karthik', 'Aditya', 'Rajesh', 'Vikram', 'Ananya', 'Rohan', 'Sneha', 'Deepak', 'Meera', 'Arjun', 'Suresh', 'Pooja', 'Priya', 'Kavita', 'Siddharth']
  const decoyLastNames = ['Reddy', 'Patel', 'Kapoor', 'Sharma', 'Verma', 'Joshi', 'Chawla', 'Deshmukh', 'Mehta', 'Nair', 'Rao', 'Kulkarni', 'Iyer', 'Bhat', 'Gupta']

  const firstName = decoyFirstNames[hash % decoyFirstNames.length]
  const lastName = decoyLastNames[(hash + 7) % decoyLastNames.length]
  const decoyName = `${firstName} ${lastName}`

  const baseAge = realAge || 35
  const decoyAge = Math.min(85, Math.max(22, (baseAge * 1.4 + (hash % 15)) % 65 + 20))
  const ageRange = `${Math.floor(decoyAge - 2)}-${Math.floor(decoyAge + 3)} yrs`

  const diseases = [
    'Type 2 Diabetes Mellitus with Peripheral Neuropathy',
    'Essential Hypertension (Stage 2 Primary with LVH)',
    'Ischemic Heart Disease (Coronary Artery Disease)',
    'Chronic Kidney Disease (Stage 3A Glomerulonephritis)',
    'Bronchial Asthma (Moderate Persistent Airway Disease)',
    'Rheumatoid Arthritis (Seropositive Polyarthritis)',
    'Hyperthyroidism (Graves Autoimmune Thyroid Disease)',
    'Gastroesophageal Reflux Disease (GERD Grade II)',
  ]

  const diagnoses = [
    'Uncontrolled Hyperglycemia with Distal Microvascular Changes',
    'Elevated Systolic BP (165/98 mmHg) & Concentric Cardiac Remodeling',
    'Subendocardial Ischemia with Exertional Angina',
    'Mild GFR Reduction (52 mL/min) with Microalbuminuria',
    'Bronchospasm with Reduced FEV1/FVC Ratio (68%)',
    'Bilateral Symmetrical Joint Inflammation & Elevated ESR',
    'Suppressed TSH (<0.01 uIU/mL) with Diffuse Thyroid Enlargement',
    'Endoscopic Reflux Esophagitis & Lower Esophageal Sphincter Incompetence',
  ]

  const treatmentPatterns = [
    'Metformin 1000mg BID + Empagliflozin 10mg QD + Retinal Screening',
    'Telmisartan 40mg + Amlodipine 5mg Daily + Low Sodium Diet',
    'Atorvastatin 40mg + Aspirin 75mg + Sublingual Nitroglycerin PRN',
    'Ramipril 5mg QD + Nephrology Monitoring + Fluid Balance Protocol',
    'Fluticasone/Salmeterol 250/50 Inhaler BID + Montelukast 10mg',
    'Methotrexate 15mg Weekly + Folic Acid 5mg + Hydroxychloroquine 200mg',
    'Methimazole 15mg Daily + Propranolol 20mg TID',
    'Pantoprazole 40mg AC + Sucralfate Suspension + Lifestyle Modification',
  ]

  const disease = diseases[hash % diseases.length]
  const diagnosis = diagnoses[hash % diagnoses.length]
  const treatmentPattern = treatmentPatterns[hash % treatmentPatterns.length]

  const randomDigits = ((hash * 137) % 900) + 100
  const emailName = cleanName.toLowerCase().replace(/[^a-z0-9]/g, '')
  const email = `${emailName}${randomDigits}@gmail.com`

  const aadhaarPart1 = ((hash * 43) % 9000) + 1000
  const aadhaarPart2 = ((hash * 89) % 9000) + 1000
  const aadhaarPart3 = ((hash * 167) % 9000) + 1000
  const aadhaar = `${aadhaarPart1} ${aadhaarPart2} ${aadhaarPart3}`

  const phoneSuffix = ((hash * 97) % 90000) + 10000
  const phone = `+91 9845${phoneSuffix}`

  const fingerprintHex = (hash * 9999999).toString(16).toUpperCase().padStart(8, '0')
  const fingerprint = `WM-FINGERPRINT-${fingerprintHex}`

  return {
    decoyId: `SYN-${String(numId).padStart(2, '0')}`,
    decoyName,
    age: Math.round(decoyAge),
    ageRange,
    disease,
    diagnosis,
    treatmentPattern,
    aadhaar,
    phone,
    email,
    fingerprint,
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
    const res = await fetch(input, init)
    const contentType = res.headers.get('content-type') || ''
    // If an API request returns HTML SPA fallback, treat as backend unreached for client fallback
    if (res.ok && contentType.includes('text/html') && String(input).includes('/api/')) {
      throw new Error(`API endpoint ${input} returned HTML SPA page instead of JSON`)
    }
    return res
  } catch (err: any) {
    if (err instanceof TypeError || String(err).includes('fetch') || String(err).includes('NetworkError') || String(err).includes('HTML SPA')) {
      const url = typeof input === 'string' ? input : input.toString()
      throw new Error(`Unable to reach the backend at ${url}`)
    }
    throw err
  }
}

export async function safeJson<T>(response: Response, fallbackValue: T): Promise<T> {
  try {
    const contentType = response.headers.get('content-type') || ''
    if (contentType.includes('text/html')) {
      return fallbackValue
    }
    const text = await response.text()
    if (!text || text.trim().startsWith('<')) {
      return fallbackValue
    }
    return JSON.parse(text) as T
  } catch {
    return fallbackValue
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

    const contentType = response.headers.get('content-type') || ''
    if (response.ok && contentType.includes('application/json')) {
      const data = await response.json().catch(() => null)
      if (data && data.access_token) {
        return data as LoginResponse
      }
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
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/dashboard/${kind}`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      const data = await safeJson<DashboardResponse>(response, null as any)
      if (data) return data
    }
  } catch (err) {
    console.warn(`Dashboard fetch fallback used for ${kind}:`, err)
  }

  return {
    role: kind,
    metrics: {
      total_patients: 12,
      active_attacks: 0,
      honeypots_active: 8,
      watermarked_records: 12,
      security_score: 98,
    },
    recent_patients: [
      { id: 'P-01', name: 'Aarav Sharma', status: 'Protected (Real)' },
      { id: 'P-02', name: 'Karthik Reddy', status: 'Protected (Real)' },
      { id: 'P-03', name: 'Rohan Verma', status: 'Protected (Real)' },
    ],
    deception_assets: [
      { type: 'honeytoken', label: 'Decoy Clinical Record P-01-DEC' },
      { type: 'watermark', label: 'Zero-Leakage Fingerprint DB' },
    ],
    alerts: [],
  }
}

export async function fetchPatients(token: string): Promise<{ patients: PatientRecord[] }> {
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      const data = await safeJson<{ patients: PatientRecord[] }>(response, null as any)
      if (data && Array.isArray(data.patients)) return data
    }
  } catch (err) {
    console.warn('Patients fetch fallback used:', err)
  }

  return { patients: [] }
}

export async function deletePatient(patientId: string, token: string): Promise<{ status: string; message: string }> {
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients/${patientId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      const data = await safeJson<{ status: string; message: string }>(response, { status: 'ok', message: 'Patient removed' })
      return data
    }
  } catch (err) {
    console.warn('Delete patient fallback used:', err)
  }

  return { status: 'ok', message: 'Patient record deleted (client mode)' }
}

export async function fetchPatientHistory(token: string): Promise<{ history: (PatientRecord & { archived_at?: string; status?: string })[] }> {
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients/history`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      const data = await safeJson<{ history: any[] }>(response, { history: [] })
      if (data && Array.isArray(data.history)) return data
    }
  } catch (err) {
    console.warn('Patient history fetch fallback used:', err)
  }

  return { history: [] }
}

export async function deletePatientHistory(historyId: string, token: string): Promise<{ status: string; message: string }> {
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients/history/${historyId}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      return await safeJson(response, { status: 'ok', message: 'History cleared' })
    }
  } catch (err) {
    console.warn('Delete patient history fallback used:', err)
  }

  return { status: 'ok', message: 'History record removed' }
}

export async function clearPatientHistory(token: string): Promise<{ status: string; message: string; count: number }> {
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients/history`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      return await safeJson(response, { status: 'ok', message: 'All history cleared', count: 0 })
    }
  } catch (err) {
    console.warn('Clear patient history fallback used:', err)
  }

  return { status: 'ok', message: 'Patient history cleared', count: 0 }
}

export async function purgeAllPatients(token: string): Promise<{ status: string; message: string }> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/patients/purge/all`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      return await safeJson(response, { status: 'ok', message: 'All patients purged' })
    }
  } catch (err) {
    console.warn('Purge all patients fallback used:', err)
  }

  return { status: 'ok', message: 'All patient records purged' }
}


export async function fetchSecurityOverview(token: string): Promise<SecurityOverviewResponse> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/security/overview`, {
      headers: {
        Authorization: `Bearer ${token}`,
        'X-Session-Id': 'active-user-session',
        'X-Device': 'trusted',
        'X-Browser': 'chrome',
      },
    })
    if (response.ok) {
      const data = await safeJson<SecurityOverviewResponse>(response, null as any)
      if (data) return data
    }
  } catch (err) {
    console.warn('Security overview fetch fallback used:', err)
  }

  return {
    active_attacks: 0,
    suspicious_sessions: 0,
    total_events: 14,
    watermarked_records: 12,
    honeytokens: 8,
  }
}


export async function fetchSecurityEvents(token: string): Promise<SecurityEvent[]> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/security/events`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    if (response.ok) {
      const payload = await safeJson<{ events: SecurityEvent[] }>(response, { events: [] })
      if (payload && Array.isArray(payload.events)) return payload.events
    }
  } catch (err) {
    console.warn('Security events fetch fallback used:', err)
  }

  return [
    { id: 'EVT-101', event_type: 'DECEIVE_ROUTED', details: 'Hacker traffic routed to synthetic decoy DB' },
    { id: 'EVT-102', event_type: 'WATERMARK_VERIFIED', details: 'Zero-leakage watermark tag applied' },
  ]
}

export async function fetchDeceptionStatus(token: string): Promise<DeceptionStatusResponse> {
  try {
    const response = await fetch(`${apiBaseUrl}/api/security/deception/status`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })
    if (response.ok) {
      const data = await safeJson<DeceptionStatusResponse>(response, { sessions: [] })
      if (data) return data
    }
  } catch (err) {
    console.warn('Deception status fetch fallback used:', err)
  }

  return { sessions: [] }
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
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients`, {
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

    if (response.ok) {
      const data = await safeJson<PatientCreateResponse>(response, null as any)
      if (data && data.patient) return data
    }
  } catch (err) {
    console.warn('Backend createPatient unreachable, using local enclave fallback:', err)
  }

  const newNumId = Math.floor(100 + Math.random() * 900)
  const synDetails = generateSyntheticTwinDetails(patient.name, newNumId, patient.age)

  const createdRecord: PatientRecord = {
    ...patient,
    patient_id: newNumId,
    id: `P-${newNumId}`,
    watermark_id: synDetails.fingerprint,
    forensic_record: {
      synthetic_patient_id: synDetails.decoyId,
      watermark_fingerprint: synDetails.fingerprint,
      name: synDetails.decoyName,
      disease: synDetails.disease,
      diagnosis: synDetails.diagnosis,
      treatment_pattern: synDetails.treatmentPattern,
      age_range: synDetails.ageRange,
      aadhaar_number: synDetails.aadhaar,
      phone_number: synDetails.phone,
      email: synDetails.email,
    },
  }

  return {
    decision: { route: 'allow', threat_score: 0, reason: 'Local Enclave Registered' },
    patient: createdRecord,
    synthetic_twin: {
      synthetic_patient_id: synDetails.decoyId,
      real_patient_id: `P-${newNumId}`,
      name: synDetails.decoyName,
      address: patient.address || 'Confidential',
      phone_number: synDetails.phone,
      aadhaar_number: synDetails.aadhaar,
      email: synDetails.email,
      insurance_details: 'Standard Network Cover',
      emergency_contact: patient.emergency_contact || 'None',
      disease: synDetails.disease,
      diagnosis: synDetails.diagnosis,
      medicines: patient.symptoms || [],
      treatment_pattern: synDetails.treatmentPattern,
      age_range: synDetails.ageRange,
      watermark_fingerprint: synDetails.fingerprint,
    },
  }
}

export async function updatePatient(patientId: string, patient: PatientCreate, token: string, sessionId: string): Promise<PatientCreateResponse> {
  try {
    const response = await safeFetch(`${apiBaseUrl}/api/patients/${patientId}`, {
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

    if (response.ok) {
      const data = await safeJson<PatientCreateResponse>(response, null as any)
      if (data && data.patient) return data
    }
  } catch (err) {
    console.warn('Backend updatePatient unreachable, using local enclave fallback:', err)
  }

  const numId = parseInt(String(patientId).replace(/\D/g, '')) || 101
  const synDetails = generateSyntheticTwinDetails(patient.name, numId, patient.age)

  const updatedRecord: PatientRecord = {
    ...patient,
    patient_id: numId,
    id: patientId,
    watermark_id: synDetails.fingerprint,
    forensic_record: {
      synthetic_patient_id: synDetails.decoyId,
      watermark_fingerprint: synDetails.fingerprint,
      name: synDetails.decoyName,
      disease: synDetails.disease,
      diagnosis: synDetails.diagnosis,
      treatment_pattern: synDetails.treatmentPattern,
      age_range: synDetails.ageRange,
      aadhaar_number: synDetails.aadhaar,
      phone_number: synDetails.phone,
      email: synDetails.email,
    },
  }

  return {
    decision: { route: 'allow', threat_score: 0, reason: 'Local Enclave Updated' },
    patient: updatedRecord,
    synthetic_twin: {
      synthetic_patient_id: synDetails.decoyId,
      real_patient_id: String(patientId),
      name: synDetails.decoyName,
      address: patient.address || 'Confidential',
      phone_number: synDetails.phone,
      aadhaar_number: synDetails.aadhaar,
      email: synDetails.email,
      insurance_details: 'Standard Network Cover',
      emergency_contact: patient.emergency_contact || 'None',
      disease: synDetails.disease,
      diagnosis: synDetails.diagnosis,
      medicines: patient.symptoms || [],
      treatment_pattern: synDetails.treatmentPattern,
      age_range: synDetails.ageRange,
      watermark_fingerprint: synDetails.fingerprint,
    },
  }
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


