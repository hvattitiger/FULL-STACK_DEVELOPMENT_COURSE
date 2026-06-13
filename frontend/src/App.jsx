import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext'
import { Layout } from './components/layout'
import LoginPage     from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import ProjectsPage  from './pages/ProjectsPage'
import TasksPage     from './pages/TasksPage'
import UsersPage     from './pages/UsersPage'
import RolesPage     from './pages/RolesPage'

// Guard: redirects to /login if not authenticated
function PrivateRoute({ children }) {
  const { isLoggedIn, isInitializing } = useAuth()   // ← use isLoggedIn, not token
  if (isInitializing) return null
  return isLoggedIn ? children : <Navigate to="/login" replace />
}

// Guard: redirects to / if not admin
function AdminRoute({ children }) {
  const { isLoggedIn, isAdmin, isInitializing } = useAuth()
  if (isInitializing) return null
  if (!isLoggedIn) return <Navigate to="/login" replace />
  if (!isAdmin)    return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected — all authenticated users */}
      <Route path="/" element={
        <PrivateRoute><Layout><DashboardPage /></Layout></PrivateRoute>
      } />
      <Route path="/projects" element={
        <PrivateRoute><Layout><ProjectsPage /></Layout></PrivateRoute>
      } />
      <Route path="/tasks" element={
        <PrivateRoute><Layout><TasksPage /></Layout></PrivateRoute>
      } />

      {/* Admin only */}
      <Route path="/users" element={
        <AdminRoute><Layout><UsersPage /></Layout></AdminRoute>
      } />
      <Route path="/roles" element={
        <AdminRoute><Layout><RolesPage /></Layout></AdminRoute>
      } />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}