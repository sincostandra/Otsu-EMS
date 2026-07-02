import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  Tooltip,
} from 'chart.js'
import { useEffect, useState } from 'react'
import { Bar } from 'react-chartjs-2'

import api from '../api/client'
import KaiPanel from '../components/analytics/KaiPanel'

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip, Legend)

const DOW = ['Min', 'Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab']

function dayOfWeek(dateStr) {
  return new Date(`${dateStr}T00:00:00`).getDay()
}

function isWeekend(dateStr) {
  const d = dayOfWeek(dateStr)
  return d === 0 || d === 6
}

const BASE_OPTIONS = {
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

const JABATAN_OPTIONS = {
  ...BASE_OPTIONS,
  interaction: { mode: 'nearest', intersect: true },
}

export default function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get('/reports/summary/')
      .then(({ data }) => setSummary(data))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p className="muted">Memuat…</p>
  if (!summary) return <p className="error">Gagal memuat ringkasan.</p>

  const jabatanData = {
    labels: summary.per_jabatan.map((r) => r.jabatan),
    datasets: [
      {
        label: 'Karyawan',
        data: summary.per_jabatan.map((r) => r.total),
        backgroundColor: '#1552b3',
        borderRadius: 4,
      },
    ],
  }

  const weekendFlags = summary.attendance_recap.map((r) => isWeekend(r.tanggal))

  const recapData = {
    labels: summary.attendance_recap.map((r) => [
      r.tanggal.slice(5),
      DOW[dayOfWeek(r.tanggal)],
    ]),
    datasets: [
      {
        label: 'Hadir',
        data: summary.attendance_recap.map((r) => r.hadir),
        backgroundColor: '#15803d',
        borderRadius: 4,
      },
      {
        label: 'Telat',
        data: summary.attendance_recap.map((r) => r.telat),
        backgroundColor: '#b45309',
        borderRadius: 4,
      },
    ],
  }

  const recapOptions = {
    ...BASE_OPTIONS,
    plugins: {
      ...BASE_OPTIONS.plugins,
      legend: { display: true, position: 'bottom' },
      tooltip: {
        ...BASE_OPTIONS.plugins.tooltip,
        callbacks: {
          title: (items) => {
            const i = items[0].dataIndex
            const r = summary.attendance_recap[i]
            const label = `${r.tanggal} (${DOW[dayOfWeek(r.tanggal)]})`
            return weekendFlags[i] ? `${label} · akhir pekan` : label
          },
        },
      },
    },
    scales: {
      ...BASE_OPTIONS.scales,
      x: {
        grid: { display: false },
        ticks: {
          color: (ctx) => (weekendFlags[ctx.index] ? '#c31006' : '#64748b'),
          font: (ctx) =>
            weekendFlags[ctx.index] ? { weight: '600' } : { weight: '400' },
        },
      },
    },
  }

  const late = summary.late_today ?? []

  return (
    <section className="stack">
      <h2>Dashboard</h2>

      <div className="stat-grid">
        <StatCard label="Total Karyawan" value={summary.total_employees} />
        <StatCard label="Hadir Hari Ini" value={summary.present_today} />
        <StatCard label="Telat Hari Ini" value={late.length} />
      </div>

      <div className="chart-grid">
        <div className="card">
          <h3>Karyawan per Jabatan</h3>
          <div className="chart-box">
            <Bar data={jabatanData} options={JABATAN_OPTIONS} />
          </div>
        </div>
        <div className="card">
          <h3>Kehadiran 7 Hari Terakhir</h3>
          <div className="chart-box">
            <Bar data={recapData} options={recapOptions} />
          </div>
        </div>
      </div>

      <KaiPanel />
    </section>
  )
}

function StatCard({ label, value }) {
  return (
    <div className="card stat-card">
      <span className="stat-value">{value}</span>
      <span className="muted">{label}</span>
    </div>
  )
}
