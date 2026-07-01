import { Navigate, Route, Routes } from 'react-router-dom'

import Layout from './components/Layout'
import ProtectedRoute from './components/ProtectedRoute'
import { useAuth } from './auth/AuthContext'
import AttendancePage from './pages/AttendancePage'
import DashboardPage from './pages/DashboardPage'
import EmployeesPage from './pages/EmployeesPage'
import LoginPage from './pages/LoginPage'

function HomeRedirect() {
  const { user } = useAuth()
  return <Navigate to={user?.is_admin ? '/dashboard' : '/attendance'} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<HomeRedirect />} />
        <Route
          path="employees"
          element={
            <ProtectedRoute adminOnly>
              <EmployeesPage />
            </ProtectedRoute>
          }
        />
        <Route path="attendance" element={<AttendancePage />} />
        <Route
          path="dashboard"
          element={
            <ProtectedRoute adminOnly>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
