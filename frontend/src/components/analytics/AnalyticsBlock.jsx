import ChartBlock from './ChartBlock'

const TONE_CLASS = {
  ok: 'ok',
  late: 'late',
  danger: 'danger',
  accent: 'accent',
  muted: 'muted',
}

function KpiBlock({ block }) {
  return (
    <div className="kai-kpi-grid">
      {block.items.map((it, i) => (
        <div key={i} className="kai-kpi">
          <span className={`kai-kpi-value ${TONE_CLASS[it.tone] || 'accent'}`}>
            {it.value}
          </span>
          <span className="kai-kpi-label">{it.label}</span>
        </div>
      ))}
    </div>
  )
}

function TableBlock({ table }) {
  return (
    <div className="table-wrap kai-table">
      <table>
        <thead>
          <tr>
            {table.columns.map((c) => (
              <th key={c}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {table.rows.map((row, i) => (
            <tr key={i}>
              {row.map((cell, j) => (
                <td key={j}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function AnalyticsBlock({ block }) {
  if (block.type === 'narrative') {
    return (
      <div className="kai-narrative">
        <span className="kai-narrative-mark">kAI</span>
        <div>
          <h4>{block.title}</h4>
          <p>{block.text}</p>
        </div>
      </div>
    )
  }

  if (block.type === 'kpi') {
    return (
      <div className="kai-block">
        {block.title && <h4>{block.title}</h4>}
        <KpiBlock block={block} />
      </div>
    )
  }

  if (block.type === 'table') {
    return (
      <div className="kai-block">
        {block.title && <h4>{block.title}</h4>}
        {block.table && <TableBlock table={block.table} />}
      </div>
    )
  }

  // chart types (bar / bar_horizontal / bar_stacked / line / doughnut)
  return (
    <div className="kai-block">
      {block.title && <h4>{block.title}</h4>}
      {block.empty ? (
        <p className="muted">Tidak ada data untuk periode ini.</p>
      ) : (
        <div className="kai-chart-box">
          <ChartBlock block={block} />
        </div>
      )}
      {block.table && <TableBlock table={block.table} />}
    </div>
  )
}
