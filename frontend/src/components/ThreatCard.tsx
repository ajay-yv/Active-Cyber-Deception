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
        background: 'rgba(15, 23, 42, 0.85)',
        border: `1px solid ${getSeverityColor()}33`,
        borderRadius: '14px',
        padding: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: `${getSeverityColor()}18`,
            border: `1px solid ${getSeverityColor()}40`,
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
            <span style={{ fontFamily: 'monospace', fontWeight: 700, color: '#f8fafc', fontSize: '0.95rem' }}>{ip}</span>
            <span
              style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '2px 8px',
                borderRadius: '999px',
                background: `${getSeverityColor()}20`,
                color: getSeverityColor(),
                border: `1px solid ${getSeverityColor()}40`,
              }}
            >
              {attackType}
            </span>
          </div>
          <p style={{ margin: '4px 0 0', fontSize: '0.8rem', color: '#cbd5e1' }}>
            {details || 'Suspicious request activity detected by Cyber Deception Gateway.'}
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color: getSeverityColor() }}>{score}</div>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Risk Score</span>
        </div>

        {isBlocked ? (
          <button
            onClick={onUnblock}
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
            Unblock IP
          </button>
        ) : (
          <button
            onClick={onBlock}
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
            🚫 Block IP
          </button>
        )}
      </div>
    </div>
  )
}
