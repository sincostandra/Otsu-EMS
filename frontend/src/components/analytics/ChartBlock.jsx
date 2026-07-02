import { Bar, Doughnut, Line } from 'react-chartjs-2'

import { PALETTE } from './charts'

const BASE = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index', intersect: false },
  plugins: {
    legend: { display: false },
    tooltip: { padding: 10, boxPadding: 4 },
  },
  scales: {
    x: { grid: { display: false } },
    y: { beginAtZero: true, ticks: { precision: 0 } },
  },
}

function barData(block) {
  return {
    labels: block.data.labels,
    datasets: block.data.datasets.map((ds) => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: ds.colors || ds.color || '#1552b3',
      borderRadius: 4,
    })),
  }
}

function lineData(block) {
  return {
    labels: block.data.labels,
    datasets: block.data.datasets.map((ds) => ({
      label: ds.label,
      data: ds.data,
      borderColor: ds.color || '#1552b3',
      backgroundColor: ds.color || '#1552b3',
      tension: 0.3,
      fill: false,
      pointRadius: 3,
    })),
  }
}

function doughnutData(block) {
  const ds = block.data.datasets[0] || { data: [] }
  return {
    labels: block.data.labels,
    datasets: [
      {
        label: ds.label,
        data: ds.data,
        backgroundColor: block.data.labels.map((_, i) => PALETTE[i % PALETTE.length]),
        borderWidth: 0,
      },
    ],
  }
}

const withLegend = (opts) => ({
  ...opts,
  plugins: { ...opts.plugins, legend: { display: true, position: 'bottom' } },
})

export default function ChartBlock({ block }) {
  const multi = (block.data?.datasets?.length || 0) > 1

  if (block.type === 'line') {
    return <Line data={lineData(block)} options={multi ? withLegend(BASE) : BASE} />
  }

  if (block.type === 'doughnut') {
    return (
      <Doughnut
        data={doughnutData(block)}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: true, position: 'right' } },
        }}
      />
    )
  }

  // bar, bar_horizontal, bar_stacked
  const options = { ...BASE }
  if (block.type === 'bar_horizontal') options.indexAxis = 'y'
  if (block.type === 'bar_stacked') {
    options.scales = {
      x: { ...BASE.scales.x, stacked: true },
      y: { ...BASE.scales.y, stacked: true },
    }
  }
  return <Bar data={barData(block)} options={multi ? withLegend(options) : options} />
}
