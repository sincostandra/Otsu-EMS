import { Fragment } from 'react'

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

function HeatmapBlock({ data }) {
  const { rows, columns, cells, max } = data
  return (
    <div
      className="kai-heatmap"
      style={{ gridTemplateColumns: `auto repeat(${columns.length}, 1fr)` }}
    >
      <span />
      {columns.map((c) => (
        <span key={c} className="kai-heat-col">
          {c}
        </span>
      ))}
      {rows.map((r, ri) => (
        <Fragment key={r}>
          <span className="kai-heat-row">{r}</span>
          {columns.map((c, ci) => {
            const v = cells[ri][ci]
            const ratio = max ? v / max : 0
            return (
              <span
                key={c}
                className="kai-heat-cell"
                title={`${r} ${c}: ${v} telat`}
                style={{
                  background: ratio
                    ? `rgba(180, 83, 9, ${(0.15 + ratio * 0.85).toFixed(2)})`
                    : 'var(--surface-2)',
                  color: ratio > 0.55 ? '#fff' : 'var(--text)',
                }}
              >
                {v || ''}
              </span>
            )
          })}
        </Fragment>
      ))}
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

  if (block.type === 'heatmap') {
    return (
      <div className="kai-block">
        {block.title && <h4>{block.title}</h4>}
        {block.empty ? (
          <p className="muted">Tidak ada data untuk periode ini.</p>
        ) : (
          <HeatmapBlock data={block.data} />
        )}
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
