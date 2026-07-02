import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js'
import { useEffect, useState } from 'react'
import { Bar, Doughnut, Line } from 'react-chartjs-2'

import api from '../api/client'
import KaiPanel from '../components/analytics/KaiPanel'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
)

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

const TODAY_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '62%',
  plugins: {
    legend: { display: true, position: 'bottom' },
    tooltip: { padding: 10, boxPadding: 4 },
  },
}

const TREND_OPTIONS = {
  ...BASE_OPTIONS,
  plugins: {
    ...BASE_OPTIONS.plugins,
    legend: { display: true, position: 'bottom' },
  },
  elements: {
    point: { radius: 0, hoverRadius: 4 },
    line: { tension: 0.3 },
  },
  scales: {
    ...BASE_OPTIONS.scales,
    x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } },
  },
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

  const trend30 = summary.attendance_trend_30d ?? []
  const trend30Data = {
    labels: trend30.map((r) => r.tanggal.slice(5)),
    datasets: [
      {
        label: 'Hadir',
        data: trend30.map((r) => r.hadir),
        borderColor: '#15803d',
        backgroundColor: '#15803d',
      },
      {
        label: 'Telat',
        data: trend30.map((r) => r.telat),
        borderColor: '#b45309',
        backgroundColor: '#b45309',
      },
    ],
  }

  const late = summary.late_today ?? []

  const ontime = Math.max(0, summary.present_today - late.length)
  const absent = Math.max(0, summary.active_employees - summary.present_today)
  const todayData = {
    labels: ['Tepat waktu', 'Telat', 'Belum hadir'],
    datasets: [
      {
        data: [ontime, late.length, absent],
        backgroundColor: ['#15803d', '#b45309', '#e2e8f0'],
        borderWidth: 0,
      },
    ],
  }

  return (
    <section className="stack">
      <h2>Dashboard</h2>

      <div className="dash-grid">
        <div className="dash-charts">
          <div className="card">
            <h3>Karyawan per Jabatan</h3>
            <div className="chart-box">
              <Bar data={jabatanData} options={JABATAN_OPTIONS} />
            </div>
          </div>

          <div className="chart-grid">
            <div className="card">
              <h3>Kehadiran 7 Hari Terakhir</h3>
              <div className="chart-box">
                <Bar data={recapData} options={recapOptions} />
              </div>
            </div>
            <div className="card">
              <h3>Status Kehadiran Hari Ini</h3>
              <div className="chart-box">
                <Doughnut data={todayData} options={TODAY_OPTIONS} />
              </div>
            </div>
          </div>

          <div className="card">
            <h3>Tren Kehadiran 30 Hari Terakhir</h3>
            <div className="chart-box">
              <Line data={trend30Data} options={TREND_OPTIONS} />
            </div>
          </div>
        </div>

        <KaiPanel />
      </div>
    </section>
  )
}
