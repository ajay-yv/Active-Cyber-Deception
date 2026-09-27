type Row = Record<string, string>

type DashboardTableProps = {
  title: string
  rows: Row[]
}

export function DashboardTable({ title, rows }: DashboardTableProps) {
  const columns = rows.length > 0 ? Object.keys(rows[0]) : []

  return (
    <section className="panel">
      <h3>{title}</h3>
      <div className="table">
        <div className="table-row table-head">
          {columns.map((column) => (
            <span key={column}>{column}</span>
          ))}
        </div>
        {rows.map((row, index) => (
          <div className="table-row" key={index}>
            {columns.map((column) => {
              const value = row[column]
              const str = value == null ? '' : String(value)
              // render clickable link for URLs
              if (str.startsWith('http') || str.startsWith('/api/')) {
                return (
                  <span key={column}>
                    <a href={str} target="_blank" rel="noreferrer">
                      {str}
                    </a>
                  </span>
                )
              }
              return <span key={column}>{str}</span>
            })}
          </div>
        ))}
      </div>
    </section>
  )
}
