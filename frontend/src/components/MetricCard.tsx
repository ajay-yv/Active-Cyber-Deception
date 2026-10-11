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
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderLeft: `4px solid ${accentColor}`,
        borderRadius: '16px',
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
        overflow: 'hidden',
        boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)',
        transition: 'transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            {title}
          </span>
          <h3 style={{ margin: '6px 0 0', fontSize: '1.9rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
            {value}
          </h3>
        </div>
        <div
          style={{
            width: '44px',
            height: '44px',
            borderRadius: '12px',
            background: `${accentColor}14`,
            border: `1px solid ${accentColor}28`,
            display: 'grid',
            placeItems: 'center',
            fontSize: '1.3rem',
          }}
        >
          {icon}
        </div>
      </div>

      <div style={{ marginTop: '14px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.82rem' }}>
        {subtitle ? <span style={{ color: '#475569', fontWeight: 500 }}>{subtitle}</span> : <span />}

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
