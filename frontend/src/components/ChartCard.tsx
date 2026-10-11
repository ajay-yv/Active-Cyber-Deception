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
        background: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)',
      }}
    >
      <div style={{ marginBottom: '18px' }}>
        <h4 style={{ margin: 0, color: '#0f172a', fontSize: '1.05rem', fontWeight: 800 }}>{title}</h4>
        {subtitle ? <p style={{ margin: '4px 0 0', color: '#64748b', fontSize: '0.82rem' }}>{subtitle}</p> : null}
      </div>

      <div style={{ display: 'grid', gap: '14px' }}>
        {data.map((item, idx) => {
          const percentage = Math.min(100, Math.round(((item.value || 0) / divisor) * 100))
          const color = item.color || '#0284c7'

          return (
            <div key={idx} style={{ display: 'grid', gap: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.84rem' }}>
                <span style={{ color: '#334155', fontWeight: 600 }}>{item.label}</span>
                <span style={{ color: color, fontWeight: 800 }}>{item.value} ({percentage}%)</span>
              </div>
              <div style={{ width: '100%', height: '8px', background: '#f1f5f9', borderRadius: '999px', overflow: 'hidden' }}>
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
