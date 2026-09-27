type Item = {
  type: string
  label: string
}

type DashboardListProps = {
  title: string
  items: Item[]
}

export function DashboardList({ title, items }: DashboardListProps) {
  return (
    <section className="panel">
      <h3>{title}</h3>
      <ul className="list">
        {items.map((item) => (
          <li key={item.label}>
            <span>{item.type}</span>
            <strong>{item.label}</strong>
          </li>
        ))}
      </ul>
    </section>
  )
}
