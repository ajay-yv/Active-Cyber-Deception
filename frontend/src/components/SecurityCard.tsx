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
        background: '#ffffff',
        border: `1px solid #e2e8f0`,
        borderTop: `4px solid ${getStatusColor()}`,
        borderRadius: '16px',
        padding: '24px',
        position: 'relative',
        boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h4 style={{ margin: 0, color: '#0f172a', fontSize: '1.05rem', fontWeight: 800 }}>{title}</h4>
        <span
          style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '4px 12px',
            borderRadius: '999px',
            background: `${getStatusColor()}15`,
            color: getStatusColor(),
            border: `1px solid ${getStatusColor()}33`,
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
        <span style={{ fontSize: '0.9rem', color: '#64748b', fontWeight: 600 }}>/ 100 Risk Score</span>
      </div>

      {/* Progress meter bar */}
      <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '999px', overflow: 'hidden', marginBottom: '12px' }}>
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

      {details ? <p style={{ margin: 0, fontSize: '0.84rem', color: '#475569', lineHeight: 1.5 }}>{details}</p> : null}
    </div>
  )
}
