import React from 'react'

type AIPredictionCardProps = {
  isolationForestScore?: number
  randomForestPred?: string | number
  xgboostProbability?: number
  overallRiskScore: number
  confidenceRating: number
  gatewayDecision: string
  decisionReason: string
}

export function AIPredictionCard({
  isolationForestScore = -0.12,
  randomForestPred = 'Hostile Probe',
  xgboostProbability = 0.94,
  overallRiskScore,
  confidenceRating,
  gatewayDecision,
  decisionReason,
}: AIPredictionCardProps) {
  const isHostile = overallRiskScore >= 50 || gatewayDecision.toLowerCase().includes('synthetic') || gatewayDecision.toLowerCase().includes('block')
  const statusColor = isHostile ? '#ef4444' : '#10b981'

  return (
    <div
      style={{
        background: 'rgba(15, 23, 42, 0.9)',
        border: `1px solid ${statusColor}40`,
        borderRadius: '20px',
        padding: '24px',
        boxShadow: `0 12px 36px ${statusColor}15`,
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#38bdf8', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            🤖 AI Security Gateway Ensemble Model
          </span>
          <h4 style={{ margin: '2px 0 0', color: '#f8fafc', fontSize: '1.15rem', fontWeight: 800 }}>
            AI Threat Risk Prediction & Decision
          </h4>
        </div>

        <span
          style={{
            fontSize: '0.8rem',
            padding: '6px 14px',
            borderRadius: '999px',
            background: `${statusColor}20`,
            color: statusColor,
            border: `1px solid ${statusColor}50`,
            fontWeight: 800,
          }}
        >
          {gatewayDecision}
        </span>
      </div>

      {/* Model Breakdown Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Isolation Forest Score</span>
          <strong style={{ fontSize: '1.2rem', color: isolationForestScore < 0 ? '#ef4444' : '#10b981', display: 'block', marginTop: '4px' }}>
            {isolationForestScore}
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Anomaly threshold &lt; 0</span>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Random Forest Prediction</span>
          <strong style={{ fontSize: '1.1rem', color: '#c084fc', display: 'block', marginTop: '4px' }}>
            {randomForestPred}
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Classification result</span>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>XGBoost Threat Prob.</span>
          <strong style={{ fontSize: '1.2rem', color: xgboostProbability > 0.5 ? '#ef4444' : '#10b981', display: 'block', marginTop: '4px' }}>
            {(xgboostProbability * 100).toFixed(1)}%
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Gradient Boosted ML</span>
        </div>

        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#94a3b8', display: 'block' }}>Ensemble Confidence</span>
          <strong style={{ fontSize: '1.2rem', color: '#38bdf8', display: 'block', marginTop: '4px' }}>
            {confidenceRating}%
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#64748b' }}>Model certainty</span>
        </div>
      </div>

      {/* Decision Reason Container */}
      <div style={{ background: 'rgba(0, 0, 0, 0.3)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', padding: '14px', fontSize: '0.85rem' }}>
        <strong style={{ color: '#cbd5e1', display: 'block', marginBottom: '4px' }}>💡 AI Decision Reasoning:</strong>
        <p style={{ margin: 0, color: '#f8fafc', lineHeight: 1.5 }}>{decisionReason}</p>
      </div>
    </div>
  )
}
