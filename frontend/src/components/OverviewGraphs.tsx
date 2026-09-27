import React, { useState } from 'react'

type TimeRange = '24h' | '7d' | '30d'

interface OverviewGraphsProps {
  totalPatients?: number
  simulatedInterceptions?: number
  onSimulateIntercept?: () => void
}

export function OverviewDashboardGraphs({
  totalPatients = 3,
  simulatedInterceptions = 0,
  onSimulateIntercept,
}: OverviewGraphsProps) {
  const [timeRange, setTimeRange] = useState<TimeRange>('24h')
  const [activeTooltip, setActiveTooltip] = useState<string | null>(null)

  // Dynamic datasets based on time range
  const trafficData = {
    '24h': {
      labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', 'Now'],
      staff: [28, 14, 82, 148, 126, 74, 112],
      threats: [8, 22, 6, 18, 38, 29, 15],
      totalQueries: 1142,
      totalBlocked: 142 + simulatedInterceptions,
    },
    '7d': {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      staff: [820, 940, 1120, 1050, 980, 420, 390],
      threats: [112, 145, 98, 134, 168, 62, 45],
      totalQueries: 5720,
      totalBlocked: 764 + simulatedInterceptions,
    },
    '30d': {
      labels: ['W1', 'W2', 'W3', 'W4'],
      staff: [4200, 4800, 5100, 4600],
      threats: [520, 640, 580, 490],
      totalQueries: 18700,
      totalBlocked: 2230 + simulatedInterceptions,
    },
  }[timeRange]

  return (
    <div style={{ display: 'grid', gap: 24 }}>
      {/* Top SOC Graph Command Header with Time Range Switcher */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(30, 41, 59, 0.9))',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          borderRadius: 20,
          padding: '20px 24px',
          boxShadow: '0 10px 30px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 16,
        }}
      >
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 4 }}>
            <span style={{ fontSize: '1.6rem' }}>📈</span>
            <h2 style={{ margin: 0, fontSize: '1.4rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '0.02em' }}>
              Healthcare Enclave Visual Telemetry &amp; Cyber Analytics
            </h2>
            <span
              style={{
                background: 'rgba(16, 185, 129, 0.15)',
                border: '1px solid #10b981',
                color: '#6ee7b7',
                padding: '3px 10px',
                borderRadius: 999,
                fontSize: '0.74rem',
                fontWeight: 700,
              }}
            >
              ● Live Graphs Active
            </span>
          </div>
          <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.84rem' }}>
            Real-time traffic throughput, threat interception curves, adversary vector distributions, and enclave health gauges.
          </p>
        </div>

        {/* Controls: Time Switcher & Triggers */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <div
            style={{
              display: 'flex',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: 10,
              padding: 3,
            }}
          >
            {(['24h', '7d', '30d'] as TimeRange[]).map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                style={{
                  padding: '6px 14px',
                  borderRadius: 8,
                  border: 'none',
                  background: timeRange === range ? 'linear-gradient(135deg, #0284c7, #2563eb)' : 'transparent',
                  color: timeRange === range ? '#fff' : '#94a3b8',
                  fontSize: '0.8rem',
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                }}
              >
                {range === '24h' ? 'Last 24 Hours' : range === '7d' ? '7 Days' : '30 Days'}
              </button>
            ))}
          </div>

          {onSimulateIntercept && (
            <button
              onClick={onSimulateIntercept}
              style={{
                padding: '8px 16px',
                borderRadius: 10,
                border: 'none',
                background: 'linear-gradient(135deg, #0284c7, #2563eb)',
                color: '#fff',
                fontSize: '0.82rem',
                fontWeight: 700,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
                boxShadow: '0 4px 12px rgba(2, 132, 199, 0.35)',
              }}
            >
              <span>⚡</span> Simulate Intercept
            </button>
          )}
        </div>
      </div>

      {/* 4 Graph Summary KPIs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 16 }}>
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderLeft: '4px solid #10b981',
            borderRadius: 16,
            padding: 18,
          }}
        >
          <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>
            Total Inpatient Census
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f8fafc', margin: '4px 0' }}>
            {totalPatients} Patients
          </div>
          <div style={{ fontSize: '0.76rem', color: '#10b981', fontWeight: 700 }}>
            ✔ 100% Real Vault Isolation
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderLeft: '4px solid #38bdf8',
            borderRadius: 16,
            padding: 18,
          }}
        >
          <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>
            Traffic Inspected ({timeRange})
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#38bdf8', margin: '4px 0' }}>
            {trafficData.totalQueries.toLocaleString()}
          </div>
          <div style={{ fontSize: '0.76rem', color: '#7dd3fc', fontWeight: 600 }}>
            &lt; 11ms Gateway Latency
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderLeft: '4px solid #ef4444',
            borderRadius: 16,
            padding: 18,
          }}
        >
          <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>
            Attacks Intercepted &amp; Deflected
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#f87171', margin: '4px 0' }}>
            {trafficData.totalBlocked}
          </div>
          <div style={{ fontSize: '0.76rem', color: '#fca5a5', fontWeight: 700 }}>
            🛡️ 0 Real Records Exposed
          </div>
        </div>

        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderLeft: '4px solid #c084fc',
            borderRadius: 16,
            padding: 18,
          }}
        >
          <div style={{ fontSize: '0.74rem', color: '#94a3b8', fontWeight: 600, textTransform: 'uppercase' }}>
            Enclave Deception Efficacy
          </div>
          <div style={{ fontSize: '1.8rem', fontWeight: 800, color: '#c084fc', margin: '4px 0' }}>
            100.0%
          </div>
          <div style={{ fontSize: '0.76rem', color: '#d8b4fe', fontWeight: 700 }}>
            A+ Military Enclave Grade
          </div>
        </div>
      </div>

      {/* Primary Row: Large Area/Spline Graph + Donut Chart */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: 20 }}>
        {/* Graph 1: Area/Line Spline Chart */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 20,
            padding: 24,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#f8fafc', fontWeight: 800 }}>
                📊 Real-Time Traffic &amp; Attack Interception Flow
              </h3>
              <p style={{ margin: '3px 0 0', color: '#94a3b8', fontSize: '0.78rem' }}>
                Curved volume comparison: Legitimate Clinical Traffic vs. Intercepted Hostile Probes
              </p>
            </div>
            <div style={{ display: 'flex', gap: 14, fontSize: '0.75rem', fontWeight: 700 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#38bdf8' }} />
                <span style={{ color: '#7dd3fc' }}>Staff Traffic</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }} />
                <span style={{ color: '#fca5a5' }}>Attacks Deflected</span>
              </div>
            </div>
          </div>

          <TrafficAreaChart labels={trafficData.labels} staff={trafficData.staff} threats={trafficData.threats} />
        </div>

        {/* Graph 2: Donut Chart (Adversary Vectors) */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 20,
            padding: 24,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#f8fafc', fontWeight: 800 }}>
              🎯 Adversary Vector Distribution
            </h3>
            <p style={{ margin: '3px 0 0', color: '#94a3b8', fontSize: '0.78rem' }}>
              Breakdown of {trafficData.totalBlocked} intercepted exploitation attempts
            </p>
          </div>

          <DonutVectorChart totalBlocked={trafficData.totalBlocked} />
        </div>
      </div>

      {/* Secondary Row: Vertical Bar Chart (Department Load) + Radial Security Gauge */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: 20 }}>
        {/* Graph 3: Department Workload & Deception Bar Chart */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 20,
            padding: 24,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#f8fafc', fontWeight: 800 }}>
                🏥 Department Admissions &amp; Decoy Shielding
              </h3>
              <p style={{ margin: '3px 0 0', color: '#94a3b8', fontSize: '0.78rem' }}>
                Real hospital patients vs. active synthetic twin lures deployed per clinical department
              </p>
            </div>
            <div style={{ display: 'flex', gap: 12, fontSize: '0.75rem', fontWeight: 700 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#10b981' }} />
                <span style={{ color: '#6ee7b7' }}>Real Patients</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                <span style={{ width: 10, height: 10, borderRadius: 2, background: '#c084fc' }} />
                <span style={{ color: '#d8b4fe' }}>Decoy Twins</span>
              </div>
            </div>
          </div>

          <DepartmentBarChart />
        </div>

        {/* Graph 4: Security Posture Radial Gauge */}
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.85)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: 20,
            padding: 24,
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
          }}
        >
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ margin: 0, fontSize: '1.15rem', color: '#f8fafc', fontWeight: 800 }}>
              🛡️ Multi-Vector Security &amp; Compliance Index
            </h3>
            <p style={{ margin: '3px 0 0', color: '#94a3b8', fontSize: '0.78rem' }}>
              Real-time audit assurance across cryptographic and machine learning enclaves
            </p>
          </div>

          <SecurityGaugeChart />
        </div>
      </div>

      {/* Graph 5: 24-Hour Activity Heatmap Strips */}
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.85)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          borderRadius: 20,
          padding: 24,
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.1rem', color: '#f8fafc', fontWeight: 800 }}>
              ⏱️ Hourly Enclave Traffic &amp; Threat Deflection Timeline (24-Hour Strip)
            </h3>
            <p style={{ margin: '3px 0 0', color: '#94a3b8', fontSize: '0.78rem' }}>
              Hover over any hour to inspect traffic density and automated decoy routing
            </p>
          </div>
          <div style={{ display: 'flex', gap: 12, fontSize: '0.75rem', fontWeight: 600 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: '#10b981' }} />
              <span style={{ color: '#94a3b8' }}>Normal Traffic</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: '#f59e0b' }} />
              <span style={{ color: '#94a3b8' }}>Elevated Probe</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 10, height: 10, borderRadius: 2, background: '#ef4444' }} />
              <span style={{ color: '#94a3b8' }}>Attack Deflected</span>
            </div>
          </div>
        </div>

        <HourlyActivityStrip activeTooltip={activeTooltip} setActiveTooltip={setActiveTooltip} />
      </div>
    </div>
  )
}

