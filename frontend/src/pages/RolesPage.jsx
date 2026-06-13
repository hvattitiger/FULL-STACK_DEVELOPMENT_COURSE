
import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { rolesApi } from '../api/endpoints'
import { Modal, Field, EmptyState, ConfirmModal, Spinner } from '../components/ui'
import { PageHeader } from '../components/layout'

const DEFAULT_ROLES = ['admin', 'task_creator', 'viewer']

export default function RolesPage() {
  const [roles,   setRoles]   = useState([])
  const [loading, setLoading] = useState(true)
  const [modal,   setModal]   = useState(false)
  const [confirm, setConfirm] = useState(null)

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()

  const load = () => rolesApi.list().then(r => setRoles(r.data)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleCreate = async (data) => {
    try {
      await rolesApi.create({ name: data.name, description: data.description || null })
      toast.success('Role created')
      reset(); setModal(false); load()
    } catch (e) { toast.error(e.response?.data?.detail || 'Error'); throw e }
  }

  const handleDelete = async (id) => {
    try { await rolesApi.delete(id); toast.success('Role deleted'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed') }
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Roles"
        action={<button className="btn-primary" onClick={() => { reset(); setModal(true) }}>+ New Role</button>}
      />

      {roles.length === 0 ? (
        <EmptyState icon="🔐" title="No roles" description="Create roles to assign to users." />
      ) : (
        <div className="card overflow-hidden p-0">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-800">
              <tr className="text-gray-500">
                {['Name', 'Description', 'Type', 'Actions'].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {roles.map(r => (
                <tr key={r.id} className="hover:bg-gray-800/40 transition-colors">
                  <td className="px-4 py-3 font-semibold text-gray-200">{r.name}</td>
                  <td className="px-4 py-3 text-gray-400">{r.description || '—'}</td>
                  <td className="px-4 py-3">
                    <span className={`badge ${DEFAULT_ROLES.includes(r.name) ? 'bg-indigo-500/15 text-indigo-400' : 'bg-gray-500/15 text-gray-400'}`}>
                      {DEFAULT_ROLES.includes(r.name) ? 'System' : 'Custom'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    {!DEFAULT_ROLES.includes(r.name) && (
                      <button className="btn-danger btn-sm" onClick={() => setConfirm(r.id)}>Delete</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Modal open={modal} onClose={() => setModal(false)} title="New Role" size="sm">
        <form onSubmit={handleSubmit(handleCreate)}>
          <Field label="Role Name *" error={errors.name?.message}>
            <input className="input" placeholder="e.g. reviewer"
              {...register('name', { required: 'Name required' })} />
          </Field>
          <Field label="Description">
            <textarea className="input resize-none min-h-[60px]"
              placeholder="What can this role do?" {...register('description')} />
          </Field>
          <div className="flex justify-end gap-3">
            <button type="button" className="btn-secondary" onClick={() => setModal(false)}>Cancel</button>
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? 'Creating…' : 'Create Role'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmModal open={!!confirm} onClose={() => setConfirm(null)}
        onConfirm={() => handleDelete(confirm)} title="Delete Role"
        message="This role will be removed from all users." />
    </div>
  )
}
