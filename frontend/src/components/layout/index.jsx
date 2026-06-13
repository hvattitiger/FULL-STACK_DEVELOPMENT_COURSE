import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'
import { RoleBadge } from '../ui'

const NAV_ITEMS = [
  { to: '/',         icon: '📊', label: 'Dashboard', roles: [] },
  { to: '/projects', icon: '📁', label: 'Projects',  roles: [] },
  { to: '/tasks',    icon: '✅', label: 'Tasks',     roles: [] },
  { to: '/users',    icon: '👥', label: 'Users',     roles: ['admin'] },
  { to: '/roles',    icon: '🔐', label: 'Roles',     roles: ['admin'] },
]

export function Sidebar() {
  const { user, logout, isAdmin } = useAuth()
  const navigate = useNavigate()
  const handleLogout = () => { logout(); navigate('/login') }
  const visibleItems = NAV_ITEMS.filter(
    item => item.roles.length === 0 || (isAdmin && item.roles.includes('admin'))
  )
  return (
    <aside className="w-60 bg-gray-900 border-r border-gray-800 flex flex-col h-screen fixed left-0 top-0 z-30">
      <div className="px-5 py-6 border-b border-gray-800">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🚀</span>
          <span className="font-bold text-lg">Task<span className="text-indigo-400">Tracker</span></span>
        </div>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
        {visibleItems.map(({ to, icon, label }) => (
          <NavLink key={to} to={to} end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 ${
                isActive
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                  : 'text-gray-400 hover:text-gray-200 hover:bg-gray-800'
              }`
            }>
            <span className="text-base">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-3 border-t border-gray-800">
        <div className="bg-gray-800 rounded-lg p-3 mb-2">
          <div className="font-semibold text-sm text-white truncate">{user?.full_name || user?.username}</div>
          <div className="text-gray-500 text-xs truncate mb-2">{user?.email}</div>
          <div className="flex flex-wrap gap-1">
            {user?.roles?.map(r => <RoleBadge key={r} role={r} />)}
          </div>
        </div>
        <button onClick={handleLogout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-400 hover:bg-red-500/10 transition-colors">
          <span>⬅</span> Sign Out
        </button>
      </div>
    </aside>
  )
}

export function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-gray-950">
      <Sidebar />
      <main className="flex-1 ml-60 p-8 overflow-y-auto min-h-screen">{children}</main>
    </div>
  )
}

export function PageHeader({ title, action }) {
  return (
    <div className="flex items-center justify-between mb-8">
      <h1 className="text-2xl font-bold text-white">{title}</h1>
      {action}
    </div>
  )
}