/* -------------------------------------------------------------
   SVG GRAPH 1: Curved Area Spline Chart (Staff Traffic vs Attacks)
---------------------------------------------------------------- */
function TrafficAreaChart({
  labels,
  staff,
  threats,
}: {
  labels: string[]
  staff: number[]
  threats: number[]
}) {
  const width = 560
  const height = 210
  const paddingX = 40
  const paddingY = 24
  const chartW = width - paddingX * 2
  const chartH = height - paddingY * 2

  const maxVal = Math.max(...staff, ...threats, 100) * 1.15

  const pointsStaff = staff.map((val, idx) => ({
    x: paddingX + (idx / (staff.length - 1)) * chartW,
    y: paddingY + chartH - (val / maxVal) * chartH,
    val,
  }))

  const pointsThreats = threats.map((val, idx) => ({
    x: paddingX + (idx / (threats.length - 1)) * chartW,
    y: paddingY + chartH - (val / maxVal) * chartH,
    val,
  }))

  const generateSmoothPath = (pts: { x: number; y: number }[]) => {
    if (pts.length === 0) return ''
    let d = `M ${pts[0].x} ${pts[0].y}`
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[i]
      const p1 = pts[i + 1]
      const cp1x = p0.x + (p1.x - p0.x) / 2
      const cp1y = p0.y
      const cp2x = p0.x + (p1.x - p0.x) / 2
      const cp2y = p1.y
      d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${p1.x} ${p1.y}`
    }
    return d
  }

  const staffPath = generateSmoothPath(pointsStaff)
  const staffArea = `${staffPath} L ${paddingX + chartW} ${paddingY + chartH} L ${paddingX} ${paddingY + chartH} Z`

  const threatsPath = generateSmoothPath(pointsThreats)
  const threatsArea = `${threatsPath} L ${paddingX + chartW} ${paddingY + chartH} L ${paddingX} ${paddingY + chartH} Z`

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
      <defs>
        <linearGradient id="staffGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
          <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
        </linearGradient>
        <linearGradient id="threatsGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#ef4444" stopOpacity="0.45" />
          <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
        </linearGradient>
      </defs>

      {/* Grid lines */}
      {[0, 0.25, 0.5, 0.75, 1].map((ratio, idx) => {
        const y = paddingY + chartH * ratio
        return (
          <g key={idx}>
            <line x1={paddingX} y1={y} x2={paddingX + chartW} y2={y} stroke="rgba(255,255,255,0.06)" strokeDasharray="4 4" />
            <text x={paddingX - 8} y={y + 4} textAnchor="end" fill="#64748b" fontSize="9" fontFamily="monospace">
              {Math.round(maxVal * (1 - ratio))}
            </text>
          </g>
        )
      })}

      {/* Area fills */}
      <path d={staffArea} fill="url(#staffGrad)" />
      <path d={threatsArea} fill="url(#threatsGrad)" />

      {/* Spline Lines */}
      <path d={staffPath} fill="none" stroke="#38bdf8" strokeWidth="2.5" />
      <path d={threatsPath} fill="none" stroke="#ef4444" strokeWidth="2.5" />

      {/* Data dots for Staff */}
      {pointsStaff.map((p, idx) => (
        <circle key={`s-${idx}`} cx={p.x} cy={p.y} r="4" fill="#0284c7" stroke="#38bdf8" strokeWidth="2" />
      ))}

      {/* Data dots for Threats */}
      {pointsThreats.map((p, idx) => (
        <circle key={`t-${idx}`} cx={p.x} cy={p.y} r="4" fill="#991b1b" stroke="#f87171" strokeWidth="2" />
      ))}

      {/* X-axis labels */}
      {labels.map((lbl, idx) => {
        const x = paddingX + (idx / (labels.length - 1)) * chartW
        return (
          <text key={idx} x={x} y={height - 4} textAnchor="middle" fill="#94a3b8" fontSize="10" fontWeight="600">
            {lbl}
          </text>
        )
      })}
    </svg>
  )
}

/* -------------------------------------------------------------
   SVG GRAPH 2: Modern Donut Chart (Adversary Vector Distribution)
---------------------------------------------------------------- */
function DonutVectorChart({ totalBlocked }: { totalBlocked: number }) {
  const slices = [
    { label: 'SQL Injection Probes', percent: 34, count: Math.round(totalBlocked * 0.34), color: '#ef4444' },
    { label: 'Single Patient Theft Probes', percent: 30, count: Math.round(totalBlocked * 0.3), color: '#f59e0b' },
    { label: 'Bulk Database Dump Probes', percent: 24, count: Math.round(totalBlocked * 0.24), color: '#c084fc' },
    { label: 'API Reconnaissance Scans', percent: 12, count: Math.round(totalBlocked * 0.12), color: '#38bdf8' },
  ]

  const size = 200
  const center = size / 2
  const radius = 70
  const circumference = 2 * Math.PI * radius

  let accumulatedPercent = 0

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, flexWrap: 'wrap' }}>
      <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
        <svg viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%' }}>
          {/* Background Track */}
          <circle cx={center} cy={center} r={radius} fill="none" stroke="rgba(255, 255, 255, 0.05)" strokeWidth="24" />

          {slices.map((slice, idx) => {
            const strokeDasharray = `${(slice.percent / 100) * circumference} ${circumference}`
            const strokeDashoffset = -((accumulatedPercent / 100) * circumference)
            accumulatedPercent += slice.percent

            return (
              <circle
                key={idx}
                cx={center}
                cy={center}
                r={radius}
                fill="none"
                stroke={slice.color}
                strokeWidth="24"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                style={{ transition: 'stroke-dasharray 0.6s ease' }}
              />
            )
          })}
        </svg>

        {/* Center Text inside Donut */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            pointerEvents: 'none',
          }}
        >
          <span style={{ fontSize: '1.5rem', fontWeight: 900, color: '#f8fafc', lineHeight: 1 }}>
            {totalBlocked}
          </span>
          <span style={{ fontSize: '0.68rem', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.08em', marginTop: 2 }}>
            DEFLECTED
          </span>
        </div>
      </div>

      {/* Legend alongside Donut */}
      <div style={{ display: 'grid', gap: 10, flex: 1, minWidth: 160 }}>
        {slices.map((slice, idx) => (
          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.78rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ width: 10, height: 10, borderRadius: 3, background: slice.color, flexShrink: 0 }} />
              <span style={{ color: '#cbd5e1', fontWeight: 600 }}>{slice.label}</span>
            </div>
            <span style={{ color: slice.color, fontWeight: 800 }}>
              {slice.percent}%
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------
   SVG GRAPH 3: Vertical Column Bar Graph (Department Admissions)
---------------------------------------------------------------- */
function DepartmentBarChart() {
  const departments = [
    { name: 'Cardiology', real: 2, decoys: 2, max: 4 },
    { name: 'Oncology', real: 1, decoys: 1, max: 4 },
    { name: 'Gen Medicine', real: 1, decoys: 1, max: 4 },
    { name: 'Neurology', real: 0, decoys: 1, max: 4 },
    { name: 'Emergency', real: 0, decoys: 1, max: 4 },
  ]

  const width = 420
  const height = 180
  const paddingBottom = 28
  const chartH = height - paddingBottom
  const barWidth = 16

  return (
    <svg viewBox={`0 0 ${width} ${height}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
      {/* Horizontal guides */}
      {[0, 1, 2, 3, 4].map((level) => {
        const y = chartH - (level / 4) * (chartH - 20) - 10
        return (
          <g key={level}>
            <line x1="20" y1={y} x2={width - 10} y2={y} stroke="rgba(255, 255, 255, 0.05)" strokeDasharray="3 3" />
            <text x="12" y={y + 3} textAnchor="end" fill="#64748b" fontSize="9" fontFamily="monospace">
              {level}
            </text>
          </g>
        )
      })}

      {/* Paired Vertical Bars */}
      {departments.map((dept, idx) => {
        const groupX = 35 + idx * 78
        const realH = (dept.real / 4) * (chartH - 20)
        const decoyH = (dept.decoys / 4) * (chartH - 20)

        const realY = chartH - realH - 10
        const decoyY = chartH - decoyH - 10

        return (
          <g key={idx}>
            {/* Real patient bar */}
            <rect
              x={groupX}
              y={realY}
              width={barWidth}
              height={Math.max(realH, 3)}
              rx="4"
              fill={dept.real > 0 ? '#10b981' : 'rgba(255,255,255,0.06)'}
            />
            {/* Decoy patient bar */}
            <rect
              x={groupX + barWidth + 4}
              y={decoyY}
              width={barWidth}
              height={Math.max(decoyH, 3)}
              rx="4"
              fill="#c084fc"
            />

            {/* Department Label */}
            <text
              x={groupX + barWidth + 2}
              y={height - 8}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="9.5"
              fontWeight="600"
            >
              {dept.name}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

/* -------------------------------------------------------------
   SVG GRAPH 4: Multi-Vector Security Radial Gauge
---------------------------------------------------------------- */
function SecurityGaugeChart() {
  const rings = [
    { label: 'Real Database Isolation', score: 100, color: '#10b981', r: 76, stroke: 12 },
    { label: 'Synthetic Realism Fidelity', score: 99.8, color: '#c084fc', r: 60, stroke: 10 },
    { label: 'Gateway Latency Efficiency', score: 98.4, color: '#38bdf8', r: 46, stroke: 8 },
  ]

  const size = 180
  const center = size / 2

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 20, flexWrap: 'wrap' }}>
      <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
        <svg viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)', width: '100%', height: '100%' }}>
          {rings.map((ring, idx) => {
            const circ = 2 * Math.PI * ring.r
            const strokeDasharray = `${(ring.score / 100) * circ} ${circ}`

            return (
              <React.Fragment key={idx}>
                {/* Track */}
                <circle
                  cx={center}
                  cy={center}
                  r={ring.r}
                  fill="none"
                  stroke="rgba(255, 255, 255, 0.05)"
                  strokeWidth={ring.stroke}
                />
                {/* Meter */}
                <circle
                  cx={center}
                  cy={center}
                  r={ring.r}
                  fill="none"
                  stroke={ring.color}
                  strokeWidth={ring.stroke}
                  strokeDasharray={strokeDasharray}
                  strokeLinecap="round"
                />
              </React.Fragment>
            )
          })}
        </svg>

        {/* Center Score */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            pointerEvents: 'none',
          }}
        >
          <span style={{ fontSize: '1.4rem', fontWeight: 900, color: '#10b981', lineHeight: 1 }}>
            99.6%
          </span>
          <span style={{ fontSize: '0.62rem', fontWeight: 800, color: '#cbd5e1', letterSpacing: '0.05em', marginTop: 2 }}>
            A+ SHIELD
          </span>
        </div>
      </div>

      <div style={{ display: 'grid', gap: 8, flex: 1, minWidth: 160 }}>
        {rings.map((ring, idx) => (
          <div key={idx} style={{ display: 'grid', gap: 3 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.76rem' }}>
              <span style={{ color: '#cbd5e1', fontWeight: 600 }}>{ring.label}</span>
              <span style={{ color: ring.color, fontWeight: 800 }}>{ring.score}%</span>
            </div>
            <div style={{ width: '100%', height: 4, background: 'rgba(255,255,255,0.06)', borderRadius: 999 }}>
              <div style={{ width: `${ring.score}%`, height: '100%', background: ring.color, borderRadius: 999 }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

/* -------------------------------------------------------------
   SVG GRAPH 5: 24-Hour Activity Strip Heatmap
---------------------------------------------------------------- */
function HourlyActivityStrip({
  activeTooltip,
  setActiveTooltip,
}: {
  activeTooltip: string | null
  setActiveTooltip: (val: string | null) => void
}) {
  const hours = [
    { hr: '00:00', load: 12, threat: false },
    { hr: '01:00', load: 8, threat: false },
    { hr: '02:00', load: 18, threat: true, desc: 'SQL probe deflected' },
    { hr: '03:00', load: 6, threat: false },
    { hr: '04:00', load: 14, threat: false },
    { hr: '05:00', load: 22, threat: false },
    { hr: '06:00', load: 45, threat: false },
    { hr: '07:00', load: 68, threat: false },
    { hr: '08:00', load: 92, threat: false },
    { hr: '09:00', load: 120, threat: true, desc: 'Honeytoken probe trapped' },
    { hr: '10:00', load: 138, threat: false },
    { hr: '11:00', load: 148, threat: false },
    { hr: '12:00', load: 110, threat: false },
    { hr: '13:00', load: 95, threat: false },
    { hr: '14:00', load: 126, threat: true, desc: 'API scan deflected' },
    { hr: '15:00', load: 142, threat: false },
    { hr: '16:00', load: 115, threat: false },
    { hr: '17:00', load: 88, threat: false },
    { hr: '18:00', load: 74, threat: false },
    { hr: '19:00', load: 62, threat: false },
    { hr: '20:00', load: 84, threat: true, desc: 'Bulk dump attempt decoyed' },
    { hr: '21:00', load: 56, threat: false },
    { hr: '22:00', load: 42, threat: false },
    { hr: '23:00', load: 38, threat: false },
  ]

  return (
    <div style={{ display: 'grid', gap: 8 }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(24, 1fr)', gap: 6, alignItems: 'flex-end', height: 70 }}>
        {hours.map((h, idx) => {
          const heightPercent = Math.max(15, (h.load / 148) * 100)
          const barColor = h.threat ? '#ef4444' : h.load > 100 ? '#38bdf8' : '#10b981'

          return (
            <div
              key={idx}
              onMouseEnter={() => setActiveTooltip(`${h.hr}: ${h.load} queries${h.desc ? ` • ⚠️ ${h.desc}` : ''}`)}
              onMouseLeave={() => setActiveTooltip(null)}
              style={{
                height: `${heightPercent}%`,
                background: barColor,
                borderRadius: 4,
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                opacity: 0.85,
                position: 'relative',
              }}
            />
          )
        })}
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#64748b', fontSize: '0.72rem', fontFamily: 'monospace' }}>
        <span>00:00 (Midnight)</span>
        <span>06:00 (Morning Shift)</span>
        <span>12:00 (Noon Peak)</span>
        <span>18:00 (Evening Shift)</span>
        <span>23:00 (Night)</span>
      </div>

      {activeTooltip && (
        <div
          style={{
            background: 'rgba(15, 23, 42, 0.95)',
            border: '1px solid rgba(56, 189, 248, 0.4)',
            borderRadius: 8,
            padding: '6px 14px',
            fontSize: '0.78rem',
            color: '#f8fafc',
            textAlign: 'center',
            boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
          }}
        >
          {activeTooltip}
        </div>
      )}
    </div>
  )
}
