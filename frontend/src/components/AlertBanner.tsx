import React from 'react'

type AlertBannerProps = {
  title: string
  message: string
  type?: 'info' | 'warning' | 'danger' | 'success'
  actionText?: string
  onAction?: () => void
  onDismiss?: () => void
}

export function AlertBanner({
  title,
  message,
  type = 'info',
  actionText,
  onAction,
  onDismiss,
}: AlertBannerProps) {
  const getTypeStyles = () => {
    switch (type) {
      case 'danger':
        return { bg: '#fee2e2', border: '#fecaca', color: '#991b1b', text: '#7f1d1d', icon: '🚨' }
      case 'warning':
        return { bg: '#fef3c7', border: '#fde68a', color: '#92400e', text: '#78350f', icon: '⚠️' }
      case 'success':
        return { bg: '#dcfce7', border: '#bbf7d0', color: '#166534', text: '#14532d', icon: '✅' }
      default:
        return { bg: '#e0f2fe', border: '#bae6fd', color: '#0369a1', text: '#0c4a6e', icon: 'ℹ️' }
    }
  }

  const styles = getTypeStyles()

  return (
    <div
      style={{
        background: styles.bg,
        border: `1px solid ${styles.border}`,
        borderRadius: '12px',
        padding: '14px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        color: styles.text,
        boxShadow: '0 2px 6px rgba(15, 23, 42, 0.04)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '1.25rem' }}>{styles.icon}</span>
        <div>
          <strong style={{ color: styles.color, fontSize: '0.92rem', fontWeight: 800 }}>{title}</strong>
          <p style={{ margin: '2px 0 0', fontSize: '0.84rem', color: styles.text }}>{message}</p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {actionText && onAction ? (
          <button
            onClick={onAction}
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              border: `1px solid ${styles.border}`,
              background: styles.bg,
              color: styles.color,
              fontSize: '0.8rem',
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            {actionText}
          </button>
        ) : null}

        {onDismiss ? (
          <button
            onClick={onDismiss}
            style={{
              background: 'none',
              border: 'none',
              color: '#94a3b8',
              fontSize: '1.1rem',
              cursor: 'pointer',
              padding: '2px 6px',
            }}
          >
            ✕
          </button>
        ) : null}
      </div>
    </div>
  )
}
