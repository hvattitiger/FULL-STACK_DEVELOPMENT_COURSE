// ── Status Badge ──────────────────────────────────────────────
const STATUS_STYLES = {
  new:         'bg-indigo-500/15 text-indigo-400',
  not_started: 'bg-gray-500/15 text-gray-400',
  in_progress: 'bg-blue-500/15 text-blue-400',
  blocked:     'bg-red-500/15 text-red-400',
  completed:   'bg-green-500/15 text-green-400',
}

export function StatusBadge({ status }) {
  return (
    <span className={`badge ${STATUS_STYLES[status] ?? 'bg-gray-500/15 text-gray-400'}`}>
      {status?.replace(/_/g, ' ')}
    </span>
  )
}

// ── Role Badge ────────────────────────────────────────────────
const ROLE_STYLES = {
  admin:        'bg-indigo-500/20 text-indigo-300',
  task_creator: 'bg-yellow-500/20 text-yellow-300',
  viewer:       'bg-green-500/20 text-green-300',
}

export function RoleBadge({ role }) {
  return (
    <span className={`badge ${ROLE_STYLES[role] ?? 'bg-gray-500/20 text-gray-300'}`}>
      {role}
    </span>
  )
}

// ── Modal ─────────────────────────────────────────────────────
export function Modal({ open, onClose, title, children, size = 'md' }) {
  if (!open) return null
  const sizes = { sm: 'max-w-sm', md: 'max-w-md', lg: 'max-w-lg', xl: 'max-w-2xl' }
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className={`card w-full ${sizes[size]} max-h-[90vh] overflow-y-auto`}>
        <div className="flex items-center justify-between mb-5">
          <h3 className="text-lg font-bold text-white">{title}</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-300 text-xl leading-none">×</button>
        </div>
        {children}
      </div>
    </div>
  )
}

// ── Form Field ────────────────────────────────────────────────
export function Field({ label, error, children }) {
  return (
    <div className="mb-4">
      {label && <label className="label">{label}</label>}
      {children}
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  )
}

// ── Empty State ───────────────────────────────────────────────
export function EmptyState({ icon = '📭', title, description }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-5xl mb-4">{icon}</div>
      <h3 className="text-lg font-semibold text-gray-300 mb-2">{title}</h3>
      {description && <p className="text-gray-500 text-sm max-w-xs">{description}</p>}
    </div>
  )
}

// ── Confirm Dialog ────────────────────────────────────────────
export function ConfirmModal({ open, onClose, onConfirm, title, message }) {
  return (
    <Modal open={open} onClose={onClose} title={title} size="sm">
      <p className="text-gray-400 text-sm mb-6">{message}</p>
      <div className="flex justify-end gap-3">
        <button className="btn-secondary" onClick={onClose}>Cancel</button>
        <button className="btn-danger" onClick={() => { onConfirm(); onClose() }}>Delete</button>
      </div>
    </Modal>
  )
}

// ── Stat Card ─────────────────────────────────────────────────
export function StatCard({ label, value, icon, color = 'text-white' }) {
  return (
    <div className="card flex items-center gap-4">
      <div className="text-3xl">{icon}</div>
      <div>
        <div className={`text-2xl font-bold ${color}`}>{value}</div>
        <div className="text-gray-500 text-sm">{label}</div>
      </div>
    </div>
  )
}

// ── Loading Spinner ───────────────────────────────────────────
export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin" />
    </div>
  )
}
