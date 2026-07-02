import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const wide = location.pathname.startsWith('/dashboard')

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <span className="brand">Otsu EMS</span>
        <nav>
          {user?.is_admin && <NavLink to="/dashboard">Dashboard</NavLink>}
          {user?.is_admin && <NavLink to="/employees">Karyawan</NavLink>}
          <NavLink to="/attendance">Absensi</NavLink>
        </nav>
        <div className="topbar-right">
          <span className="muted">{user?.email}</span>
          <button className="ghost" onClick={handleLogout}>
            Keluar
          </button>
        </div>
      </header>
      <main className={wide ? 'content content-wide' : 'content'}>
        <Outlet />
      </main>
    </div>
  )
}
