import { Navigate } from 'react-router-dom'

import { useAuth } from '../auth/AuthContext'

export default function ProtectedRoute({ children, adminOnly = false }) {
  const { user, loading } = useAuth()

  if (loading) return <div className="page-center">Loading…</div>
  if (!user) return <Navigate to="/login" replace />
  if (adminOnly && !user.is_admin) return <Navigate to="/attendance" replace />
  return children
}
