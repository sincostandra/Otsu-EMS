import {
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
import { Bar, Line } from 'react-chartjs-2'

import api from '../api/client'

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  LineElement,
  PointElement,
  Tooltip,
  Legend,
)

const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
}

const RECAP_OPTIONS = {
  ...CHART_OPTIONS,
  plugins: { legend: { display: true, position: 'bottom' } },
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

  const recapData = {
    labels: summary.attendance_recap.map((r) => r.tanggal.slice(5)),
    datasets: [
      {
        label: 'Hadir',
        data: summary.attendance_recap.map((r) => r.hadir),
        borderColor: '#15803d',
        backgroundColor: 'rgba(21, 128, 61, 0.18)',
        tension: 0.3,
        fill: true,
      },
      {
        label: 'Telat',
        data: summary.attendance_recap.map((r) => r.telat),
        borderColor: '#b45309',
        backgroundColor: 'rgba(180, 83, 9, 0.18)',
        tension: 0.3,
        fill: true,
      },
    ],
  }

  const late = summary.late_today ?? []

  return (
    <section className="stack">
      <h2>Dashboard</h2>

      <div className="stat-grid">
        <StatCard label="Total Karyawan" value={summary.total_employees} />
        <StatCard label="Karyawan Aktif" value={summary.active_employees} />
        <StatCard label="Hadir Hari Ini" value={summary.present_today} />
        <StatCard label="Telat Hari Ini" value={late.length} />
      </div>

      <div className="chart-grid">
        <div className="card">
          <h3>Karyawan per Jabatan</h3>
          <div className="chart-box">
            <Bar data={jabatanData} options={CHART_OPTIONS} />
          </div>
        </div>
        <div className="card">
          <h3>Kehadiran 7 Hari Terakhir</h3>
          <div className="chart-box">
            <Line data={recapData} options={RECAP_OPTIONS} />
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Telat Hari Ini</h3>
        {late.length === 0 ? (
          <p className="muted">Tidak ada keterlambatan hari ini.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Nama</th>
                <th>Jabatan</th>
                <th>Jam Masuk</th>
              </tr>
            </thead>
            <tbody>
              {late.map((r, i) => (
                <tr key={i}>
                  <td>{r.nama}</td>
                  <td>{r.jabatan}</td>
                  <td>
                    <span className="badge late">{r.jam_masuk}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
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
