import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const user = await login(email, password)
      const fallback = user.is_admin ? '/dashboard' : '/attendance'
      navigate(location.state?.from ?? fallback, { replace: true })
    } catch {
      setError('Email atau password salah.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="page-center">
      <form className="card login-card" onSubmit={handleSubmit}>
        <h1>Otsu EMS</h1>
        <p className="muted">Masuk untuk mengelola data karyawan &amp; absensi.</p>
        <label>
          Email
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={submitting}>
          {submitting ? 'Memproses…' : 'Masuk'}
        </button>
      </form>
    </div>
  )
}
