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
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)',
        transition: 'transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <span style={{ fontSize: '0.78rem', color: '#0284c7', fontWeight: 800, letterSpacing: '0.04em' }}>
              {patient.id && String(patient.id).startsWith('P-')
                ? patient.id
                : patient.patient_id
                ? `P-${String(patient.patient_id).padStart(2, '0')}`
                : patient.id || 'P-01'}
            </span>
            <h4 style={{ margin: '2px 0 0', color: '#0f172a', fontSize: '1.15rem', fontWeight: 800 }}>
              {patient.name}
            </h4>
          </div>
          <span
            style={{
              fontSize: '0.75rem',
              color: '#475569',
              background: '#f1f5f9',
              border: '1px solid #e2e8f0',
              padding: '4px 10px',
              borderRadius: '999px',
              fontWeight: 700,
            }}
          >
            {patient.age} yrs {patient.gender ? `• ${patient.gender}` : ''}
          </span>
        </div>

        {/* Status Badges Row */}
        <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginBottom: '14px' }}>
          <span style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: '#dcfce7', color: '#15803d', border: '1px solid #bbf7d0', fontWeight: 700 }}>
            🛡️ Protected
          </span>
          <span style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: isTwinLinked ? '#f5f3ff' : '#f1f5f9', color: isTwinLinked ? '#6d28d9' : '#64748b', border: isTwinLinked ? '1px solid #ddd6fe' : '1px solid #e2e8f0', fontWeight: 700 }}>
            {isTwinLinked ? '🧬 Synthetic Twin Linked' : '⏳ Pending Twin'}
          </span>
          <span style={{ fontSize: '0.7rem', padding: '3px 8px', borderRadius: '6px', background: '#e0f2fe', color: '#0369a1', border: '1px solid #bae6fd', fontWeight: 700 }}>
            ✨ AI Verified
          </span>
        </div>

        <div style={{ fontSize: '0.84rem', color: '#334155', display: 'grid', gap: '4px', marginBottom: '16px' }}>
          <div><strong style={{ color: '#64748b', fontWeight: 600 }}>Diagnosis:</strong> {patient.disease} {patient.diagnosis ? `(${patient.diagnosis})` : ''}</div>
          <div><strong style={{ color: '#64748b', fontWeight: 600 }}>Doctor:</strong> {patient.doctor_assigned || 'Dr. Unassigned'}</div>
          <div><strong style={{ color: '#64748b', fontWeight: 600 }}>Department:</strong> {patient.department || 'General Clinical'}</div>
        </div>
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '12px', borderTop: '1px solid #f1f5f9' }}>
        <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
          Updated: {patient.updated_at ? new Date(patient.updated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently'}
        </span>

        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={onViewDetails}
            style={{
              padding: '6px 12px',
              borderRadius: '8px',
              border: '1px solid #bae6fd',
              background: '#e0f2fe',
              color: '#0369a1',
              fontSize: '0.78rem',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.15s ease',
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
                border: '1px solid #bbf7d0',
                background: '#dcfce7',
                color: '#15803d',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
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
                border: '1px solid #fecaca',
                background: '#fee2e2',
                color: '#b91c1c',
                fontSize: '0.78rem',
                fontWeight: 700,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
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
