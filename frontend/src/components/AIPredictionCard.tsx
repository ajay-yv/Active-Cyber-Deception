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
        background: '#ffffff',
        border: `1px solid #e2e8f0`,
        borderTop: `4px solid ${statusColor}`,
        borderRadius: '16px',
        padding: '24px',
        boxShadow: '0 4px 14px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.03)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: '#0284c7', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            🤖 AI Security Gateway Ensemble Model
          </span>
          <h4 style={{ margin: '2px 0 0', color: '#0f172a', fontSize: '1.2rem', fontWeight: 800 }}>
            AI Threat Risk Prediction & Decision
          </h4>
        </div>

        <span
          style={{
            fontSize: '0.8rem',
            padding: '6px 14px',
            borderRadius: '999px',
            background: `${statusColor}15`,
            color: statusColor,
            border: `1px solid ${statusColor}33`,
            fontWeight: 800,
          }}
        >
          {gatewayDecision}
        </span>
      </div>

      {/* Model Breakdown Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '12px', marginBottom: '20px' }}>
        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', fontWeight: 600 }}>Isolation Forest Score</span>
          <strong style={{ fontSize: '1.25rem', color: isolationForestScore < 0 ? '#dc2626' : '#059669', display: 'block', marginTop: '4px' }}>
            {isolationForestScore}
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Anomaly threshold &lt; 0</span>
        </div>

        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', fontWeight: 600 }}>Random Forest Prediction</span>
          <strong style={{ fontSize: '1.15rem', color: '#7c3aed', display: 'block', marginTop: '4px' }}>
            {randomForestPred}
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Classification result</span>
        </div>

        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', fontWeight: 600 }}>XGBoost Threat Prob.</span>
          <strong style={{ fontSize: '1.25rem', color: xgboostProbability > 0.5 ? '#dc2626' : '#059669', display: 'block', marginTop: '4px' }}>
            {(xgboostProbability * 100).toFixed(1)}%
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Gradient Boosted ML</span>
        </div>

        <div style={{ background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: '12px', padding: '14px' }}>
          <span style={{ fontSize: '0.75rem', color: '#64748b', display: 'block', fontWeight: 600 }}>Ensemble Confidence</span>
          <strong style={{ fontSize: '1.25rem', color: '#0284c7', display: 'block', marginTop: '4px' }}>
            {confidenceRating}%
          </strong>
          <span style={{ fontSize: '0.7rem', color: '#94a3b8' }}>Model certainty</span>
        </div>
      </div>

      {/* Decision Reason Container */}
      <div style={{ background: '#f1f5f9', border: '1px solid #cbd5e1', borderRadius: '12px', padding: '14px', fontSize: '0.85rem' }}>
        <strong style={{ color: '#1e293b', display: 'block', marginBottom: '4px' }}>💡 AI Decision Reasoning:</strong>
        <p style={{ margin: 0, color: '#334155', lineHeight: 1.5 }}>{decisionReason}</p>
      </div>
    </div>
  )
}
