import React from 'react'

type PatientCardProps = {
  patient: {
    id: string
    patient_id?: string | number
    name: string
    age: number
    gender?: string
    disease: string
    diagnosis?: string
    doctor_assigned?: string
    department?: string
    admission_date?: string
    forensic_record?: any
    watermark_fingerprint?: string
    updated_at?: string
  }
  onViewDetails: () => void
  onEdit?: () => void
  onDelete?: () => void
  isDeleting?: boolean
}

export function PatientCard({ patient, onViewDetails, onEdit, onDelete, isDeleting }: PatientCardProps) {
  const isTwinLinked = Boolean(patient.forensic_record || patient.watermark_fingerprint)

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '16px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
        transition: 'transform 0.2s ease, border-color 0.2s ease',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <span style={{ fontSize: '0.78rem', color: '#38bdf8', fontWeight: 700 }}>
              {patient.id && String(patient.id).startsWith('P-')
                ? patient.id
                : patient.patient_id
                ? `P-${String(patient.patient_id).padStart(2, '0')}`
                : patient.id || 'P-01'}
            </span>
            <h4 style={{ margin: '2px 0 0', color: '#f8fafc', fontSize: '1.1rem', fontWeight: 800 }}>
              {patient.name}
            </h4>
          </div>
          <span
            style={{
              fontSize: '0.75rem',
              color: '#cbd5e1',
              background: 'rgba(255, 255, 255, 0.06)',
              padding: '4px 10px',
              borderRadius: '999px',
              fontWeight: 600,
            }}
          >
            {patient.age} yrs {patient.gender ? `• ${patient.gender}` : ''}
          </span>
        </div>

        {/* Status Badges Row */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
          <span style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)', fontWeight: 700 }}>
            🛡️ Protected
          </span>
          <span style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: isTwinLinked ? 'rgba(168, 85, 247, 0.15)' : 'rgba(148, 163, 184, 0.15)', color: isTwinLinked ? '#c084fc' : '#94a3b8', border: isTwinLinked ? '1px solid rgba(168, 85, 247, 0.3)' : '1px solid rgba(148, 163, 184, 0.3)', fontWeight: 700 }}>
            {isTwinLinked ? '🧬 Synthetic Twin Linked' : '⏳ Pending Twin'}
          </span>
          <span style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: 'rgba(6, 182, 212, 0.15)', color: '#22d3ee', border: '1px solid rgba(6, 182, 212, 0.3)', fontWeight: 700 }}>
            ✨ AI Verified
          </span>
        </div>

        <div style={{ fontSize: '0.82rem', color: '#cbd5e1', display: 'grid', gap: '4px', marginBottom: '16px' }}>
          <div><strong style={{ color: '#94a3b8' }}>Diagnosis:</strong> {patient.disease} {patient.diagnosis ? `(${patient.diagnosis})` : ''}</div>
          <div><strong style={{ color: '#94a3b8' }}>Doctor:</strong> {patient.doctor_assigned || 'Dr. Unassigned'}</div>
          <div><strong style={{ color: '#94a3b8' }}>Department:</strong> {patient.department || 'General Clinical'}</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid rgba(255, 255, 255, 0.06)' }}>
        <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
          Updated: {patient.updated_at ? new Date(patient.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}
        </span>

        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={onViewDetails}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid rgba(56, 189, 248, 0.4)',
              background: 'rgba(56, 189, 248, 0.15)',
              color: '#38bdf8',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            👁️ Details
          </button>
          {onEdit ? (
            <button
              onClick={onEdit}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid rgba(16, 185, 129, 0.4)',
                background: 'rgba(16, 185, 129, 0.15)',
                color: '#34d399',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              ✏️ Edit
            </button>
          ) : null}
          {onDelete ? (
            <button
              onClick={onDelete}
              disabled={isDeleting}
              style={{
                padding: '6px 12px',
                borderRadius: '8px',
                border: '1px solid rgba(239, 68, 68, 0.4)',
                background: 'rgba(239, 68, 68, 0.15)',
                color: '#fca5a5',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {isDeleting ? 'Deleting...' : '🗑️'}
            </button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
