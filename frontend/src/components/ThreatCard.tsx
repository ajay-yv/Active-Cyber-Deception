import React from 'react'

type ThreatCardProps = {
  ip: string
  score: number
  attackType: string
  timestamp: string
  details?: string
  isBlocked?: boolean
  onBlock?: () => void
  onUnblock?: () => void
}

export function ThreatCard({
  ip,
  score,
  attackType,
  timestamp,
  details,
  isBlocked = false,
  onBlock,
  onUnblock,
}: ThreatCardProps) {
  const getSeverityColor = () => {
    if (score >= 80) return '#ef4444'
    if (score >= 50) return '#f59e0b'
    return '#06b6d4'
  }

  return (
    <div
      style={{
        background: '#ffffff',
        border: `1px solid #e2e8f0`,
        borderLeft: `4px solid ${getSeverityColor()}`,
        borderRadius: '14px',
        padding: '16px 20px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        boxShadow: '0 2px 8px rgba(15, 23, 42, 0.04)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: `${getSeverityColor()}15`,
            border: `1px solid ${getSeverityColor()}33`,
            display: 'grid',
            placeItems: 'center',
            fontSize: '1.1rem',
            color: getSeverityColor(),
          }}
        >
          ⚠️
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontFamily: 'monospace', fontWeight: 800, color: '#0f172a', fontSize: '0.95rem' }}>{ip}</span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '999px',
                background: `${getSeverityColor()}15`,
                color: getSeverityColor(),
                border: `1px solid ${getSeverityColor()}33`,
              }}
            >
              {attackType}
            </span>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '0.82rem', color: '#475569' }}>
            {details || 'Suspicious request activity detected by Cyber Deception Gateway.'}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.25rem', fontWeight: 900, color: getSeverityColor() }}>{score}</div>
          <span style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 600 }}>Risk Score</span>
        </div>

        {isBlocked ? (
          <button
            onClick={onUnblock}
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              border: '1px solid #bbf7d0',
              background: '#dcfce7',
              color: '#15803d',
              fontSize: '0.8rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Unblock IP
          </button>
        ) : (
          <button
            onClick={onBlock}
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              border: '1px solid #fecaca',
              background: '#fee2e2',
              color: '#b91c1c',
              fontSize: '0.8rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            🚫 Block IP
          </button>
        )}
      </div>
    </div>
  )
}
