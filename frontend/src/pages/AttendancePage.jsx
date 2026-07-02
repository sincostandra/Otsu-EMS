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
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [profile, setProfile] = useState(null) // employee's own profile
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
          tanggal_after: dateFrom || undefined,
          tanggal_before: dateTo || undefined,
          status: statusFilter || undefined,
        },
      })
      setRows(data.results)
      setCount(data.count)
    } finally {
      setLoading(false)
    }
  }, [page, search, dateFrom, dateTo, statusFilter])

  const loadToday = useCallback(async () => {
    if (isAdmin) return
    const [todayRes, statsRes, profileRes] = await Promise.all([
      api.get('/attendance/', { params: { tanggal: todayStr() } }),
      api.get('/reports/my-stats/'),
      api.get('/employees/'),
    ])
    setToday(todayRes.data.results[0] ?? null)
    setStats(statsRes.data)
    setProfile(profileRes.data.results[0] ?? null)
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
        {isAdmin && (
          <ExportButtons
            resource="attendance"
            params={{
              search: search || undefined,
              tanggal_after: dateFrom || undefined,
              tanggal_before: dateTo || undefined,
              status: statusFilter || undefined,
            }}
          />
        )}
      </div>

      {!isAdmin && profile && <ProfileView employee={profile} />}

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
          Dari
          <input
            type="date"
            value={dateFrom}
            onChange={(e) => {
              setPage(1)
              setDateFrom(e.target.value)
            }}
          />
        </label>
        <label className="inline">
          Sampai
          <input
            type="date"
            value={dateTo}
            onChange={(e) => {
              setPage(1)
              setDateTo(e.target.value)
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

function initialsOf(name) {
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((s) => s[0].toUpperCase())
    .join('')
}

function ProfileView({ employee }) {
  return (
    <div className="card profile-card">
      <div className="profile-avatar" aria-hidden="true">
        {initialsOf(employee.nama)}
      </div>
      <div className="profile-body">
        <h3>{employee.nama}</h3>
        <p className="muted">{employee.jabatan}</p>
        <dl className="profile-fields">
          <div>
            <dt>Email</dt>
            <dd>{employee.email}</dd>
          </div>
          <div>
            <dt>Tanggal Masuk</dt>
            <dd>{employee.tanggal_masuk}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>
              <span className={employee.status_aktif ? 'status on' : 'status off'}>
                {employee.status_aktif ? 'Aktif' : 'Nonaktif'}
              </span>
            </dd>
          </div>
        </dl>
      </div>
    </div>
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
    <span className={isLate ? 'status late' : 'status on'}>
      {isLate ? 'Telat' : 'Tepat'}
    </span>
  )
}
