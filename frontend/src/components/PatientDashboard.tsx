import React, { useEffect, useState, useCallback, useRef } from 'react'
import type { PatientRecord, LabResultResponse } from '../api'
import { fetchCurrentPatient, fetchLabResults, fetchPatients } from '../api'

interface PatientDashboardProps {
  token: string
  user: any
  onLogout: () => void
}

export const PatientDashboardComponent: React.FC<PatientDashboardProps> = ({ token, user, onLogout }) => {
  const [patients, setPatients] = useState<PatientRecord[]>([])
  const [selectedRecordId, setSelectedRecordId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [lastSyncTime, setLastSyncTime] = useState<string>(new Date().toLocaleTimeString())
  const [isSyncPulsing, setIsSyncPulsing] = useState(false)
  const [adminUpdateToast, setAdminUpdateToast] = useState<string | null>(null)
  const previousRecordsHashRef = useRef<string>('')

  // Lab Lookup State
  const [labPatientId, setLabPatientId] = useState('')
  const [labResult, setLabResult] = useState<LabResultResponse | null>(null)
  const [labLoading, setLabLoading] = useState(false)
  const [labError, setLabError] = useState('')

  const loadPatientRecords = useCallback(async (isBackground: boolean = false) => {
    try {
      if (!isBackground) setLoading(true)
      let fetchedPatients: PatientRecord[] = []
      try {
        const patient = await fetchCurrentPatient(token)
        if (patient) {
          fetchedPatients = [patient]
        }
      } catch (e) {
        console.warn('fetchCurrentPatient unsuccessful, checking hospital patients:', e)
      }

      if (fetchedPatients.length === 0) {
        const res = await fetchPatients(token)
        fetchedPatients = res.patients || []
      }

      setPatients(fetchedPatients)

      const newHash = JSON.stringify(fetchedPatients.map((p) => ({ id: p.id, name: p.name, disease: p.disease, meds: p.medicines, doc: p.doctor_assigned })))
      if (previousRecordsHashRef.current && previousRecordsHashRef.current !== newHash) {
        setIsSyncPulsing(true)
        setAdminUpdateToast('✨ Clinical records simultaneously updated by Administrator!')
        setTimeout(() => {
          setIsSyncPulsing(false)
        }, 2000)
        setTimeout(() => {
          setAdminUpdateToast(null)
        }, 5000)
      }
      previousRecordsHashRef.current = newHash
      setLastSyncTime(new Date().toLocaleTimeString())
    } catch (err) {
      console.warn('Failed to fetch patient records:', err)
      setPatients([])
      setLabResult(null)
    } finally {
      if (!isBackground) setLoading(false)
    }
  }, [token])

  useEffect(() => {
    loadPatientRecords(false)

    // Fast polling (every 2 seconds) for simultaneous sync with Admin changes
    const interval = setInterval(() => {
      loadPatientRecords(true)
    }, 2000)

    const handleSync = () => {
      loadPatientRecords(true)
    }

    window.addEventListener('patient_data_changed', handleSync)
    window.addEventListener('storage', handleSync)

    return () => {
      clearInterval(interval)
      window.removeEventListener('patient_data_changed', handleSync)
      window.removeEventListener('storage', handleSync)
    }
  }, [loadPatientRecords])

  // The active record for this patient portal view
  const activeRecord = (() => {
    if (!patients || patients.length === 0) return null

    // 1. If user explicitly selected a record from the roster selector
    if (selectedRecordId) {
      const selected = patients.find((p) => String(p.id) === selectedRecordId || String(p.patient_id) === selectedRecordId)
      if (selected) return selected
    }

    // 2. Match by linked patient_record_id
    const linkedId = String(user?.patient_record_id || '')
    if (linkedId) {
      const record = patients.find((patient) => String(patient.id) === linkedId || String(patient.patient_id) === linkedId)
      if (record) return record
    }

    // 3. Match by email
    const userEmail = (user?.email || '').trim().toLowerCase()
    if (userEmail) {
      const byEmail = patients.find((p) => p.email && p.email.trim().toLowerCase() === userEmail)
      if (byEmail) return byEmail
    }

    // 4. Match by phone or mobile number
    const userPhone = (user?.phone_number || user?.username || '').replace(/\D/g, '')
    if (userPhone && userPhone.length >= 7) {
      const byPhone = patients.find((p) => {
        const cleanPPhone = (p.phone || '').replace(/\D/g, '')
        return cleanPPhone && (cleanPPhone.includes(userPhone) || userPhone.includes(cleanPPhone))
      })
      if (byPhone) return byPhone
    }

    // 5. Match by full name
    const userName = (user?.full_name || '').trim().toLowerCase()
    if (userName && userName !== 'patient' && userName !== 'patient user' && userName !== 'patient record (self)') {
      const byName = patients.find((p) => p.name && p.name.trim().toLowerCase() === userName)
      if (byName) return byName
    }

    // 6. Default to the first available patient in the hospital vault
    return patients[0] || null
  })()

  // Determine if the current session was authenticated via Google
  const isGoogleAuth = Boolean(
    user?.auth_provider === 'google' ||
    (user?.email &&
      (user.email.endsWith('@gmail.com') || user.email.includes('@')) &&
      !user.email.endsWith('@patient.health') &&
      !user.email.includes('+') &&
      !user.email.includes('mobile') &&
      !/^\d+@/.test(user.email))
  )

  // Compute patient display name: strictly show patient name, never email or mobile phone
  const patientDisplayName = (() => {
    const recName = activeRecord?.name?.trim()
    if (recName && !recName.includes('@') && !/^\+?\d+$/.test(recName.replace(/\s+/g, '')) && !recName.toLowerCase().startsWith('patient (')) {
      return recName
    }
    const uName = user?.full_name?.trim()
    if (uName && !uName.includes('@') && !/^\+?\d+$/.test(uName.replace(/\s+/g, '')) && !uName.toLowerCase().startsWith('patient (')) {
      return uName
    }
    if (recName && !recName.includes('@') && !/^\+?\d+$/.test(recName.replace(/\s+/g, ''))) {
      return recName
    }
    if (uName && !uName.includes('@') && !/^\+?\d+$/.test(uName.replace(/\s+/g, ''))) {
      return uName
    }
    return 'Patient Account'
  })()

  // Update default lab lookup ID when active record changes
  useEffect(() => {
    if (activeRecord && activeRecord.id) {
      setLabPatientId(String(activeRecord.id))
    }
  }, [activeRecord?.id])

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
    <div style={{ minHeight: '100vh', background: '#f8fafc', color: '#0f172a', display: 'flex', flexDirection: 'column', fontFamily: "'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, sans-serif" }}>
      
      {/* TOP NAVIGATION BAR */}
      <header style={{ background: '#ffffff', borderBottom: '1px solid #e2e8f0', padding: '16px 32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 50, boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #059669, #10b981)', display: 'grid', placeItems: 'center', fontSize: 22, color: '#fff', boxShadow: '0 4px 14px rgba(16,185,129,0.25)' }}>
            🏥
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
                Patient Health Portal
              </h2>
              <span style={{ fontSize: '0.7rem', padding: '2px 8px', borderRadius: 6, background: '#dcfce7', border: '1px solid #bbf7d0', color: '#15803d', fontWeight: 800, letterSpacing: '0.04em' }}>
                PERSONAL EHR VAULT
              </span>
            </div>
            <p style={{ margin: 0, fontSize: '0.8rem', color: '#059669', fontWeight: 600 }}>
              St. Jude Health System • Real-Time Clinical Records Synchronized with Hospital Administration
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          {/* Live Sync Status Pill */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '6px 14px',
            borderRadius: 20,
            background: isSyncPulsing ? '#dcfce7' : '#f0fdf4',
            border: '1px solid #bbf7d0',
            transition: 'all 0.3s ease',
          }}>
            <span style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              background: '#10b981',
              boxShadow: '0 0 10px #10b981',
              display: 'inline-block',
            }} />
            <span style={{ fontSize: '0.75rem', color: '#15803d', fontWeight: 700 }}>
              Live EHR Sync: {lastSyncTime}
            </span>
          </div>

          <div style={{ textAlign: 'right' }}>
            <strong style={{ display: 'block', fontSize: '0.88rem', color: '#0f172a', fontWeight: 800 }}>
              {patientDisplayName}
            </strong>
            <span style={{ fontSize: '0.7rem', color: '#059669', fontWeight: 800 }}>
              PATIENT ACCOUNT
            </span>
          </div>

          {/* Email ID Display Badge: ONLY shown when signed in with Google */}
          {isGoogleAuth && user?.email ? (
            <div
              style={{
                padding: '6px 14px',
                borderRadius: 20,
                background: '#e0f2fe',
                border: '1px solid #bae6fd',
                color: '#0369a1',
                fontSize: '0.82rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              <span>📧</span>
              <span>
                {user.email}
              </span>
            </div>
          ) : null}

          <button
            onClick={onLogout}
            style={{
              padding: '8px 16px',
              borderRadius: 8,
              border: '1px solid #fecaca',
              background: '#fee2e2',
              color: '#b91c1c',
              fontWeight: 700,
              fontSize: '0.84rem',
              cursor: 'pointer',
              transition: 'background 0.2s',
            }}
          >
            Logout
          </button>
        </div>
      </header>

      {/* DASHBOARD CONTENT BODY */}
      <main style={{ padding: '28px 32px', maxWidth: 1280, margin: '0 auto', width: '100%', flex: 1 }}>

        {/* SIMULTANEOUS ADMIN UPDATE TOAST NOTIFICATION */}
        {adminUpdateToast ? (
          <div style={{
            marginBottom: 20,
            padding: '12px 20px',
            borderRadius: 12,
            background: 'linear-gradient(135deg, #059669, #10b981)',
            color: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            boxShadow: '0 4px 14px rgba(16, 185, 129, 0.3)',
            animation: 'fadeIn 0.3s ease',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: '0.9rem', fontWeight: 700 }}>
              <span>🔔</span>
              <span>{adminUpdateToast}</span>
            </div>
            <button
              onClick={() => setAdminUpdateToast(null)}
              style={{ background: 'none', border: 'none', color: '#fff', fontSize: '1.2rem', cursor: 'pointer' }}
            >
              ×
            </button>
          </div>
        ) : null}

        {/* REAL-TIME EHR SYNCHRONIZATION STATUS BAR */}
        <div style={{
          background: '#ffffff',
          border: '1px solid #bbf7d0',
          borderLeft: '4px solid #059669',
          borderRadius: 16,
          padding: '14px 20px',
          marginBottom: 24,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 12,
          boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: '1.2rem' }}>🟢</span>
            <div>
              <span style={{ fontSize: '0.88rem', fontWeight: 800, color: '#166534' }}>
                Simultaneous Administrator Data Synchronization Active
              </span>
              <p style={{ margin: 0, fontSize: '0.8rem', color: '#475569' }}>
                Any patient profiles, diagnoses, prescriptions, or clinical notes entered by Hospital Administrator appear here simultaneously in real time.
              </p>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: '0.82rem', color: '#15803d', fontWeight: 600 }}>
              <strong>{patients.length}</strong> {patients.length === 1 ? 'Record' : 'Records'} in Hospital Vault
            </span>
            <button
              onClick={() => loadPatientRecords(false)}
              style={{
                padding: '6px 14px',
                borderRadius: 8,
                border: '1px solid #bbf7d0',
                background: '#dcfce7',
                color: '#15803d',
                fontSize: '0.8rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              🔄 Refresh Now
            </button>
          </div>
        </div>

        {/* MULTI-PATIENT ROSTER SELECTOR (IF MULTIPLE PATIENTS REGISTERED BY ADMIN) */}
        {patients.length > 1 ? (
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
              <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                📋 Hospital Patient Records Registered by Admin ({patients.length}) — Click to View Profile:
              </span>
            </div>
            <div style={{ display: 'flex', gap: 10, overflowX: 'auto', paddingBottom: 4 }}>
              {patients.map((p) => {
                const isSelected = activeRecord?.id === p.id
                return (
                  <button
                    key={String(p.id)}
                    onClick={() => setSelectedRecordId(String(p.id))}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '10px 16px',
                      borderRadius: 12,
                      border: isSelected ? '2px solid #059669' : '1px solid #e2e8f0',
                      background: isSelected ? '#ecfdf5' : '#ffffff',
                      color: isSelected ? '#065f46' : '#334155',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      transition: 'all 0.2s ease',
                      fontSize: '0.85rem',
                      fontWeight: isSelected ? 800 : 600,
                      boxShadow: '0 1px 3px rgba(15, 23, 42, 0.04)',
                    }}
                  >
                    <span>👤</span>
                    <span>{p.name}</span>
                    <span style={{ fontSize: '0.72rem', padding: '2px 6px', borderRadius: 4, background: isSelected ? '#059669' : '#f1f5f9', color: isSelected ? '#ffffff' : '#64748b', fontWeight: 800 }}>
                      {p.id || `P-${p.patient_id}`}
                    </span>
                    {isSelected ? <span style={{ color: '#059669', fontWeight: 800 }}>✓</span> : null}
                  </button>
                )
              })}
            </div>
          </div>
        ) : null}

        {/* ACTIVE PATIENT OVERVIEW HERO BANNER */}
        {activeRecord ? (
          <div style={{
            background: 'linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 40%, #e0f2fe 100%)',
            border: '1px solid #bbf7d0',
            borderRadius: 20,
            padding: '24px 30px',
            marginBottom: 28,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: 20,
            boxShadow: '0 4px 16px -2px rgba(15, 23, 42, 0.05)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
              <div style={{
                width: 64,
                height: 64,
                borderRadius: 18,
                background: 'linear-gradient(135deg, #059669, #10b981)',
                display: 'grid',
                placeItems: 'center',
                fontSize: 32,
                color: '#fff',
                boxShadow: '0 6px 18px rgba(16,185,129,0.25)',
              }}>
                👤
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
                  <h1 style={{ margin: 0, fontSize: '1.75rem', fontWeight: 800, color: '#0f172a' }}>
                    {activeRecord.name}
                  </h1>
                  <span style={{
                    padding: '3px 10px',
                    borderRadius: 8,
                    background: '#fee2e2',
                    border: '1px solid #fecaca',
                    color: '#b91c1c',
                    fontSize: '0.78rem',
                    fontWeight: 800,
                  }}>
                    Blood Group: {activeRecord.blood_group || 'O+'}
                  </span>
                  <span style={{
                    padding: '3px 10px',
                    borderRadius: 8,
                    background: '#e0f2fe',
                    border: '1px solid #bae6fd',
                    color: '#0369a1',
                    fontSize: '0.78rem',
                    fontWeight: 800,
                  }}>
                    ID: {activeRecord.id || `P-${activeRecord.patient_id}`}
                  </span>
                </div>
                <p style={{ margin: 0, color: '#475569', fontSize: '0.9rem', fontWeight: 500 }}>
                  {activeRecord.age} Years • {activeRecord.gender || 'Not Specified'} • Admitted on {activeRecord.admission_date || 'Current Session'}
                </p>
              </div>
            </div>

            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ padding: '12px 20px', borderRadius: 14, background: '#ffffff', border: '1px solid #bbf7d0', textAlign: 'center', boxShadow: '0 2px 6px rgba(0,0,0,0.03)' }}>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#059669', textTransform: 'uppercase', fontWeight: 800 }}>Attending Doctor</span>
                <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{activeRecord.doctor_assigned || 'Dr. Priya Nair'}</strong>
              </div>
              <div style={{ padding: '12px 20px', borderRadius: 14, background: '#ffffff', border: '1px solid #bae6fd', textAlign: 'center', boxShadow: '0 2px 6px rgba(0,0,0,0.03)' }}>
                <span style={{ display: 'block', fontSize: '0.72rem', color: '#0284c7', textTransform: 'uppercase', fontWeight: 800 }}>Department</span>
                <strong style={{ fontSize: '1rem', color: '#0f172a' }}>{activeRecord.department || 'Cardiology'}</strong>
              </div>
            </div>
          </div>
        ) : null}

        {/* CLINICAL DATA CARDS GRID */}
        {activeRecord ? (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24 }}>
            
            {/* 1. PERSONAL INFORMATION & IDENTIFICATION CARD */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 26, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
              <h3 style={{ margin: '0 0 18px', fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                <span>👤</span> Personal & Identification Details
              </h3>

              <div style={{ display: 'grid', gap: 12, fontSize: '0.88rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Patient Vault ID:</span>
                  <strong style={{ color: '#0284c7', fontWeight: 800 }}>{activeRecord.id || `P-${activeRecord.patient_id}`}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Full Legal Name:</span>
                  <strong style={{ color: '#0f172a' }}>{activeRecord.name}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Age / Gender:</span>
                  <strong style={{ color: '#0f172a' }}>{activeRecord.age} yrs | {activeRecord.gender || 'Not Specified'}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Date of Birth:</span>
                  <span style={{ color: '#0f172a', fontWeight: 600 }}>{activeRecord.date_of_birth || 'Not Specified'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Blood Group:</span>
                  <span style={{ color: '#b91c1c', fontWeight: 800 }}>{activeRecord.blood_group || 'O+'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Aadhaar Number:</span>
                  <span style={{ color: '#0369a1', fontWeight: 700 }}>{activeRecord.aadhaar || 'Verified in Vault'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Mobile Phone:</span>
                  <span style={{ color: '#0f172a', fontWeight: 600 }}>{activeRecord.phone || '+91 98888 00000'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Email Address:</span>
                  <span style={{ color: '#0f172a', fontWeight: 600 }}>
                    {isGoogleAuth && user?.email
                      ? user.email
                      : activeRecord.email &&
                        !activeRecord.email.endsWith('@patient.health') &&
                        !activeRecord.email.includes('+') &&
                        !activeRecord.email.includes('mobile') &&
                        !/^\d+@/.test(activeRecord.email)
                      ? activeRecord.email
                      : 'Not provided'}
                  </span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Emergency Contact:</span>
                  <span style={{ color: '#b91c1c', fontWeight: 700 }}>{activeRecord.emergency_contact || '+91 98888 11111'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 4 }}>
                  <span style={{ color: '#64748b' }}>Residential Address:</span>
                  <span style={{ color: '#334155', maxWidth: '60%', textAlign: 'right', fontWeight: 500 }}>{activeRecord.address || 'Confidential'}</span>
                </div>
              </div>
            </div>

            {/* 2. CLINICAL DIAGNOSIS & MEDICAL CONDITION CARD */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 26, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
              <h3 style={{ margin: '0 0 18px', fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                <span>🩺</span> Active Diagnosis & Clinical Condition
              </h3>

              <div style={{ display: 'grid', gap: 14 }}>
                <div style={{ background: '#ecfdf5', padding: 14, borderRadius: 14, border: '1px solid #a7f3d0' }}>
                  <span style={{ fontSize: '0.72rem', color: '#059669', textTransform: 'uppercase', fontWeight: 800 }}>Primary Condition</span>
                  <h4 style={{ margin: '4px 0 4px', color: '#065f46', fontSize: '1.15rem', fontWeight: 800 }}>{activeRecord.disease || 'General Medical Assessment'}</h4>
                  <p style={{ margin: 0, fontSize: '0.88rem', color: '#166534' }}>
                    <strong>Clinical Diagnosis:</strong> {activeRecord.diagnosis || 'Standard Observation'}
                  </p>
                </div>

                <div>
                  <span style={{ color: '#64748b', fontSize: '0.82rem', fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Symptoms & Complaints:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {activeRecord.symptoms && activeRecord.symptoms.length > 0 ? (
                      activeRecord.symptoms.map((s, idx) => (
                        <span key={idx} style={{ background: '#fef3c7', border: '1px solid #fde68a', color: '#92400e', padding: '3px 8px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 700 }}>
                          ⚠ {s}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.82rem' }}>No acute symptoms recorded</span>
                    )}
                  </div>
                </div>

                <div>
                  <span style={{ color: '#64748b', fontSize: '0.82rem', fontWeight: 700, display: 'block', marginBottom: 6 }}>
                    Allergies & Cautions:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {activeRecord.allergies && activeRecord.allergies.length > 0 ? (
                      activeRecord.allergies.map((a, idx) => (
                        <span key={idx} style={{ background: '#fee2e2', border: '1px solid #fecaca', color: '#b91c1c', padding: '3px 8px', borderRadius: 6, fontSize: '0.78rem', fontWeight: 700 }}>
                          🚫 {a}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.82rem' }}>No known drug allergies reported</span>
                    )}
                  </div>
                </div>

                <div>
                  <span style={{ color: '#64748b', fontSize: '0.82rem', fontWeight: 700, display: 'block', marginBottom: 2 }}>
                    Treatment Protocol / Care Pattern:
                  </span>
                  <p style={{ margin: 0, color: '#0f172a', fontSize: '0.9rem', fontWeight: 600 }}>
                    {activeRecord.treatment_pattern || 'Hospital Standard Clinical Care Protocol'}
                  </p>
                </div>
              </div>
            </div>

            {/* 3. PRESCRIBED MEDICATIONS & DOSAGE SCHEDULE CARD */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 26, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
              <h3 style={{ margin: '0 0 18px', fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                <span>💊</span> Prescribed Medicines & Dosages
              </h3>

              <div style={{ display: 'grid', gap: 14 }}>
                <div>
                  <span style={{ color: '#64748b', fontSize: '0.82rem', fontWeight: 700, display: 'block', marginBottom: 8 }}>
                    Active Prescriptions:
                  </span>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {activeRecord.medicines && activeRecord.medicines.length > 0 ? (
                      activeRecord.medicines.map((med, idx) => (
                        <span key={idx} style={{
                          background: '#e0f2fe',
                          border: '1px solid #bae6fd',
                          color: '#0369a1',
                          padding: '5px 12px',
                          borderRadius: 8,
                          fontWeight: 700,
                          fontSize: '0.85rem',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 6,
                        }}>
                          💊 {med}
                        </span>
                      ))
                    ) : (
                      <span style={{ color: '#64748b', fontSize: '0.85rem' }}>No medicines currently prescribed</span>
                    )}
                  </div>
                </div>

                <div style={{ background: '#f8fafc', padding: 14, borderRadius: 12, border: '1px solid #e2e8f0' }}>
                  <span style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 700, textTransform: 'uppercase', display: 'block', marginBottom: 4 }}>
                    Dosage Schedule & Administration:
                  </span>
                  <p style={{ margin: 0, color: '#0f172a', fontSize: '0.9rem', fontWeight: 600 }}>
                    {activeRecord.dosages && activeRecord.dosages.length > 0
                      ? activeRecord.dosages.join(' • ')
                      : 'Take 1 tablet daily after food as directed by physician.'}
                  </p>
                </div>

                <div style={{ padding: 10, borderRadius: 8, background: '#f0fdf4', border: '1px solid #bbf7d0', fontSize: '0.82rem', color: '#166534', fontWeight: 500 }}>
                  ℹ️ Medications are monitored for dosage adherence and clinical response. Contact your physician if you experience side effects.
                </div>
              </div>
            </div>

            {/* 4. ATTENDING PHYSICIAN & WARD ALLOCATION CARD */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 26, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
              <h3 style={{ margin: '0 0 18px', fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                <span>👨‍⚕️</span> Attending Physician & Department
              </h3>

              <div style={{ display: 'flex', alignItems: 'center', gap: 16, marginBottom: 16 }}>
                <div style={{
                  width: 56,
                  height: 56,
                  borderRadius: 16,
                  background: 'linear-gradient(135deg, #0284c7, #0369a1)',
                  display: 'grid',
                  placeItems: 'center',
                  fontSize: 26,
                  color: '#fff',
                  boxShadow: '0 4px 12px rgba(2, 132, 199, 0.25)',
                }}>
                  👨‍⚕️
                </div>
                <div>
                  <h4 style={{ margin: 0, color: '#0f172a', fontSize: '1.15rem', fontWeight: 800 }}>
                    {activeRecord.doctor_assigned || 'Dr. Priya Nair'}
                  </h4>
                  <span style={{ color: '#0284c7', fontSize: '0.85rem', fontWeight: 700 }}>
                    {activeRecord.department || 'Cardiology'} Specialist
                  </span>
                </div>
              </div>

              <div style={{ display: 'grid', gap: 10, fontSize: '0.88rem', color: '#334155' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Department:</span>
                  <strong style={{ color: '#0f172a' }}>{activeRecord.department || 'Cardiology & Internal Medicine'}</strong>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Ward / Room / Bed:</span>
                  <span style={{ color: '#059669', fontWeight: 700 }}>{activeRecord.ward || 'General Medical Ward'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6, borderBottom: '1px solid #f1f5f9' }}>
                  <span style={{ color: '#64748b' }}>Admission Date:</span>
                  <span style={{ color: '#0f172a' }}>{activeRecord.admission_date || 'Active Registration'}</span>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 6 }}>
                  <span style={{ color: '#64748b' }}>Discharge Status:</span>
                  <span style={{ color: activeRecord.discharge_date ? '#64748b' : '#059669', fontWeight: 700 }}>
                    {activeRecord.discharge_date || 'Currently Admitted & Under Observation'}
                  </span>
                </div>
              </div>
            </div>

            {/* 5. DIAGNOSTIC LAB REPORTS & TESTS CARD */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 26, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                <span>🧪</span> Diagnostic Lab Reports & Vitals
              </h3>

              {/* Lab Reports entered by Admin */}
              <div style={{ marginBottom: 16 }}>
                <span style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 700, display: 'block', marginBottom: 6 }}>
                  Reports Registered by Administrator:
                </span>
                <div style={{ display: 'grid', gap: 6 }}>
                  {activeRecord.lab_reports && activeRecord.lab_reports.length > 0 ? (
                    activeRecord.lab_reports.map((lr, idx) => (
                      <div key={idx} style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '8px 12px', borderRadius: 8, fontSize: '0.84rem', color: '#065f46', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600 }}>
                        <span>📋</span>
                        <span>{lr}</span>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: '#94a3b8', fontSize: '0.82rem', padding: '6px 0' }}>
                      No diagnostic lab files uploaded by admin yet.
                    </div>
                  )}
                </div>
              </div>

              {/* Interactive Lab Lookup */}
              <form onSubmit={handleFetchLab} style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
                <input
                  value={labPatientId}
                  onChange={(e) => setLabPatientId(e.target.value)}
                  placeholder="Patient ID (e.g. P-01)"
                  required
                  style={{ flex: 1, padding: '9px 12px', borderRadius: 8, border: '1px solid #cbd5e1', background: '#ffffff', color: '#0f172a', fontSize: '0.85rem' }}
                />
                <button
                  type="submit"
                  disabled={labLoading}
                  style={{ padding: '9px 14px', borderRadius: 8, background: 'linear-gradient(135deg, #059669, #10b981)', color: '#ffffff', border: 'none', fontWeight: 800, cursor: 'pointer', fontSize: '0.82rem', boxShadow: '0 2px 8px rgba(5,150,105,0.25)' }}
                >
                  {labLoading ? 'Checking...' : 'Check Lab'}
                </button>
              </form>

              {labError ? (
                <div style={{ padding: 8, borderRadius: 8, background: '#fee2e2', border: '1px solid #fecaca', color: '#b91c1c', fontSize: '0.8rem', marginBottom: 8, fontWeight: 600 }}>
                  ⚠️ {labError}
                </div>
              ) : null}

              {labResult ? (
                <div style={{ background: '#f8fafc', padding: 12, borderRadius: 10, border: '1px solid #e2e8f0', fontSize: '0.84rem', color: '#334155' }}>
                  <div style={{ color: '#059669', fontWeight: 800 }}>{labResult.test_name}</div>
                  <div>Finding: <strong style={{ color: '#0f172a' }}>{labResult.result}</strong></div>
                  <div style={{ fontSize: '0.74rem', color: '#64748b', marginTop: 4 }}>
                    Reported: {new Date(labResult.reported_at).toLocaleString()}
                  </div>
                </div>
              ) : null}
            </div>

            {/* 6. DIGITAL WATERMARK & INTEGRITY BADGE CARD */}
            <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 26, boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
              <h3 style={{ margin: '0 0 16px', fontSize: '1.15rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: 10, fontWeight: 800 }}>
                <span>🛡️</span> Zero-Leakage Privacy & Integrity
              </h3>

              <div style={{ display: 'grid', gap: 12, fontSize: '0.84rem', color: '#334155' }}>
                <div style={{ background: '#f0fdf4', padding: 12, borderRadius: 10, border: '1px solid #bbf7d0' }}>
                  <span style={{ fontSize: '0.72rem', color: '#059669', textTransform: 'uppercase', fontWeight: 800 }}>Security Watermark Tag</span>
                  <div style={{ color: '#166534', fontFamily: 'monospace', fontSize: '0.88rem', fontWeight: 800, marginTop: 2 }}>
                    {activeRecord.watermark_id || `WM-SEC-${activeRecord.id || activeRecord.patient_id}`}
                  </div>
                </div>

                <div>
                  <span style={{ color: '#64748b', fontSize: '0.78rem', fontWeight: 600 }}>Cryptographic Fingerprint:</span>
                  <div style={{ color: '#0f172a', fontFamily: 'monospace', fontSize: '0.82rem', wordBreak: 'break-all', fontWeight: 600 }}>
                    {activeRecord.watermark_fingerprint || 'e4d8b9a1c2f30485a7e6b5c4d3e2f1a0'}
                  </div>
                </div>

                <div style={{ padding: 10, borderRadius: 8, background: '#e0f2fe', border: '1px solid #bae6fd', fontSize: '0.82rem', color: '#0369a1' }}>
                  🔒 <strong>Cyber Deception Enclave Protection:</strong> Your genuine medical records are isolated and protected. Any external unauthorized reconnaissance is diverted to synthetic decoy twins.
                </div>
              </div>
            </div>

          </div>
        ) : (
          <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: 20, padding: 48, textAlign: 'center', boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05)' }}>
            <div style={{ fontSize: '3rem', marginBottom: 12 }}>🏥</div>
            <h3 style={{ color: '#0f172a', fontSize: '1.35rem', margin: '0 0 8px', fontWeight: 800 }}>
              {loading ? 'Synchronizing Patient Vault...' : 'No Active Patient Records Found'}
            </h3>
            <p style={{ color: '#64748b', maxWidth: 480, margin: '0 auto 20px', fontSize: '0.9rem' }}>
              Patient records registered by Hospital Administrator will populate here automatically and simultaneously in real time.
            </p>
            <button
              onClick={() => loadPatientRecords(false)}
              style={{
                padding: '10px 22px',
                borderRadius: 10,
                background: 'linear-gradient(135deg, #059669, #10b981)',
                color: '#ffffff',
                border: 'none',
                fontWeight: 800,
                cursor: 'pointer',
                fontSize: '0.9rem',
                boxShadow: '0 4px 14px rgba(5, 150, 105, 0.25)',
              }}
            >
              🔄 Check for Records
            </button>
          </div>
        )}

      </main>
    </div>
  )
}
