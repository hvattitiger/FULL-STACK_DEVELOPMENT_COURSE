import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { tasksApi, projectsApi, usersApi } from '../api/endpoints'
import { StatusBadge, Modal, Field, EmptyState, ConfirmModal, Spinner } from '../components/ui'
import { PageHeader } from '../components/layout'
import { useAuth } from '../context/AuthContext'

const STATUSES = ['new', 'not_started', 'in_progress', 'blocked', 'completed']

const STATUS_LABELS = {
  new: 'New', not_started: 'Not Started',
  in_progress: 'In Progress', blocked: 'Blocked', completed: 'Completed',
}

const STATUS_COLORS = {
  new:         'border-indigo-500/40 bg-indigo-500/5',
  not_started: 'border-gray-600/40 bg-gray-800/30',
  in_progress: 'border-blue-500/40 bg-blue-500/5',
  blocked:     'border-red-500/40 bg-red-500/5',
  completed:   'border-green-500/40 bg-green-500/5',
}

// ── Task Form ─────────────────────────────────────────────────
function TaskForm({ defaultValues, projects, users, onSubmit, onClose, isCreator }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Field label="Title *" error={errors.title?.message}>
        <input className="input" placeholder="Fix login bug"
          {...register('title', { required: 'Title is required' })} />
      </Field>
      <Field label="Description">
        <textarea className="input min-h-[70px] resize-none" placeholder="Details..."
          {...register('description')} />
      </Field>
      <Field label="Project *" error={errors.project_id?.message}>
        <select className="input" {...register('project_id', { required: 'Project is required' })}>
          <option value="">— Select project —</option>
          {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Status">
          <select className="input" {...register('status')}>
            {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
          </select>
        </Field>
        <Field label="Due Date">
          <input type="date" className="input" {...register('due_date')} />
        </Field>
      </div>
      {/* FIX 1: Assignee dropdown visible to task_creator AND admin */}
      {isCreator && (
        <Field label="Assign To">
          <select className="input" {...register('assignee_id')}>
            <option value="">— Unassigned —</option>
            {users.map(u => (
              <option key={u.id} value={u.id}>
                {u.username}{u.full_name ? ` (${u.full_name})` : ''}
              </option>
            ))}
          </select>
        </Field>
      )}
      <div className="flex justify-end gap-3 mt-2">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save Task'}
        </button>
      </div>
    </form>
  )
}

// ── Kanban Card ───────────────────────────────────────────────
function KanbanCard({ task, userMap, onEdit, onDelete, onStatusChange, canEdit, canChangeStatus }) {
  return (
    <div className="bg-gray-900 border border-gray-700 rounded-lg p-3 hover:border-indigo-500/50 transition-colors group">
      <div className="font-medium text-sm text-gray-200 mb-1 group-hover:text-white">{task.title}</div>
      {task.description && (
        <p className="text-gray-500 text-xs mb-2 line-clamp-2">{task.description}</p>
      )}
      <div className="flex flex-col gap-1 text-xs text-gray-600 mb-3">
        {task.due_date && <span>📅 {task.due_date}</span>}
        {task.assignee_id && <span>👤 {userMap[task.assignee_id] || '—'}</span>}
      </div>
      <div className="flex gap-1.5 flex-wrap">
        {canEdit && (
          <button className="btn-secondary btn-sm" onClick={() => onEdit(task)}>Edit</button>
        )}
        {canChangeStatus && (
          <select
            className="input btn-sm min-w-[130px]"
            value={task.status}
            onChange={(e) => onStatusChange(task.id, e.target.value)}
          >
            {STATUSES.map(s => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </select>
        )}
        {canEdit && (
          <button className="btn-danger btn-sm" onClick={() => onDelete(task.id)}>×</button>
        )}
      </div>
    </div>
  )
}

// ── Main Page ─────────────────────────────────────────────────
export default function TasksPage() {
  const { isAdmin, isCreator, user } = useAuth()
  const [tasks,      setTasks]      = useState([])
  const [projects,   setProjects]   = useState([])
  const [users,      setUsers]      = useState([])
  const [loading,    setLoading]    = useState(true)
  const [view,       setView]       = useState('table')
  const [filterProj, setFilterProj] = useState('')
  const [filterStat, setFilterStat] = useState('')
  const [modal,      setModal]      = useState(null)
  const [confirm,    setConfirm]    = useState(null)

  const load = async () => {
    try {
      const [t, p] = await Promise.all([
        tasksApi.list(filterProj || undefined),
        projectsApi.list(),
      ])
      setTasks(t.data)
      setProjects(p.data)

      // FIX 1: task_creator also needs user list to assign tasks
      // Viewers don't need it — they can't assign
      if (isCreator) {
        const u = await usersApi.list()
        setUsers(u.data)
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [filterProj])

  const userMap    = Object.fromEntries(users.map(u => [u.id, u.username]))
  const projectMap = Object.fromEntries(projects.map(p => [p.id, p.name]))

  // FIX 2: Viewers only see tasks assigned to them — enforced on backend too,
  // but we also filter locally to be safe in case cached data is stale
  const filtered = tasks.filter(t => {
    const matchStatus  = !filterStat || t.status === filterStat
    const matchViewer  = isCreator || t.assignee_id === user?.id
    return matchStatus && matchViewer
  })

  const handleSave = async (data) => {
    const clean = {
      ...data,
      description: data.description || null,
      due_date:    data.due_date    || null,
      assignee_id: data.assignee_id || null,
    }
    try {
      if (modal.mode === 'edit') {
        await tasksApi.update(modal.task.id, clean)
        toast.success('Task updated')
      } else {
        await tasksApi.create(clean)
        toast.success('Task created')
      }
      setModal(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); throw e }
  }

  const handleDelete = async (id) => {
    try { await tasksApi.delete(id); toast.success('Task deleted'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const handleStatusChange = async (id, newStatus) => {
    try {
      await tasksApi.setStatus(id, newStatus)
      toast.success('Task status updated')
      load()
    }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const canChangeStatus = (task) =>
    isAdmin || isCreator || task.assignee_id === user?.id

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Tasks"
        action={
          <div className="flex items-center gap-3">
            <div className="flex bg-gray-800 rounded-lg p-1 gap-1">
              {['table', 'kanban'].map(v => (
                <button key={v} onClick={() => setView(v)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    view === v ? 'bg-indigo-600 text-white' : 'text-gray-400 hover:text-gray-200'
                  }`}>
                  {v === 'table' ? '☰ Table' : '⬜ Kanban'}
                </button>
              ))}
            </div>
            {isCreator && (
              <button className="btn-primary" onClick={() => setModal({ mode: 'create' })}>
                + New Task
              </button>
            )}
          </div>
        }
      />

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <select className="input max-w-[200px]" value={filterProj}
          onChange={e => setFilterProj(e.target.value)}>
          <option value="">All Projects</option>
          {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
        </select>
        <select className="input max-w-[160px]" value={filterStat}
          onChange={e => setFilterStat(e.target.value)}>
          <option value="">All Statuses</option>
          {STATUSES.map(s => <option key={s} value={s}>{STATUS_LABELS[s]}</option>)}
        </select>
        {/* Viewer info banner */}
        {!isCreator && (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-xs text-indigo-400">
            👤 Showing only tasks assigned to you
          </div>
        )}
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon="✅" title="No tasks found"
          description={isCreator ? "Create a new task to get started." : "No tasks are assigned to you yet."} />
      ) : view === 'table' ? (
        /* ── TABLE VIEW ── */
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-800">
                <tr className="text-gray-500">
                  {['Title', 'Project', 'Status', 'Due Date', 'Assignee', 'Actions'].map(h => (
                    <th key={h} className="text-left px-4 py-3 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {filtered.map(t => (
                  <tr key={t.id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-200">{t.title}</td>
                    <td className="px-4 py-3 text-gray-400">{projectMap[t.project_id] || '—'}</td>
                    <td className="px-4 py-3"><StatusBadge status={t.status} /></td>
                    <td className="px-4 py-3 text-gray-400">{t.due_date || '—'}</td>
                    <td className="px-4 py-3 text-gray-400">
                      {t.assignee_id
                        ? (userMap[t.assignee_id] || '—')
                        : <em className="text-gray-600">Unassigned</em>}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        {isCreator && (
                          <button className="btn-secondary btn-sm"
                            onClick={() => setModal({ mode: 'edit', task: t })}>Edit</button>
                        )}
                        {canChangeStatus(t) && (
                          <select
                            className="input btn-sm min-w-[140px]"
                            value={t.status}
                            onChange={(e) => handleStatusChange(t.id, e.target.value)}
                          >
                            {STATUSES.map(s => (
                              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
                            ))}
                          </select>
                        )}
                        {isAdmin && (
                          <button className="btn-danger btn-sm"
                            onClick={() => setConfirm(t.id)}>Del</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        /* ── KANBAN VIEW ── */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-4">
          {STATUSES.map(status => {
            const colTasks = filtered.filter(t => t.status === status)
            return (
              <div key={status} className={`rounded-xl border p-3 ${STATUS_COLORS[status]}`}>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-bold text-gray-400 uppercase tracking-wide">
                    {STATUS_LABELS[status]}
                  </span>
                  <span className="text-xs bg-gray-800 text-gray-400 rounded-full px-2 py-0.5">
                    {colTasks.length}
                  </span>
                </div>
                <div className="space-y-2">
                  {colTasks.map(task => (
                    <KanbanCard
                      key={task.id}
                      task={task}
                      userMap={userMap}
                      onEdit={(t) => setModal({ mode: 'edit', task: t })}
                      onDelete={(id) => setConfirm(id)}
                      onStatusChange={handleStatusChange}
                      canEdit={isCreator}
                      canChangeStatus={canChangeStatus(task)}
                    />
                  ))}
                  {colTasks.length === 0 && (
                    <p className="text-gray-700 text-xs text-center py-4">Empty</p>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Modal */}
      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title={modal?.mode === 'edit' ? 'Edit Task' : 'New Task'}
        size="lg"
      >
        {modal && (
          <TaskForm
            defaultValues={modal.task || { status: 'new' }}
            projects={projects}
            users={users}
            onSubmit={handleSave}
            onClose={() => setModal(null)}
            isCreator={isCreator}
          />
        )}
      </Modal>

      {/* Confirm delete */}
      <ConfirmModal
        open={!!confirm}
        onClose={() => setConfirm(null)}
        onConfirm={() => handleDelete(confirm)}
        title="Delete Task"
        message="This task will be permanently deleted."
      />
    </div>
  )
}