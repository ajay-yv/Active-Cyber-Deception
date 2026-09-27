import React from 'react'

type SecurityCardProps = {
  title: string
  score: number
  statusText: string
  statusType?: 'secure' | 'warning' | 'critical'
  details?: string
  accentColor?: string
}

export function SecurityCard({
  title,
  score,
  statusText,
  statusType = 'secure',
  details,
  accentColor = '#10b981',
}: SecurityCardProps) {
  const getStatusColor = () => {
    switch (statusType) {
      case 'secure':
        return '#10b981'
      case 'warning':
        return '#f59e0b'
      case 'critical':
        return '#ef4444'
      default:
        return accentColor
    }
  }

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(12px)',
        border: `1px solid ${getStatusColor()}33`,
        borderRadius: '20px',
        padding: '24px',
        position: 'relative',
        boxShadow: `0 12px 36px ${getStatusColor()}15`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, color: '#f8fafc', fontSize: '1rem', fontWeight: 700 }}>{title}</h4>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: '999px',
            background: `${getStatusColor()}20`,
            color: getStatusColor(),
            border: `1px solid ${getStatusColor()}40`,
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
          }}
        >
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: getStatusColor(), display: 'inline-block' }} />
          {statusText}
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '2.5rem', fontWeight: 900, color: getStatusColor(), lineHeight: 1 }}>{score}</span>
        <span style={{ fontSize: '0.9rem', color: '#94a3b8', fontWeight: 600 }}>/ 100 Risk Score</span>
      </div>

      {/* Progress meter bar */}
      <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '999px', overflow: 'hidden', marginBottom: '12px' }}>
        <div
          style={{
            width: `${Math.min(100, Math.max(0, score))}%`,
            height: '100%',
            background: `linear-gradient(90deg, ${getStatusColor()}, ${accentColor})`,
            borderRadius: '999px',
            transition: 'width 0.5s ease',
          }}
        />
      </div>

      {details ? <p style={{ margin: 0, fontSize: '0.82rem', color: '#cbd5e1', lineHeight: 1.5 }}>{details}</p> : null}
    </div>
  )
}
