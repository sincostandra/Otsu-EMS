import { useCallback, useEffect, useState } from 'react'

import api from '../api/client'
import { useAuth } from '../auth/AuthContext'
import EmployeeForm from '../components/EmployeeForm'
import ExportButtons from '../components/ExportButtons'
import Modal from '../components/Modal'
import Pagination from '../components/Pagination'

const PAGE_SIZE = 10

export default function EmployeesPage() {
  const { user } = useAuth()
  const isAdmin = user?.is_admin
  const [rows, setRows] = useState([])
  const [count, setCount] = useState(0)
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [editing, setEditing] = useState(null) // null | 'new' | employee object

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await api.get('/employees/', {
        params: { page, search: search || undefined },
      })
      setRows(data.results)
      setCount(data.count)
    } finally {
      setLoading(false)
    }
  }, [page, search])

  useEffect(() => {
    const timer = setTimeout(load, search ? 300 : 0) // debounce typing
    return () => clearTimeout(timer)
  }, [load, search])

  // reset to first page whenever the search term changes
  useEffect(() => {
    setPage(1)
  }, [search])

  const handleSubmit = async (payload) => {
    const { data } =
      editing === 'new'
        ? await api.post('/employees/', payload)
        : await api.put(`/employees/${editing.id}/`, payload)
    load()
    return data
  }

  const handleDelete = async (employee) => {
    if (!window.confirm(`Hapus data ${employee.nama}?`)) return
    await api.delete(`/employees/${employee.id}/`)
    load()
  }

  return (
    <section className="stack">
      <div className="toolbar">
        <h2>Karyawan</h2>
        <div className="toolbar-actions">
          <ExportButtons resource="employees" params={{ search: search || undefined }} />
          {isAdmin && (
            <button onClick={() => setEditing('new')}>+ Tambah Karyawan</button>
          )}
        </div>
      </div>

      <input
        className="search"
        placeholder="Cari nama, email, atau jabatan…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="card table-wrap">
        <table>
          <thead>
            <tr>
              <th>Nama</th>
              <th>Email</th>
              <th>Jabatan</th>
              <th>Tanggal Masuk</th>
              <th>Status</th>
              {isAdmin && <th>Aksi</th>}
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
                    <span className={emp.status_aktif ? 'badge ok' : 'badge off'}>
                      {emp.status_aktif ? 'Aktif' : 'Nonaktif'}
                    </span>
                  </td>
                  {isAdmin && (
                    <td className="actions">
                      <button className="ghost" onClick={() => setEditing(emp)}>
                        Edit
                      </button>
                      <button
                        className="ghost danger"
                        onClick={() => handleDelete(emp)}
                      >
                        Hapus
                      </button>
                    </td>
                  )}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <Pagination
        page={page}
        count={count}
        pageSize={PAGE_SIZE}
        onChange={setPage}
      />

      {editing && (
        <Modal
          title={editing === 'new' ? 'Tambah Karyawan' : 'Edit Karyawan'}
          onClose={() => setEditing(null)}
        >
          <EmployeeForm
            initial={editing === 'new' ? null : editing}
            onSubmit={handleSubmit}
          />
        </Modal>
      )}
    </section>
  )
}
