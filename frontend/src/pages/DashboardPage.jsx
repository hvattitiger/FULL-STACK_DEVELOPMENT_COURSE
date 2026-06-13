import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import { tasksApi, projectsApi } from '../api/endpoints'
import { StatusBadge, StatCard, Spinner } from '../components/ui'
import { PageHeader } from '../components/layout'

const STATUS_COLORS = {
  new:         '#6366f1',
  not_started: '#6b7280',
  in_progress: '#3b82f6',
  blocked:     '#ef4444',
  completed:   '#22c55e',
}

const CUSTOM_TOOLTIP = ({ active, payload }) => {
  if (active && payload?.length) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm">
        <p className="text-white font-semibold">{payload[0].name}</p>
        <p className="text-gray-300">{payload[0].value} tasks</p>
      </div>
    )
  }
  return null
}

export default function DashboardPage() {
  const [tasks,    setTasks]    = useState([])
  const [projects, setProjects] = useState([])
  const [loading,  setLoading]  = useState(true)

  useEffect(() => {
    Promise.all([tasksApi.list(), projectsApi.list()])
      .then(([t, p]) => { setTasks(t.data); setProjects(p.data) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner />

  // Status counts for pie chart
  const statusCounts = tasks.reduce((acc, t) => {
    acc[t.status] = (acc[t.status] || 0) + 1
    return acc
  }, {})

  const pieData = Object.entries(statusCounts).map(([name, value]) => ({ name, value }))

  // Tasks per project for bar chart
  const projectMap = Object.fromEntries(projects.map(p => [p.id, p.name]))
  const tasksByProject = projects.map(p => ({
    name: p.name.length > 15 ? p.name.slice(0, 15) + '…' : p.name,
    tasks: tasks.filter(t => t.project_id === p.id).length,
    completed: tasks.filter(t => t.project_id === p.id && t.status === 'completed').length,
  }))

  const recentTasks = [...tasks].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 8)

  return (
    <div>
      <PageHeader title="Dashboard" />

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
        <StatCard label="Projects"   value={projects.length} icon="📁" />
        <StatCard label="Total Tasks" value={tasks.length}   icon="📋" />
        <StatCard label="In Progress" value={statusCounts.in_progress || 0} icon="⚡" color="text-blue-400" />
        <StatCard label="Blocked"     value={statusCounts.blocked     || 0} icon="🚫" color="text-red-400" />
        <StatCard label="Completed"   value={statusCounts.completed   || 0} icon="✅" color="text-green-400" />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* Bar chart */}
        <div className="card">
          <h2 className="font-semibold text-white mb-4">Tasks by Project</h2>
          {tasksByProject.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={tasksByProject} barCategoryGap="30%">
                <XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#6b7280', fontSize: 11 }} axisLine={false} tickLine={false} allowDecimals={false} />
                <Tooltip content={<CUSTOM_TOOLTIP />} cursor={{ fill: 'rgba(99,102,241,0.08)' }} />
                <Bar dataKey="tasks"     name="Total"     fill="#6366f1" radius={[4,4,0,0]} />
                <Bar dataKey="completed" name="Completed" fill="#22c55e" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-sm text-center py-12">No project data yet</p>
          )}
        </div>

        {/* Pie chart */}
        <div className="card">
          <h2 className="font-semibold text-white mb-4">Task Status Breakdown</h2>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                     dataKey="value" nameKey="name" paddingAngle={3}>
                  {pieData.map(({ name }) => (
                    <Cell key={name} fill={STATUS_COLORS[name] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip content={<CUSTOM_TOOLTIP />} />
                <Legend
                  formatter={(v) => <span className="text-gray-400 text-xs">{v.replace(/_/g, ' ')}</span>}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-sm text-center py-12">No tasks yet</p>
          )}
        </div>
      </div>

      {/* Recent tasks table */}
      <div className="card">
        <h2 className="font-semibold text-white mb-4">Recent Tasks</h2>
        {recentTasks.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-gray-500 border-b border-gray-800">
                  <th className="text-left pb-3 font-medium">Title</th>
                  <th className="text-left pb-3 font-medium">Project</th>
                  <th className="text-left pb-3 font-medium">Status</th>
                  <th className="text-left pb-3 font-medium">Due</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {recentTasks.map(t => (
                  <tr key={t.id} className="hover:bg-gray-800/50 transition-colors">
                    <td className="py-3 text-gray-200 font-medium">{t.title}</td>
                    <td className="py-3 text-gray-400">{projectMap[t.project_id] || '—'}</td>
                    <td className="py-3"><StatusBadge status={t.status} /></td>
                    <td className="py-3 text-gray-400">{t.due_date || '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm text-center py-8">No tasks yet. Create your first task!</p>
        )}
      </div>
    </div>
  )
}
