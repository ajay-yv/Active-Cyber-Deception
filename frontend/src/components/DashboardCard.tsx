type DashboardCardProps = {
  label: string
  value: string | number
  accent: string
}

export function DashboardCard({ label, value, accent }: DashboardCardProps) {
  return (
    <article className="card" style={{ ['--card-accent' as string]: accent }}>
      <span>{label}</span>
      <strong>{value}</strong>
    </article>
  )
}
