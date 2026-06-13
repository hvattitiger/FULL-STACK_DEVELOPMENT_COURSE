import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { usersApi, rolesApi } from '../api/endpoints'
import { RoleBadge, Modal, Field, EmptyState, ConfirmModal, Spinner } from '../components/ui'
import { PageHeader } from '../components/layout'

function UserForm({ defaultValues, onSubmit, onClose, isEdit }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues })
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Field label="Username *" error={errors.username?.message}>
        <input className="input" disabled={isEdit} {...register('username', { required: !isEdit })} />
      </Field>
      <Field label="Email *" error={errors.email?.message}>
        <input type="email" className="input" {...register('email', { required: 'Email required' })} />
      </Field>
      <Field label="Full Name">
        <input className="input" {...register('full_name')} />
      </Field>
      <Field label={isEdit ? 'New Password (leave blank to keep current)' : 'Password *'} error={errors.password?.message}>
        <input type="password" className="input"
          {...register('password', { required: !isEdit ? 'Password required' : false, minLength: { value: 8, message: 'Min 8 characters' } })} />
      </Field>
      <div className="flex justify-end gap-3 mt-2">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save User'}
        </button>
      </div>
    </form>
  )
}

export default function UsersPage() {
  const [users,   setUsers]   = useState([])
  const [roles,   setRoles]   = useState([])
  const [loading, setLoading] = useState(true)
  const [modal,   setModal]   = useState(null)
  const [confirm, setConfirm] = useState(null)
  const [roleModal, setRoleModal] = useState(null) // { userId }
  const [selectedRole, setSelectedRole] = useState('')

  const load = async () => {
    const [u, r] = await Promise.all([usersApi.list(), rolesApi.list()])
    setUsers(u.data); setRoles(r.data)
    setLoading(false)
  }
  useEffect(() => { load() }, [])

  const handleSave = async (data) => {
    const clean = { ...data, full_name: data.full_name || null }
    if (!clean.password) delete clean.password
    try {
      if (modal.mode === 'edit') {
        await usersApi.update(modal.user.id, clean)
        toast.success('User updated')
      } else {
        const { apiClient } = await import('../api/client')
        await apiClient.post('/auth/register', clean)
        toast.success('User created')
      }
      setModal(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); throw e }
  }

  const handleDelete = async (id) => {
    try { await usersApi.delete(id); toast.success('User deleted'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const handleAssignRole = async () => {
    if (!selectedRole) return
    try {
      await usersApi.assignRole(roleModal.userId, selectedRole)
      toast.success('Role assigned'); setRoleModal(null); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  const handleRemoveRole = async (userId, roleId) => {
    try { await usersApi.removeRole(userId, roleId); toast.success('Role removed'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Users"
        action={<button className="btn-primary" onClick={() => setModal({ mode: 'create' })}>+ New User</button>}
      />

      {users.length === 0 ? (
        <EmptyState icon="👥" title="No users" description="Create the first user account." />
      ) : (
        <div className="card overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="border-b border-gray-800">
                <tr className="text-gray-500">
                  {['Username','Email','Full Name','Roles','Status','Actions'].map(h => (
                    <th key={h} className="text-left px-4 py-3 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {users.map(u => (
                  <tr key={u.id} className="hover:bg-gray-800/40 transition-colors">
                    <td className="px-4 py-3 font-semibold text-gray-200">{u.username}</td>
                    <td className="px-4 py-3 text-gray-400">{u.email}</td>
                    <td className="px-4 py-3 text-gray-400">{u.full_name || '—'}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {u.roles.map(r => (
                          <span key={r} className="group relative">
                            <RoleBadge role={r} />
                            <button
                              onClick={() => handleRemoveRole(u.id, roles.find(x => x.name === r)?.id)}
                              className="absolute -top-1 -right-1 w-3.5 h-3.5 bg-red-500 rounded-full text-white text-[8px] hidden group-hover:flex items-center justify-center"
                            >×</button>
                          </span>
                        ))}
                        <button
                          onClick={() => { setRoleModal({ userId: u.id }); setSelectedRole('') }}
                          className="text-xs text-indigo-400 hover:text-indigo-300 border border-indigo-500/30 rounded-full px-1.5 py-0.5">
                          + Role
                        </button>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`badge ${u.is_active ? 'bg-green-500/15 text-green-400' : 'bg-red-500/15 text-red-400'}`}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button className="btn-secondary btn-sm" onClick={() => setModal({ mode: 'edit', user: u })}>Edit</button>
                        <button className="btn-danger btn-sm" onClick={() => setConfirm(u.id)}>Del</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* User modal */}
      <Modal open={!!modal} onClose={() => setModal(null)} title={modal?.mode === 'edit' ? 'Edit User' : 'New User'}>
        {modal && <UserForm defaultValues={modal.user || {}} onSubmit={handleSave} onClose={() => setModal(null)} isEdit={modal.mode === 'edit'} />}
      </Modal>

      {/* Assign Role modal */}
      <Modal open={!!roleModal} onClose={() => setRoleModal(null)} title="Assign Role" size="sm">
        <Field label="Select Role">
          <select className="input" value={selectedRole} onChange={e => setSelectedRole(e.target.value)}>
            <option value="">— Choose role —</option>
            {roles.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
          </select>
        </Field>
        <div className="flex justify-end gap-3">
          <button className="btn-secondary" onClick={() => setRoleModal(null)}>Cancel</button>
          <button className="btn-primary" onClick={handleAssignRole}>Assign</button>
        </div>
      </Modal>

      {/* Confirm delete */}
      <ConfirmModal open={!!confirm} onClose={() => setConfirm(null)}
        onConfirm={() => handleDelete(confirm)} title="Delete User"
        message="This user will be permanently deleted." />
    </div>
  )
}
