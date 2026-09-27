import React from 'react'

type TimelineStep = {
  title: string
  subtitle: string
  status?: 'completed' | 'active' | 'pending' | 'warning'
  detail?: string
  icon?: string
}

type TimelineProps = {
  steps?: TimelineStep[]
}

const defaultSteps: TimelineStep[] = [
  { title: 'Incoming Request', subtitle: 'Attacker / Client HTTP Access', status: 'completed', icon: '🌐', detail: 'IP: 192.168.1.105 | User-Agent: ProbeBot' },
  { title: 'Deception Gateway', subtitle: 'Session & Auth Inspection', status: 'completed', icon: '🛡️', detail: 'Gateway identifies hostile signature' },
  { title: 'AI Risk Engine', subtitle: 'Isolation Forest + XGBoost', status: 'active', icon: '🧠', detail: 'Threat Probability: 94.2% (Hostile)' },
  { title: 'Synthetic Twin Generator', subtitle: 'AI Decoy Record Linkage', status: 'pending', icon: '🧬', detail: 'Serving synthetic patient twin' },
  { title: 'Forensic Watermarking', subtitle: 'Watermark Fingerprint Injection', status: 'pending', icon: '🔍', detail: 'Embedded Watermark: WM-88231-IST' },
]

export function Timeline({ steps = defaultSteps }: TimelineProps) {
  const getStepColor = (status: TimelineStep['status']) => {
    switch (status) {
      case 'completed':
        return '#10b981'
      case 'active':
        return '#38bdf8'
      case 'warning':
        return '#f59e0b'
      default:
        return '#64748b'
    }
  }

  return (
    <div style={{ background: 'rgba(15, 23, 42, 0.85)', borderRadius: '20px', padding: '24px', border: '1px solid rgba(255,255,255,0.08)' }}>
      <h4 style={{ margin: '0 0 20px', color: '#f8fafc', fontSize: '1.05rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 8 }}>
        ⚡ Visual Deception Pipeline & Attack Timeline
      </h4>

      <div style={{ display: 'grid', gridTemplateColumns: `repeat(${steps.length}, 1fr)`, gap: '12px', position: 'relative' }}>
        {steps.map((step, idx) => {
          const color = getStepColor(step.status)
          return (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.03)',
                border: `1px solid ${color}40`,
                borderRadius: '14px',
                padding: '14px',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                position: 'relative',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span
                  style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '50%',
                    background: `${color}25`,
                    color: color,
                    display: 'grid',
                    placeItems: 'center',
                    fontWeight: 800,
                    fontSize: '0.8rem',
                    border: `1px solid ${color}`,
                  }}
                >
                  {step.icon || idx + 1}
                </span>
                <span style={{ fontSize: '0.75rem', fontWeight: 700, color: color, textTransform: 'uppercase' }}>
                  Step {idx + 1}
                </span>
              </div>

              <div>
                <h5 style={{ margin: 0, color: '#f8fafc', fontSize: '0.9rem', fontWeight: 700 }}>{step.title}</h5>
                <p style={{ margin: '2px 0 0', color: '#94a3b8', fontSize: '0.78rem' }}>{step.subtitle}</p>
              </div>

              {step.detail ? (
                <div style={{ fontSize: '0.72rem', color: '#cbd5e1', background: 'rgba(0,0,0,0.3)', padding: '6px 8px', borderRadius: '6px', marginTop: 'auto' }}>
                  {step.detail}
                </div>
              ) : null}
            </div>
          )
        })}
      </div>
    </div>
  )
}
