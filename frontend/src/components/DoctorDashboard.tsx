import React, { useEffect, useState } from 'react'
import type { PatientCreate, PatientRecord, LabResultResponse } from '../api'
import { createPatient, deletePatient, fetchLabResults, fetchPatients, updatePatient } from '../api'
import { DOCTORS_LIST, type DoctorProfile } from './DoctorLoginPage'

interface DoctorDashboardProps {
  token: string
  user: any
  onLogout: () => void
  onSwitchDoctor?: () => void
}

export const DoctorDashboardComponent: React.FC<DoctorDashboardProps> = ({ token, user, onLogout, onSwitchDoctor }) => {
  const [patients, setPatients] = useState<PatientRecord[]>([])
  const [activeTab, setActiveTab] = useState<'roster' | 'register' | 'lab' | 'profile'>('roster')
  const [selectedPatient, setSelectedPatient] = useState<PatientRecord | null>(null)
  const [editingPatientId, setEditingPatientId] = useState<string | null>(null)

  // Resolve doctor profile dynamically from authenticated user
  const currentDoctor: DoctorProfile = DOCTORS_LIST.find((d) =>
    d.username === user?.username ||
    d.id === user?.username ||
    d.altUsername === user?.username ||
    (user?.full_name && user.full_name.toLowerCase().includes(d.name.toLowerCase().replace(/^dr\.\s*/i, '')))
  ) || DOCTORS_LIST[0]

  const loggedInDoctorName = currentDoctor.name

  // Filter patients based on selected department or doctor assignment
  const filteredPatients = patients.filter((p) => {
    const docDept = (currentDoctor.dept || '').trim().toLowerCase()
    const pDept = (p.department || '').trim().toLowerCase()

    // 1. Check department match (e.g. Cardiology, Neurology, Pediatrics, Orthopedics, General Medicine)
    if (docDept && pDept) {
      if (pDept === docDept || pDept.includes(docDept) || docDept.includes(pDept)) {
        return true
      }
    }

    // 2. Check doctor assigned match
    if (p.doctor_assigned) {
      const docClean = currentDoctor.name.replace(/^Dr\.\s*/i, '').trim().toLowerCase()
      const pDocClean = p.doctor_assigned.replace(/^Dr\.\s*/i, '').trim().toLowerCase()
      const docLastName = docClean.split(' ').slice(-1)[0]
      if (pDocClean.includes(docClean) || docClean.includes(pDocClean) || (docLastName && pDocClean.includes(docLastName))) {
        return true
      }
      if (docDept && pDocClean.includes(docDept)) {
        return true
      }
    }

    // 3. Fallback: if General Medicine doctor, also show patients with General / Clinical / Unassigned department
    if ((!p.department || pDept.includes('general') || pDept.includes('clinical')) && (docDept.includes('general') || currentDoctor.id === 'doctor_anita')) {
      return true
    }

    return false
  })

  // Patient form state
  const [form, setForm] = useState<PatientCreate>({
    name: '',
    age: 35,
    disease: '',
    diagnosis: '',
    medicines: [''],
    dosages: [''],
    treatment_pattern: 'Standard Care Protocol',
    gender: 'Female',
    date_of_birth: '',
    blood_group: 'O+',
    phone: '',
    email: '',
    address: '',
    aadhaar: '',
    emergency_contact: '',
    symptoms: [],
    allergies: [],
    doctor_assigned: `${currentDoctor.name} (${currentDoctor.dept})`,
    department: currentDoctor.dept,
    admission_date: new Date().toISOString().slice(0, 10),
    discharge_date: '',
    lab_reports: [],
    medical_images: [],
  })

  useEffect(() => {
    setForm((prev) => ({
      ...prev,
      doctor_assigned: `${currentDoctor.name} (${currentDoctor.dept})`,
      department: currentDoctor.dept,
    }))
  }, [currentDoctor])

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  // Lab Lookup State
  const [labPatientId, setLabPatientId] = useState('P-01')
  const [labResult, setLabResult] = useState<LabResultResponse | null>(null)
  const [labLoading, setLabLoading] = useState(false)
  const [labError, setLabError] = useState('')

  useEffect(() => {
    loadPatients()
    const interval = setInterval(() => {
      loadPatients()
    }, 3000)

    const handleSync = () => {
      loadPatients()
    }

    window.addEventListener('patient_data_changed', handleSync)
    window.addEventListener('storage', handleSync)

    return () => {
      clearInterval(interval)
      window.removeEventListener('patient_data_changed', handleSync)
      window.removeEventListener('storage', handleSync)
    }
  }, [token])

  async function loadPatients() {
    try {
      const res = await fetchPatients(token)
      setPatients(res.patients || [])
    } catch (err) {
      console.warn('Failed to load patient records:', err)
    }
  }

  async function handleDeletePatient(id: string) {
    if (!window.confirm('Are you sure you want to delete this clinical record?')) return
    try {
      await deletePatient(id, token)
      setMessage('Patient record deleted successfully.')
      window.dispatchEvent(new Event('patient_data_changed'))
      await loadPatients()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete patient')
    }
  }

  function handleStartEdit(p: PatientRecord) {
    setEditingPatientId(p.id)
    setForm({
      name: p.name || '',
      age: p.age || 35,
      disease: p.disease || '',
      diagnosis: p.diagnosis || '',
      medicines: p.medicines?.length ? p.medicines : [''],
      dosages: p.dosages?.length ? p.dosages : [''],
      treatment_pattern: p.treatment_pattern || 'Standard Care',
      gender: p.gender || 'Female',
      date_of_birth: p.date_of_birth || '',
      blood_group: p.blood_group || 'O+',
      phone: p.phone || '',
      email: p.email || '',
      address: p.address || '',
      aadhaar: p.aadhaar || '',
      emergency_contact: p.emergency_contact || '',
      symptoms: p.symptoms || [],
      allergies: p.allergies || [],
      doctor_assigned: p.doctor_assigned || 'Dr. Priya Nair (Cardiology)',
      department: p.department || 'Cardiology',
      admission_date: p.admission_date || '',
      discharge_date: p.discharge_date || '',
      lab_reports: p.lab_reports || [],
      medical_images: p.medical_images || [],
    })
    setActiveTab('register')
  }

  async function handleSubmitPatient(e: React.FormEvent) {
    e.preventDefault()
    setIsSubmitting(true)
    setError('')
    setMessage('')

    const sessionId = `doctor-session-${Date.now()}`

    try {
      if (editingPatientId) {
        await updatePatient(editingPatientId, form, token, sessionId)
        setMessage(`Updated clinical details & prescription for ${form.name} successfully.`)
      } else {
        await createPatient(form, token, sessionId)
        setMessage(`Registered new patient record for ${form.name} successfully.`)
      }
      setEditingPatientId(null)
      await loadPatients()
      setActiveTab('roster')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save patient record')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function handleFetchLab(e: React.FormEvent) {
    e.preventDefault()
    setLabLoading(true)
    setLabError('')
    setLabResult(null)

    try {
      const res = await fetchLabResults(labPatientId, token)
      setLabResult(res)
    } catch (err) {
      setLabError(err instanceof Error ? err.message : 'Lab lookup failed')
    } finally {
      setLabLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: '#090d16', color: '#f1f5f9', display: 'flex', flexDirection: 'column' }}>
      
      {/* DOCTOR TOP NAVIGATION BAR */}
      <header style={{ background: 'rgba(15, 23, 42, 0.95)', borderBottom: '1px solid rgba(2, 132, 199, 0.3)', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 50 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #0284c7, #0891b2)', display: 'grid', placeItems: 'center', fontSize: 22, color: '#fff', boxShadow: '0 4px 12px rgba(2,132,199,0.4)' }}>
            👨‍⚕️
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc' }}>
              Doctor Clinical Dashboard
            </h2>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#38bdf8' }}>
              {currentDoctor.name} | License {currentDoctor.license}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <strong style={{ display: 'block', fontSize: '0.85rem', color: '#f8fafc' }}>{currentDoctor.name}</strong>
            <span style={{ fontSize: '0.72rem', color: '#34d399', background: 'rgba(16,185,129,0.15)', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>
              ONLINE • DOCTOR ROLE
            </span>
          </div>
          {onSwitchDoctor ? (
            <button
              onClick={onSwitchDoctor}
              style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid rgba(56,189,248,0.4)', background: 'rgba(56,189,248,0.15)', color: '#38bdf8', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}
            >
              🔄 Switch Doctor
            </button>
          ) : null}
          <button
            onClick={onLogout}
            style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid rgba(239,68,68,0.4)', background: 'rgba(239,68,68,0.15)', color: '#fca5a5', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer' }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* DASHBOARD CONTENT BODY */}
      <main style={{ padding: '32px', maxWidth: 1400, margin: '0 auto', width: '100%', flex: 1 }}>
        
        {/* CLINICAL METRICS CARDS (FILTERED BY LOGGED IN DOCTOR) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 32 }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: 16, padding: 20 }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Assigned Patients</span>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#38bdf8', marginTop: 4 }}>{filteredPatients.length}</div>
            <span style={{ fontSize: '0.75rem', color: '#34d399' }}>
              Assigned to {currentDoctor.name}
            </span>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(16, 185, 129, 0.2)', borderRadius: 16, padding: 20 }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Today's Consultations</span>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#34d399', marginTop: 4 }}>{filteredPatients.length}</div>
            <span style={{ fontSize: '0.75rem', color: '#a7f3d0' }}>Scheduled Clinical Rounds</span>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(168, 85, 247, 0.2)', borderRadius: 16, padding: 20 }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Prescriptions Active</span>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#c084fc', marginTop: 4 }}>
              {filteredPatients.reduce((acc, p) => acc + (p.medicines ? p.medicines.filter((m: string) => m && m.trim().length > 0).length : 0), 0)}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#e9d5ff' }}>Dosages Monitored</span>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: 16, padding: 20 }}>
            <span style={{ fontSize: '0.8rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 700 }}>Lab Reports Pending</span>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: '#fbbf24', marginTop: 4 }}>
              {filteredPatients.reduce((acc, p) => acc + (p.lab_reports ? p.lab_reports.filter((r: string) => r && r.trim().length > 0).length : 0), 0)}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#fde68a' }}>
              {filteredPatients.reduce((acc, p) => acc + (p.lab_reports ? p.lab_reports.filter((r: string) => r && r.trim().length > 0).length : 0), 0) > 0 ? 'ECG & Diagnostic Panels' : '0 Pending Diagnostics'}
            </span>
          </div>
        </div>

        {/* CLINICAL NAVIGATION TABS */}
        <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: 16, marginBottom: 28 }}>
          <button
            onClick={() => setActiveTab('roster')}
            style={{ padding: '10px 20px', borderRadius: 10, border: activeTab === 'roster' ? '1px solid #38bdf8' : '1px solid transparent', background: activeTab === 'roster' ? 'rgba(56, 189, 248, 0.15)' : 'transparent', color: activeTab === 'roster' ? '#38bdf8' : '#94a3b8', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}
          >
            👥 Patient Roster ({filteredPatients.length})
          </button>
          <button
            onClick={() => setActiveTab('lab')}
            style={{ padding: '10px 20px', borderRadius: 10, border: activeTab === 'lab' ? '1px solid #fbbf24' : '1px solid transparent', background: activeTab === 'lab' ? 'rgba(251, 191, 36, 0.15)' : 'transparent', color: activeTab === 'lab' ? '#fbbf24' : '#94a3b8', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}
          >
            🧪 Lab Reports & Vitals
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            style={{ padding: '10px 20px', borderRadius: 10, border: activeTab === 'profile' ? '1px solid #c084fc' : '1px solid transparent', background: activeTab === 'profile' ? 'rgba(192, 132, 252, 0.15)' : 'transparent', color: activeTab === 'profile' ? '#c084fc' : '#94a3b8', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer' }}
          >
            👨‍⚕️ Doctor Credentials
          </button>
        </div>

        {/* NOTIFICATIONS / ALERTS */}
        {message ? (
          <div style={{ padding: '12px 16px', borderRadius: 10, background: 'rgba(16, 185, 129, 0.15)', border: '1px solid #10b981', color: '#34d399', marginBottom: 24 }}>
            ✓ {message}
          </div>
        ) : null}
        {error ? (
          <div style={{ padding: '12px 16px', borderRadius: 10, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid #ef4444', color: '#fca5a5', marginBottom: 24 }}>
            ⚠️ {error}
          </div>
        ) : null}

        {/* TAB 1: PATIENT ROSTER TABLE */}
        {activeTab === 'roster' && (
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(56, 189, 248, 0.2)', borderRadius: 20, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: 10 }}>
                👥 Clinical Patient Roster — {currentDoctor.name}
              </h3>
              <span style={{ padding: '4px 12px', borderRadius: 20, background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', fontWeight: 700, fontSize: '0.8rem' }}>
                {filteredPatients.length} Active Patients
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
                    <th style={{ padding: '12px 16px' }}>Patient ID</th>
                    <th style={{ padding: '12px 16px' }}>Patient Name</th>
                    <th style={{ padding: '12px 16px' }}>Age / Gender</th>
                    <th style={{ padding: '12px 16px' }}>Blood Group</th>
                    <th style={{ padding: '12px 16px' }}>Disease / Diagnosis</th>
                    <th style={{ padding: '12px 16px' }}>Prescribed Medicines</th>
                    <th style={{ padding: '12px 16px' }}>Doctor Assigned</th>
                    <th style={{ padding: '12px 16px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPatients.length === 0 ? (
                    <tr>
                      <td colSpan={8} style={{ padding: '40px 16px', textAlign: 'center', color: '#94a3b8' }}>
                        🏥 No patient records currently assigned to {currentDoctor.name}.
                        <br />
                        <span style={{ fontSize: '0.8rem', color: '#64748b', marginTop: 6, display: 'inline-block' }}>
                          Patient records registered under your department by Administrator will appear here automatically.
                        </span>
                      </td>
                    </tr>
                  ) : (
                    filteredPatients.map((p) => (
                      <tr key={p.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                        <td style={{ padding: '14px 16px', fontWeight: 700, color: '#38bdf8' }}>{p.id || `P-${p.patient_id}`}</td>
                        <td style={{ padding: '14px 16px', fontWeight: 600, color: '#f8fafc' }}>{p.name}</td>
                        <td style={{ padding: '14px 16px', color: '#cbd5e1' }}>{p.age} yrs | {p.gender || 'Female'}</td>
                        <td style={{ padding: '14px 16px', color: '#f43f5e', fontWeight: 700 }}>{p.blood_group || 'O+'}</td>
                        <td style={{ padding: '14px 16px', color: '#cbd5e1' }}>
                          <div style={{ fontWeight: 700, color: '#fbbf24' }}>{p.disease}</div>
                          <div style={{ fontSize: '0.78rem', color: '#94a3b8' }}>{p.diagnosis}</div>
                        </td>
                        <td style={{ padding: '14px 16px', color: '#34d399' }}>
                          {p.medicines?.length ? p.medicines.join(', ') : 'Amlodipine 5mg'}
                        </td>
                        <td style={{ padding: '14px 16px', color: '#cbd5e1' }}>
                          {p.doctor_assigned || 'Dr. Priya Nair'}
                        </td>
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <button
                              onClick={() => setSelectedPatient(p)}
                              style={{ padding: '6px 12px', borderRadius: 8, background: 'rgba(56, 189, 248, 0.15)', border: '1px solid rgba(56, 189, 248, 0.3)', color: '#38bdf8', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}
                            >
                              View Record
                            </button>
                            <button
                              onClick={() => handleStartEdit(p)}
                              style={{ padding: '6px 12px', borderRadius: 8, background: 'rgba(52, 211, 153, 0.15)', border: '1px solid rgba(52, 211, 153, 0.3)', color: '#34d399', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}
                            >
                              Update Note
                            </button>
                            <button
                              onClick={() => handleDeletePatient(p.id)}
                              style={{ padding: '6px 12px', borderRadius: 8, background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.3)', color: '#fca5a5', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer' }}
                            >
                              Delete
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* TAB 2: EDIT PATIENT CLINICAL RECORD FORM */}
        {activeTab === 'register' && (
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(52, 211, 153, 0.3)', borderRadius: 20, padding: 32, maxWidth: 800 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: '1.2rem', color: '#f8fafc' }}>
                ✍️ Update Clinical Record for Patient #{editingPatientId || 'Record'}
              </h3>
              <button
                type="button"
                onClick={() => {
                  setEditingPatientId(null)
                  setActiveTab('roster')
                }}
                style={{ padding: '6px 14px', borderRadius: 8, background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#cbd5e1', fontSize: '0.85rem', cursor: 'pointer' }}
              >
                ✖ Cancel & Back to Roster
              </button>
            </div>

            <form onSubmit={handleSubmitPatient} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Patient Full Name *
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Age *
                <input
                  type="number"
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: parseInt(e.target.value) || 0 })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Gender
                <select
                  value={form.gender || 'Female'}
                  onChange={(e) => setForm({ ...form, gender: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Other">Other</option>
                </select>
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Blood Group
                <input
                  value={form.blood_group || 'O+'}
                  onChange={(e) => setForm({ ...form, blood_group: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Primary Disease / Condition *
                <input
                  value={form.disease}
                  onChange={(e) => setForm({ ...form, disease: e.target.value })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Clinical Diagnosis *
                <input
                  value={form.diagnosis}
                  onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1', gridColumn: 'span 2' }}>
                Prescribed Medicines (comma separated)
                <input
                  value={form.medicines.join(', ')}
                  onChange={(e) => setForm({ ...form, medicines: e.target.value.split(',').map((s) => s.trim()) })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1', gridColumn: 'span 2' }}>
                Treatment Pattern / Protocol
                <input
                  value={form.treatment_pattern}
                  onChange={(e) => setForm({ ...form, treatment_pattern: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Attending Doctor Assigned
                <select
                  value={form.doctor_assigned || 'Dr. Priya Nair (Cardiology)'}
                  onChange={(e) => setForm({ ...form, doctor_assigned: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                >
                  <option value="Dr. Priya Nair (Cardiology)">Dr. Priya Nair (Cardiology)</option>
                  <option value="Dr. Ananya Sharma (Neurology)">Dr. Ananya Sharma (Neurology)</option>
                  <option value="Dr. Rajesh Kumar (Oncology)">Dr. Rajesh Kumar (Oncology)</option>
                </select>
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#cbd5e1' }}>
                Phone Number
                <input
                  value={form.phone || ''}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff' }}
                />
              </label>

              <div style={{ gridColumn: 'span 2', display: 'flex', gap: 12, marginTop: 12 }}>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{ padding: '12px 24px', borderRadius: 10, background: 'linear-gradient(135deg, #0284c7, #2563eb)', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer' }}
                >
                  {isSubmitting ? 'Saving Record...' : editingPatientId ? 'Save Clinical Updates' : 'Register Patient Record'}
                </button>
                {editingPatientId && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingPatientId(null)
                      setActiveTab('roster')
                    }}
                    style={{ padding: '12px 24px', borderRadius: 10, background: 'rgba(255,255,255,0.05)', color: '#94a3b8', border: '1px solid rgba(255,255,255,0.1)', fontWeight: 700, cursor: 'pointer' }}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>
        )}

        {/* TAB 3: LAB REPORTS & VITALS */}
        {activeTab === 'lab' && (
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(251, 191, 36, 0.3)', borderRadius: 20, padding: 32, maxWidth: 650 }}>
            <h3 style={{ margin: '0 0 20px', fontSize: '1.2rem', color: '#f8fafc' }}>
              🧪 Fetch Patient Lab Diagnostics
            </h3>

            <form onSubmit={handleFetchLab} style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
              <input
                value={labPatientId}
                onChange={(e) => setLabPatientId(e.target.value)}
                placeholder="Enter Patient ID (e.g. P-01)"
                required
                style={{ flex: 1, padding: '12px 16px', borderRadius: 10, border: '1px solid rgba(255,255,255,0.1)', background: '#1e293b', color: '#fff', fontSize: '0.95rem' }}
              />
              <button
                type="submit"
                disabled={labLoading}
                style={{ padding: '12px 20px', borderRadius: 10, background: '#f59e0b', color: '#0f172a', border: 'none', fontWeight: 800, cursor: 'pointer' }}
              >
                {labLoading ? 'Fetching...' : 'Fetch Lab Report'}
              </button>
            </form>

            {labError ? (
              <div style={{ padding: 12, borderRadius: 8, background: 'rgba(239,68,68,0.15)', color: '#fca5a5' }}>
                ⚠️ {labError}
              </div>
            ) : null}

            {labResult ? (
              <div style={{ background: '#1e293b', padding: 20, borderRadius: 12, border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                <h4 style={{ margin: '0 0 10px', color: '#fbbf24' }}>Official Hospital Diagnostic Result</h4>
                <div style={{ display: 'grid', gap: 8, fontSize: '0.9rem', color: '#e2e8f0' }}>
                  <div><strong>Patient ID:</strong> {labResult.patient_id}</div>
                  <div><strong>Diagnostic Test:</strong> {labResult.test_name}</div>
                  <div><strong>Result Summary:</strong> <span style={{ color: '#34d399', fontWeight: 700 }}>{labResult.result}</span></div>
                  <div><strong>Report Timestamp:</strong> {new Date(labResult.reported_at).toLocaleString()}</div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* TAB 4: DOCTOR CREDENTIALS PROFILE */}
        {activeTab === 'profile' && (
          <div style={{ background: 'rgba(15, 23, 42, 0.8)', border: `1px solid ${currentDoctor.accent}55`, borderRadius: 20, padding: 32, maxWidth: 650 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
              <div style={{ width: 64, height: 64, borderRadius: 20, background: `linear-gradient(135deg, ${currentDoctor.accent}, #0284c7)`, display: 'grid', placeItems: 'center', fontSize: 32, color: '#fff' }}>
                {currentDoctor.icon}
              </div>
              <div>
                <h3 style={{ margin: 0, color: '#f8fafc', fontSize: '1.4rem' }}>{currentDoctor.name}</h3>
                <span style={{ color: currentDoctor.accent, fontWeight: 700, fontSize: '0.9rem' }}>{currentDoctor.title}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gap: 12, fontSize: '0.9rem', color: '#e2e8f0' }}>
              <div><strong>Medical License ID:</strong> {currentDoctor.license} (State Medical Council)</div>
              <div><strong>Specialization:</strong> {currentDoctor.title}</div>
              <div><strong>Department:</strong> Department of {currentDoctor.dept}</div>
              <div><strong>Hospital Email:</strong> {user?.email || (currentDoctor.id.replace('doctor_', '') + '@stjude.org')}</div>
              <div><strong>Consultation Rounds:</strong> Monday – Saturday | 09:00 AM – 04:00 PM</div>
              <div><strong>Security Clearance:</strong> Certified Clinical Staff (EHR Access Tier 2)</div>
            </div>
          </div>
        )}

        {/* PATIENT DETAILS MODAL */}
        {selectedPatient && (
          <div style={{ position: 'fixed', inset: 0, zIndex: 999, background: 'rgba(2, 6, 23, 0.85)', backdropFilter: 'blur(10px)', display: 'grid', placeItems: 'center', padding: 20 }}>
            <div style={{ width: '100%', maxWidth: 550, background: '#0f172a', borderRadius: 24, padding: 32, border: '1px solid rgba(56, 189, 248, 0.4)', color: '#f8fafc', position: 'relative' }}>
              <button
                onClick={() => setSelectedPatient(null)}
                style={{ position: 'absolute', top: 20, right: 20, background: 'none', border: 'none', color: '#94a3b8', fontSize: '1.2rem', cursor: 'pointer' }}
              >
                ✕
              </button>
              <h3 style={{ margin: '0 0 16px', color: '#38bdf8' }}>Clinical Record: {selectedPatient.name}</h3>
              <div style={{ display: 'grid', gap: 10, fontSize: '0.9rem' }}>
                <div><strong>Patient ID:</strong> {selectedPatient.id || selectedPatient.patient_id}</div>
                <div><strong>Age / Gender:</strong> {selectedPatient.age} yrs | {selectedPatient.gender || 'Female'}</div>
                <div><strong>Blood Group:</strong> {selectedPatient.blood_group || 'O+'}</div>
                <div><strong>Condition / Disease:</strong> {selectedPatient.disease}</div>
                <div><strong>Diagnosis:</strong> {selectedPatient.diagnosis}</div>
                <div><strong>Medicines:</strong> {selectedPatient.medicines?.join(', ')}</div>
                <div><strong>Dosages:</strong> {selectedPatient.dosages?.join(', ') || '1 OD'}</div>
                <div><strong>Treatment Pattern:</strong> {selectedPatient.treatment_pattern || 'Standard Care'}</div>
                <div><strong>Doctor Assigned:</strong> {selectedPatient.doctor_assigned || 'Dr. Priya Nair'}</div>
              </div>
            </div>
          </div>
        )}

      </main>
    </div>
  )
}
