import React from 'react'

type ChartBarItem = {
  label: string
  value: number
  color?: string
}

type ChartCardProps = {
  title: string
  subtitle?: string
  data: ChartBarItem[]
  maxValue?: number
  percentageBasis?: 'total' | 'max'
}

export function ChartCard({ title, subtitle, data, maxValue, percentageBasis = 'total' }: ChartCardProps) {
  const sum = data.reduce((acc, d) => acc + (d.value || 0), 0)
  const divisor = percentageBasis === 'total' 
    ? (maxValue || (sum > 0 ? sum : 1)) 
    : (maxValue || Math.max(...data.map((d) => d.value), 1))

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.85)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '20px',
        padding: '24px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
      }}
    >
      <div style={{ marginBottom: '18px' }}>
        <h4 style={{ margin: 0, color: '#f8fafc', fontSize: '1.05rem', fontWeight: 800 }}>{title}</h4>
        {subtitle ? <p style={{ margin: '4px 0 0', color: '#94a3b8', fontSize: '0.8rem' }}>{subtitle}</p> : null}
      </div>

      <div style={{ display: 'grid', gap: '14px' }}>
        {data.map((item, idx) => {
          const percentage = Math.min(100, Math.round(((item.value || 0) / divisor) * 100))
          const color = item.color || '#38bdf8'

          return (
            <div key={idx} style={{ display: 'grid', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span style={{ color: '#e2e8f0', fontWeight: 600 }}>{item.label}</span>
                <span style={{ color: color, fontWeight: 800 }}>{item.value} ({percentage}%)</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: 'rgba(255, 255, 255, 0.06)', borderRadius: '999px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${percentage}%`,
                    height: '100%',
                    background: color,
                    borderRadius: '999px',
                    transition: 'width 0.6s ease',
                  }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
