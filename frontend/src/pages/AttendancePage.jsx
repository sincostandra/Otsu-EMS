import { useCallback, useEffect, useState } from 'react'

import api from '../api/client'
import { useAuth } from '../auth/AuthContext'
import ExportButtons from '../components/ExportButtons'
import Pagination from '../components/Pagination'

const PAGE_SIZE = 10

function todayStr() {
  const now = new Date()
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000)
  return local.toISOString().slice(0, 10)
}

export default function AttendancePage() {
  const { user } = useAuth()
  const isAdmin = user?.is_admin
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [dateFilter, setDateFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [today, setToday] = useState(null) // employee's record for today
  const [stats, setStats] = useState(null) // employee's monthly summary
  const [message, setMessage] = useState('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/attendance/', {
        params: {
          page,
          search: search || undefined,
          tanggal: dateFilter || undefined,
          status: statusFilter || undefined,
        },
      })
      setRows(data.results)
      setCount(data.count)
    } finally {
      setLoading(false)
    }
  }, [page, search, dateFilter, statusFilter])

  const loadToday = useCallback(async () => {
    if (isAdmin) return
    const [todayRes, statsRes] = await Promise.all([
      api.get('/attendance/', { params: { tanggal: todayStr() } }),
      api.get('/reports/my-stats/'),
    ])
    setToday(todayRes.data.results[0] ?? null)
    setStats(statsRes.data)
  }, [isAdmin])

  useEffect(() => {
    const timer = setTimeout(load, search ? 300 : 0)
    return () => clearTimeout(timer)
  }, [load, search])

  useEffect(() => {
    loadToday()
  }, [loadToday])

  const doAction = async (action) => {
    setMessage('')
    try {
      await api.post(`/attendance/${action}/`)
      await Promise.all([load(), loadToday()])
    } catch (err) {
      setMessage(err.response?.data?.detail || 'Aksi gagal.')
    }
  }

  return (
    <section className="stack">
      <div className="toolbar">
        <h2>Absensi</h2>
        <ExportButtons
          resource="attendance"
          params={{
            search: search || undefined,
            tanggal: dateFilter || undefined,
            status: statusFilter || undefined,
          }}
        />
      </div>

      {!isAdmin && (
        <div className="card checkin-card">
          <div>
            <strong>Absensi hari ini</strong>
            <p className="muted">
              {today?.jam_masuk
                ? `Masuk ${today.jam_masuk}${
                    today.jam_keluar ? ` · Keluar ${today.jam_keluar}` : ''
                  }`
                : 'Belum check-in.'}
            </p>
          </div>
          <div className="checkin-actions">
            <button onClick={() => doAction('check-in')} disabled={Boolean(today?.jam_masuk)}>
              Check In
            </button>
            <button
              className="ghost"
              onClick={() => doAction('check-out')}
              disabled={!today?.jam_masuk || Boolean(today?.jam_keluar)}
            >
              Check Out
            </button>
          </div>
        </div>
      )}
      {message && <p className="error">{message}</p>}

      {!isAdmin && stats && (
        <div className="stat-grid">
          <StatCard label="Hadir Bulan Ini" value={stats.hadir} />
          <StatCard label="Telat" value={stats.telat} tone="late" />
          <StatCard label="Tidak Hadir" value={stats.tidak_hadir} />
          <StatCard label="Kehadiran" value={`${stats.attendance_rate}%`} />
        </div>
      )}

      <div className="filters">
        {isAdmin && (
          <input
            className="search"
            placeholder="Cari nama atau email…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        )}
        <label className="inline">
          Tanggal
          <input
            type="date"
            value={dateFilter}
            onChange={(e) => {
              setPage(1)
              setDateFilter(e.target.value)
            }}
          />
        </label>
        {isAdmin && (
          <label className="inline">
            Status
            <select
              value={statusFilter}
              onChange={(e) => {
                setPage(1)
                setStatusFilter(e.target.value)
              }}
            >
              <option value="">Semua</option>
              <option value="hadir">Tepat waktu</option>
              <option value="telat">Telat</option>
            </select>
          </label>
        )}
      </div>

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              {isAdmin && <th>Nama</th>}
              {isAdmin && <th>Email</th>}
              <th>Tanggal</th>
              <th>Jam Masuk</th>
              <th>Jam Keluar</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={6} className="muted center">
                  Memuat…
                </td>
              </tr>
            ) : rows.length === 0 ? (
              <tr>
                <td colSpan={6} className="muted center">
                  Belum ada data absensi.
                </td>
              </tr>
            ) : (
              rows.map((r) => (
                <tr key={r.id}>
                  {isAdmin && <td>{r.nama}</td>}
                  {isAdmin && <td>{r.email}</td>}
                  <td>{r.tanggal}</td>
                  <td>{r.jam_masuk || '—'}</td>
                  <td>{r.jam_keluar || '—'}</td>
                  <td>
                    <StatusBadge status={r.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} count={count} pageSize={PAGE_SIZE} onChange={setPage} />
    </section>
  )
}

function StatCard({ label, value, tone }) {
  return (
    <div className="card stat-card">
      <span className={tone === 'late' ? 'stat-value late' : 'stat-value'}>
        {value}
      </span>
      <span className="muted">{label}</span>
    </div>
  )
}

function StatusBadge({ status }) {
  if (!status) return <span className="muted">—</span>
  const isLate = status === 'TELAT'
  return (
    <span className={isLate ? 'badge telat' : 'badge ok'}>
      {isLate ? 'Telat' : 'Tepat'}
    </span>
  )
}
