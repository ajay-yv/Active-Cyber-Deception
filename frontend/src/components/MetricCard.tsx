import React from 'react'

type MetricCardProps = {
  title: string
  value: string | number
  subtitle?: string
  icon?: string
  trend?: string
  trendType?: 'positive' | 'negative' | 'neutral' | 'danger'
  accentColor?: string
  badgeText?: string
}

export function MetricCard({
  title,
  value,
  subtitle,
  icon = '📊',
  trend,
  trendType = 'neutral',
  accentColor = '#38bdf8',
  badgeText,
}: MetricCardProps) {
  const getTrendColor = () => {
    switch (trendType) {
      case 'positive':
        return '#10b981'
      case 'danger':
        return '#ef4444'
      case 'negative':
        return '#f59e0b'
      default:
        return '#94a3b8'
    }
  }

  return (
    <div
      className="metric-card-container"
      style={{
        background: 'rgba(15, 23, 42, 0.75)',
        backdropFilter: 'blur(12px)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderLeft: `4px solid ${accentColor}`,
        borderRadius: '16px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.35)',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: '0.78rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {title}
          </span>
          <h3 style={{ margin: '6px 0 0', fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.02em' }}>
            {value}
          </h3>
        </div>
        <div
          style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: `${accentColor}18`,
            border: `1px solid ${accentColor}33`,
            display: 'grid',
            placeItems: 'center',
            fontSize: '1.25rem',
          }}
        >
          {icon}
        </div>
      </div>

      <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem' }}>
        {subtitle ? <span style={{ color: '#cbd5e1' }}>{subtitle}</span> : <span />}

        {trend ? (
          <span style={{ color: getTrendColor(), fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
            {trend}
          </span>
        ) : null}

        {badgeText ? (
          <span
            style={{
              fontSize: '0.72rem',
              padding: '2px 8px',
              borderRadius: '999px',
              background: `${accentColor}20`,
              color: accentColor,
              fontWeight: 700,
              border: `1px solid ${accentColor}40`,
            }}
          >
            {badgeText}
          </span>
        ) : null}
      </div>
    </div>
  )
}
