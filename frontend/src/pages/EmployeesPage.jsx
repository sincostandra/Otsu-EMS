import { useCallback, useEffect, useState } from 'react'

import api from '../api/client'
import EmployeeForm from '../components/EmployeeForm'
import ExportButtons from '../components/ExportButtons'
import Modal from '../components/Modal'
import Pagination from '../components/Pagination'

const PAGE_SIZE = 10

// Admin-only page (route is gated by <ProtectedRoute adminOnly>).
export default function EmployeesPage() {
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [jabatanFilter, setJabatanFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [jabatanOptions, setJabatanOptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null) // null | 'new' | employee object
  const [notice, setNotice] = useState(null) // { type: 'ok' | 'error', text }

  const exportParams = {
    search: search || undefined,
    jabatan: jabatanFilter || undefined,
    status_aktif: statusFilter || undefined,
  }

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/employees/', {
        params: {
          page,
          search: search || undefined,
          jabatan: jabatanFilter || undefined,
          status_aktif: statusFilter || undefined,
        },
      })
      setRows(data.results)
      setCount(data.count)
    } finally {
      setLoading(false)
    }
  }, [page, search, jabatanFilter, statusFilter])

  useEffect(() => {
    const timer = setTimeout(load, search ? 300 : 0) // debounce typing
    return () => clearTimeout(timer)
  }, [load, search])

  // reset to first page whenever a filter changes
  useEffect(() => {
    setPage(1)
  }, [search, jabatanFilter, statusFilter])

  // jabatan options for the filter dropdown
  useEffect(() => {
    api
      .get('/employees/jabatan-options/')
      .then(({ data }) => setJabatanOptions(data))
      .catch(() => {})
  }, [])

  // auto-dismiss the notification
  useEffect(() => {
    if (!notice) return
    const t = setTimeout(() => setNotice(null), 4000)
    return () => clearTimeout(t)
  }, [notice])

  const handleSubmit = async (payload) => {
    const isNew = editing === 'new'
    const { data } = isNew
      ? await api.post('/employees/', payload)
      : await api.put(`/employees/${editing.id}/`, payload)
    load()
    setNotice({
      type: 'ok',
      text: isNew
        ? `Karyawan ${data.nama} berhasil ditambahkan.`
        : `Data ${data.nama} berhasil diperbarui.`,
    })
    return data
  }

  const handleDelete = async (employee) => {
    if (!window.confirm(`Hapus data ${employee.nama}?`)) return
    try {
      await api.delete(`/employees/${employee.id}/`)
      load()
      setNotice({ type: 'ok', text: `Karyawan ${employee.nama} berhasil dihapus.` })
    } catch (err) {
      setNotice({
        type: 'error',
        text: err.response?.data?.detail || 'Gagal menghapus data karyawan.',
      })
    }
  }

  return (
    <section className="stack">
      <div className="toolbar">
        <h2>Karyawan</h2>
        <div className="toolbar-actions">
          <ExportButtons resource="employees" params={exportParams} />
          <button onClick={() => setEditing('new')}>+ Tambah Karyawan</button>
        </div>
      </div>

      {notice && <div className={`toast ${notice.type}`}>{notice.text}</div>}

      <div className="filters">
        <input
          className="search"
          placeholder="Cari nama, email, atau jabatan…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <label className="inline">
          Jabatan
          <select
            value={jabatanFilter}
            onChange={(e) => setJabatanFilter(e.target.value)}
          >
            <option value="">Semua</option>
            {jabatanOptions.map((j) => (
              <option key={j} value={j}>
                {j}
              </option>
            ))}
          </select>
        </label>
        <label className="inline">
          Status
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">Semua</option>
            <option value="true">Aktif</option>
            <option value="false">Nonaktif</option>
          </select>
        </label>
      </div>

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nama</th>
              <th>Email</th>
              <th>Jabatan</th>
              <th>Tanggal Masuk</th>
              <th>Status</th>
              <th>Aksi</th>
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
                  Tidak ada data.
                </td>
              </tr>
            ) : (
              rows.map((emp) => (
                <tr key={emp.id}>
                  <td>{emp.nama}</td>
                  <td>{emp.email}</td>
                  <td>{emp.jabatan}</td>
                  <td>{emp.tanggal_masuk}</td>
                  <td>
                    <span className={emp.status_aktif ? 'status on' : 'status off'}>
                      {emp.status_aktif ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  <td className="actions">
                    <button className="ghost" onClick={() => setEditing(emp)}>
                      Edit
                    </button>
                    <button className="ghost danger" onClick={() => handleDelete(emp)}>
                      Hapus
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} count={count} pageSize={PAGE_SIZE} onChange={setPage} />

      {editing && (
        <Modal
          title={editing === 'new' ? 'Tambah Karyawan' : 'Edit Karyawan'}
          onClose={() => setEditing(null)}
        >
          <EmployeeForm
            initial={editing === 'new' ? null : editing}
            onSubmit={handleSubmit}
            onDone={() => setEditing(null)}
          />
        </Modal>
      )}
    </section>
  )
}
