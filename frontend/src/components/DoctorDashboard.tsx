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
    <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', display: 'flex', flexDirection: 'column' }}>
      
      {/* DOCTOR TOP NAVIGATION BAR */}
      <header style={{ background: '#ffffff', borderBottom: '1px solid #e2e8f0', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 50, boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #0284c7, #0369a1)', display: 'grid', placeItems: 'center', fontSize: 22, color: '#fff', boxShadow: '0 4px 12px rgba(2,132,199,0.25)' }}>
            👨‍⚕️
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
              Doctor Clinical Dashboard
            </h2>
            <p style={{ margin: 0, fontSize: '0.82rem', color: '#0284c7', fontWeight: 600 }}>
              {currentDoctor.name} | License {currentDoctor.license}
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{ textAlign: 'right' }}>
            <strong style={{ display: 'block', fontSize: '0.88rem', color: '#0f172a', fontWeight: 800 }}>{currentDoctor.name}</strong>
            <span style={{ fontSize: '0.72rem', color: '#15803d', background: '#dcfce7', border: '1px solid #bbf7d0', padding: '2px 8px', borderRadius: 6, fontWeight: 700 }}>
              ONLINE • DOCTOR ROLE
            </span>
          </div>
          {onSwitchDoctor ? (
            <button
              onClick={onSwitchDoctor}
              style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid #bae6fd', background: '#e0f2fe', color: '#0369a1', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
            >
              🔄 Switch Doctor
            </button>
          ) : null}
          <button
            onClick={onLogout}
            style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid #fecaca', background: '#fee2e2', color: '#b91c1c', fontWeight: 700, fontSize: '0.85rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* DASHBOARD CONTENT BODY */}
      <main style={{ padding: '32px', maxWidth: 1400, margin: '0 auto', width: '100%', flex: 1 }}>
        
        {/* CLINICAL METRICS CARDS (FILTERED BY LOGGED IN DOCTOR) */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 20, marginBottom: 32 }}>
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderTop: '4px solid #0284c7', borderRadius: 16, padding: 20, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <span style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Assigned Patients</span>
            <div style={{ fontSize: '2.1rem', fontWeight: 900, color: '#0f172a', marginTop: 4 }}>{filteredPatients.length}</div>
            <span style={{ fontSize: '0.75rem', color: '#0369a1', fontWeight: 600 }}>
              Assigned to {currentDoctor.name}
            </span>
          </div>

          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderTop: '4px solid #059669', borderRadius: 16, padding: 20, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <span style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Today's Consultations</span>
            <div style={{ fontSize: '2.1rem', fontWeight: 900, color: '#0f172a', marginTop: 4 }}>{filteredPatients.length}</div>
            <span style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: 600 }}>Scheduled Clinical Rounds</span>
          </div>

          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderTop: '4px solid #7c3aed', borderRadius: 16, padding: 20, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <span style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Prescriptions Active</span>
            <div style={{ fontSize: '2.1rem', fontWeight: 900, color: '#0f172a', marginTop: 4 }}>
              {filteredPatients.reduce((acc, p) => acc + (p.medicines ? p.medicines.filter((m: string) => m && m.trim().length > 0).length : 0), 0)}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#6d28d9', fontWeight: 600 }}>Dosages Monitored</span>
          </div>

          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderTop: '4px solid #d97706', borderRadius: 16, padding: 20, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <span style={{ fontSize: '0.78rem', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>Lab Reports Pending</span>
            <div style={{ fontSize: '2.1rem', fontWeight: 900, color: '#0f172a', marginTop: 4 }}>
              {filteredPatients.reduce((acc, p) => acc + (p.lab_reports ? p.lab_reports.filter((r: string) => r && r.trim().length > 0).length : 0), 0)}
            </div>
            <span style={{ fontSize: '0.75rem', color: '#b45309', fontWeight: 600 }}>
              {filteredPatients.reduce((acc, p) => acc + (p.lab_reports ? p.lab_reports.filter((r: string) => r && r.trim().length > 0).length : 0), 0) > 0 ? 'ECG & Diagnostic Panels' : '0 Pending Diagnostics'}
            </span>
          </div>
        </div>

        {/* CLINICAL NAVIGATION TABS */}
        <div style={{ display: 'flex', gap: 12, borderBottom: '1px solid #e2e8f0', paddingBottom: 16, marginBottom: 28 }}>
          <button
            onClick={() => setActiveTab('roster')}
            style={{ padding: '10px 20px', borderRadius: 10, border: activeTab === 'roster' ? '1px solid #0284c7' : '1px solid transparent', background: activeTab === 'roster' ? '#e0f2fe' : 'transparent', color: activeTab === 'roster' ? '#0369a1' : '#475569', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
          >
            👥 Patient Roster ({filteredPatients.length})
          </button>
          <button
            onClick={() => setActiveTab('lab')}
            style={{ padding: '10px 20px', borderRadius: 10, border: activeTab === 'lab' ? '1px solid #d97706' : '1px solid transparent', background: activeTab === 'lab' ? '#fef3c7' : 'transparent', color: activeTab === 'lab' ? '#92400e' : '#475569', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
          >
            🧪 Lab Reports & Vitals
          </button>
          <button
            onClick={() => setActiveTab('profile')}
            style={{ padding: '10px 20px', borderRadius: 10, border: activeTab === 'profile' ? '1px solid #7c3aed' : '1px solid transparent', background: activeTab === 'profile' ? '#f5f3ff' : 'transparent', color: activeTab === 'profile' ? '#6d28d9' : '#475569', fontWeight: 700, fontSize: '0.9rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
          >
            👨‍⚕️ Doctor Credentials
          </button>
        </div>

        {/* NOTIFICATIONS / ALERTS */}
        {message ? (
          <div style={{ padding: '12px 16px', borderRadius: 10, background: '#dcfce7', border: '1px solid #bbf7d0', color: '#15803d', marginBottom: 24, fontWeight: 600 }}>
            ✓ {message}
          </div>
        ) : null}
        {error ? (
          <div style={{ padding: '12px 16px', borderRadius: 10, background: '#fee2e2', border: '1px solid #fecaca', color: '#b91c1c', marginBottom: 24, fontWeight: 600 }}>
            ⚠️ {error}
          </div>
        ) : null}

        {/* TAB 1: PATIENT ROSTER TABLE */}
        {activeTab === 'roster' && (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 18, padding: 24, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                👥 Clinical Patient Roster — {currentDoctor.name}
              </h3>
              <span style={{ padding: '4px 12px', borderRadius: 20, background: '#e0f2fe', border: '1px solid #bae6fd', color: '#0369a1', fontWeight: 700, fontSize: '0.8rem' }}>
                {filteredPatients.length} Active Patients
              </span>
            </div>

            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0', color: '#475569' }}>
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
                      <td colSpan={8} style={{ padding: '40px 16px', textAlign: 'center', color: '#64748b' }}>
                        🏥 No patient records currently assigned to {currentDoctor.name}.
                        <br />
                        <span style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: 6, display: 'inline-block' }}>
                          Patient records registered under your department by Administrator will appear here automatically.
                        </span>
                      </td>
                    </tr>
                  ) : (
                    filteredPatients.map((p) => (
                      <tr key={p.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                        <td style={{ padding: '14px 16px', fontWeight: 800, color: '#0284c7' }}>{p.id || `P-${p.patient_id}`}</td>
                        <td style={{ padding: '14px 16px', fontWeight: 700, color: '#0f172a' }}>{p.name}</td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>{p.age} yrs | {p.gender || 'Female'}</td>
                        <td style={{ padding: '14px 16px', color: '#b91c1c', fontWeight: 800 }}>{p.blood_group || 'O+'}</td>
                        <td style={{ padding: '14px 16px', color: '#334155' }}>
                          <div style={{ fontWeight: 700, color: '#b45309' }}>{p.disease}</div>
                          <div style={{ fontSize: '0.8rem', color: '#64748b' }}>{p.diagnosis}</div>
                        </td>
                        <td style={{ padding: '14px 16px', color: '#15803d', fontWeight: 600 }}>
                          {p.medicines?.length ? p.medicines.join(', ') : 'Amlodipine 5mg'}
                        </td>
                        <td style={{ padding: '14px 16px', color: '#475569' }}>
                          {p.doctor_assigned || 'Dr. Priya Nair'}
                        </td>
                        <td style={{ padding: '14px 16px' }}>
                          <div style={{ display: 'flex', gap: 8 }}>
                            <button
                              onClick={() => setSelectedPatient(p)}
                              style={{ padding: '6px 12px', borderRadius: 8, background: '#e0f2fe', border: '1px solid #bae6fd', color: '#0369a1', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
                            >
                              View Record
                            </button>
                            <button
                              onClick={() => handleStartEdit(p)}
                              style={{ padding: '6px 12px', borderRadius: 8, background: '#dcfce7', border: '1px solid #bbf7d0', color: '#15803d', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
                            >
                              Update Note
                            </button>
                            <button
                              onClick={() => handleDeletePatient(p.id)}
                              style={{ padding: '6px 12px', borderRadius: 8, background: '#fee2e2', border: '1px solid #fecaca', color: '#b91c1c', fontWeight: 700, fontSize: '0.8rem', cursor: 'pointer', transition: 'all 0.15s ease' }}
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
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 32, maxWidth: 800, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <h3 style={{ margin: 0, fontSize: '1.25rem', color: '#0f172a', fontWeight: 800 }}>
                ✍️ Update Clinical Record for Patient #{editingPatientId || 'Record'}
              </h3>
              <button
                type="button"
                onClick={() => {
                  setEditingPatientId(null)
                  setActiveTab('roster')
                }}
                style={{ padding: '6px 14px', borderRadius: 8, background: '#f1f5f9', border: '1px solid #cbd5e1', color: '#475569', fontSize: '0.85rem', cursor: 'pointer', fontWeight: 600 }}
              >
                ✖ Cancel & Back to Roster
              </button>
            </div>

            <form onSubmit={handleSubmitPatient} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Patient Full Name *
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Age *
                <input
                  type="number"
                  value={form.age}
                  onChange={(e) => setForm({ ...form, age: parseInt(e.target.value) || 0 })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Gender
                <select
                  value={form.gender || 'Female'}
                  onChange={(e) => setForm({ ...form, gender: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                >
                  <option value="Female">Female</option>
                  <option value="Male">Male</option>
                  <option value="Other">Other</option>
                </select>
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Blood Group
                <input
                  value={form.blood_group || 'O+'}
                  onChange={(e) => setForm({ ...form, blood_group: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Primary Disease / Condition *
                <input
                  value={form.disease}
                  onChange={(e) => setForm({ ...form, disease: e.target.value })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Clinical Diagnosis *
                <input
                  value={form.diagnosis}
                  onChange={(e) => setForm({ ...form, diagnosis: e.target.value })}
                  required
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600, gridColumn: 'span 2' }}>
                Prescribed Medicines (comma separated)
                <input
                  value={form.medicines.join(', ')}
                  onChange={(e) => setForm({ ...form, medicines: e.target.value.split(',').map((s) => s.trim()) })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600, gridColumn: 'span 2' }}>
                Treatment Pattern / Protocol
                <input
                  value={form.treatment_pattern}
                  onChange={(e) => setForm({ ...form, treatment_pattern: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Attending Doctor Assigned
                <select
                  value={form.doctor_assigned || 'Dr. Priya Nair (Cardiology)'}
                  onChange={(e) => setForm({ ...form, doctor_assigned: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                >
                  <option value="Dr. Priya Nair (Cardiology)">Dr. Priya Nair (Cardiology)</option>
                  <option value="Dr. Ananya Sharma (Neurology)">Dr. Ananya Sharma (Neurology)</option>
                  <option value="Dr. Rajesh Kumar (Oncology)">Dr. Rajesh Kumar (Oncology)</option>
                </select>
              </label>

              <label style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.85rem', color: '#334155', fontWeight: 600 }}>
                Phone Number
                <input
                  value={form.phone || ''}
                  onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  style={{ padding: '10px 14px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a' }}
                />
              </label>

              <div style={{ gridColumn: 'span 2', display: 'flex', gap: 12, marginTop: 12 }}>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  style={{ padding: '12px 24px', borderRadius: 10, background: 'linear-gradient(135deg, #0284c7, #0369a1)', color: '#fff', border: 'none', fontWeight: 700, cursor: 'pointer', boxShadow: '0 4px 14px rgba(2, 132, 199, 0.25)' }}
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
                    style={{ padding: '12px 24px', borderRadius: 10, background: '#f1f5f9', color: '#475569', border: '1px solid #cbd5e1', fontWeight: 700, cursor: 'pointer' }}
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
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 32, maxWidth: 650, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <h3 style={{ margin: '0 0 20px', fontSize: '1.25rem', color: '#0f172a', fontWeight: 800 }}>
              🧪 Fetch Patient Lab Diagnostics
            </h3>

            <form onSubmit={handleFetchLab} style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
              <input
                value={labPatientId}
                onChange={(e) => setLabPatientId(e.target.value)}
                placeholder="Enter Patient ID (e.g. P-01)"
                required
                style={{ flex: 1, padding: '12px 16px', borderRadius: 10, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a', fontSize: '0.95rem' }}
              />
              <button
                type="submit"
                disabled={labLoading}
                style={{ padding: '12px 20px', borderRadius: 10, background: 'linear-gradient(135deg, #d97706, #b45309)', color: '#ffffff', border: 'none', fontWeight: 800, cursor: 'pointer', boxShadow: '0 4px 14px rgba(217, 119, 6, 0.25)' }}
              >
                {labLoading ? 'Fetching...' : 'Fetch Lab Report'}
              </button>
            </form>

            {labError ? (
              <div style={{ padding: 12, borderRadius: 8, background: '#fee2e2', border: '1px solid #fecaca', color: '#b91c1c', fontWeight: 600 }}>
                ⚠️ {labError}
              </div>
            ) : null}

            {labResult ? (
              <div style={{ background: '#f8fafc', padding: 20, borderRadius: 14, border: '1px solid #e2e8f0' }}>
                <h4 style={{ margin: '0 0 10px', color: '#b45309', fontWeight: 800 }}>Official Hospital Diagnostic Result</h4>
                <div style={{ display: 'grid', gap: 8, fontSize: '0.9rem', color: '#334155' }}>
                  <div><strong>Patient ID:</strong> {labResult.patient_id}</div>
                  <div><strong>Diagnostic Test:</strong> {labResult.test_name}</div>
                  <div><strong>Result Summary:</strong> <span style={{ color: '#15803d', fontWeight: 800 }}>{labResult.result}</span></div>
                  <div><strong>Report Timestamp:</strong> {new Date(labResult.reported_at).toLocaleString()}</div>
                </div>
              </div>
            ) : null}
          </div>
        )}

        {/* TAB 4: DOCTOR CREDENTIALS PROFILE */}
        {activeTab === 'profile' && (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 32, maxWidth: 650, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 24 }}>
              <div style={{ width: 64, height: 64, borderRadius: 20, background: `linear-gradient(135deg, ${currentDoctor.accent}, #0369a1)`, display: 'grid', placeItems: 'center', fontSize: 32, color: '#fff', boxShadow: '0 4px 14px rgba(2,132,199,0.25)' }}>
                {currentDoctor.icon}
              </div>
              <div>
                <h3 style={{ margin: 0, color: '#0f172a', fontSize: '1.4rem', fontWeight: 800 }}>{currentDoctor.name}</h3>
                <span style={{ color: '#0284c7', fontWeight: 700, fontSize: '0.9rem' }}>{currentDoctor.title}</span>
              </div>
            </div>

            <div style={{ display: 'grid', gap: 12, fontSize: '0.9rem', color: '#334155' }}>
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
          <div style={{ position: 'fixed', inset: 0, zIndex: 999, background: 'rgba(15, 23, 42, 0.5)', backdropFilter: 'blur(8px)', display: 'grid', placeItems: 'center', padding: 20 }}>
            <div style={{ width: '100%', maxWidth: 550, background: '#ffffff', borderRadius: 24, padding: 32, border: '1px solid #e2e8f0', color: '#0f172a', position: 'relative', boxShadow: '0 25px 50px -12px rgba(15, 23, 42, 0.15)' }}>
              <button
                onClick={() => setSelectedPatient(null)}
                style={{ position: 'absolute', top: 20, right: 20, background: 'none', border: 'none', color: '#64748b', fontSize: '1.4rem', cursor: 'pointer' }}
              >
                ✕
              </button>
              <h3 style={{ margin: '0 0 16px', color: '#0284c7', fontWeight: 800, fontSize: '1.3rem' }}>Clinical Record: {selectedPatient.name}</h3>
              <div style={{ display: 'grid', gap: 10, fontSize: '0.9rem', color: '#334155' }}>
                <div><strong>Patient ID:</strong> {selectedPatient.id || selectedPatient.patient_id}</div>
                <div><strong>Age / Gender:</strong> {selectedPatient.age} yrs | {selectedPatient.gender || 'Female'}</div>
                <div><strong>Blood Group:</strong> <span style={{ color: '#b91c1c', fontWeight: 800 }}>{selectedPatient.blood_group || 'O+'}</span></div>
                <div><strong>Condition / Disease:</strong> {selectedPatient.disease}</div>
                <div><strong>Diagnosis:</strong> {selectedPatient.diagnosis}</div>
                <div><strong>Medicines:</strong> <span style={{ color: '#15803d', fontWeight: 700 }}>{selectedPatient.medicines?.join(', ')}</span></div>
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
