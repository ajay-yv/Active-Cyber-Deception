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
        return { bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.35)', color: '#fca5a5', icon: '🚨' }
      case 'warning':
        return { bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.35)', color: '#fcd34d', icon: '⚠️' }
      case 'success':
        return { bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.35)', color: '#6ee7b7', icon: '✅' }
      default:
        return { bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.35)', color: '#7dd3fc', icon: 'ℹ️' }
    }
  }

  const styles = getTypeStyles()

  return (
    <div
      style={{
        background: styles.bg,
        border: `1px solid ${styles.border}`,
        borderRadius: '14px',
        padding: '14px 20px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        color: '#f8fafc',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '1.25rem' }}>{styles.icon}</span>
        <div>
          <strong style={{ color: styles.color, fontSize: '0.9rem', fontWeight: 800 }}>{title}</strong>
          <p style={{ margin: '2px 0 0', fontSize: '0.82rem', color: '#e2e8f0' }}>{message}</p>
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
