import { useState } from 'react'

const EMPTY = {
  nama: '',
  email: '',
  jabatan: '',
  tanggal_masuk: '',
  status_aktif: true,
  password: '',
}

export default function EmployeeForm({ initial, onSubmit, onDone, jabatanOptions = [] }) {
  const isEdit = Boolean(initial)
  const [values, setValues] = useState(
    initial ? { ...EMPTY, ...initial, password: '' } : EMPTY,
  )
  const [error, setError] = useState('')
  const [tempPassword, setTempPassword] = useState('')
  const [saving, setSaving] = useState(false)

  const update = (field) => (e) => {
    const value = e.target.type === 'checkbox' ? e.target.checked : e.target.value
    setValues((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSaving(true)
    const payload = { ...values }
    if (!payload.password) delete payload.password
    try {
      const data = await onSubmit(payload)
      if (data?.temp_password) {
        setTempPassword(data.temp_password)
      } else {
        onDone?.()
      }
    } catch (err) {
      const detail = err.response?.data
      setError(
        detail?.email?.[0] ||
          detail?.detail ||
          'Gagal menyimpan data. Periksa kembali isian.',
      )
    } finally {
      setSaving(false)
    }
  }

  if (tempPassword) {
    return (
      <div className="stack">
        <p>Karyawan tersimpan. Password sementara untuk login pertama:</p>
        <code className="temp-password">{tempPassword}</code>
        <p className="muted">
          Salin dan berikan ke karyawan — password ini hanya tampil sekali.
        </p>
        <button type="button" onClick={() => onDone?.()}>
          Selesai
        </button>
      </div>
    )
  }

  return (
    <form className="stack" onSubmit={handleSubmit}>
      <label>
        Nama
        <input value={values.nama} onChange={update('nama')} required />
      </label>
      <label>
        Email
        <input
          type="email"
          value={values.email}
          onChange={update('email')}
          required
        />
      </label>
      <label>
        Jabatan
        <select value={values.jabatan} onChange={update('jabatan')} required>
          <option value="" disabled>
            Pilih jabatan…
          </option>
          {jabatanOptions.map((j) => (
            <option key={j} value={j}>
              {j}
            </option>
          ))}
          {values.jabatan && !jabatanOptions.includes(values.jabatan) && (
            <option value={values.jabatan}>{values.jabatan}</option>
          )}
        </select>
      </label>
      <label>
        Tanggal Masuk
        <input
          type="date"
          value={values.tanggal_masuk}
          onChange={update('tanggal_masuk')}
          required
        />
      </label>
      <label>
        Password {isEdit ? '(kosongkan jika tidak diubah)' : '(opsional)'}
        <input
          type="password"
          value={values.password}
          onChange={update('password')}
          minLength={8}
          placeholder={isEdit ? '••••••••' : 'Otomatis jika kosong'}
        />
      </label>
      <label className="checkbox">
        <input
          type="checkbox"
          checked={values.status_aktif}
          onChange={update('status_aktif')}
        />
        Karyawan aktif
      </label>
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={saving}>
        {saving ? 'Menyimpan…' : 'Simpan'}
      </button>
    </form>
  )
}
