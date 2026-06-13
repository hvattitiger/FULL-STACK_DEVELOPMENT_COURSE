import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'
import { projectsApi } from '../api/endpoints'
import { Modal, Field, EmptyState, ConfirmModal, Spinner } from '../components/ui'
import { PageHeader } from '../components/layout'
import { useAuth } from '../context/AuthContext'

function ProjectForm({ defaultValues, onSubmit, onClose }) {
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues })

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <Field label="Project Name *" error={errors.name?.message}>
        <input className="input" placeholder="Website Redesign" {...register('name', { required: 'Name is required' })} />
      </Field>
      <Field label="Description" error={errors.description?.message}>
        <textarea className="input min-h-[80px] resize-none" placeholder="Project goals and scope..."
          {...register('description')} />
      </Field>
      <div className="grid grid-cols-2 gap-3">
        <Field label="Start Date">
          <input type="date" className="input" {...register('start_date')} />
        </Field>
        <Field label="End Date">
          <input type="date" className="input" {...register('end_date')} />
        </Field>
      </div>
      <div className="flex justify-end gap-3 mt-2">
        <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving…' : 'Save Project'}
        </button>
      </div>
    </form>
  )
}

export default function ProjectsPage() {
  const { isAdmin, isCreator } = useAuth()
  const [projects, setProjects] = useState([])
  const [loading,  setLoading]  = useState(true)
  const [modal,    setModal]    = useState(null) // null | { mode: 'create'|'edit', project? }
  const [confirm,  setConfirm]  = useState(null) // projectId to delete

  const load = () => projectsApi.list().then(r => setProjects(r.data)).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleSave = async (data) => {
    const clean = { ...data, description: data.description || null, start_date: data.start_date || null, end_date: data.end_date || null }
    try {
      if (modal.mode === 'edit') {
        await projectsApi.update(modal.project.id, clean)
        toast.success('Project updated')
      } else {
        await projectsApi.create(clean)
        toast.success('Project created')
      }
      setModal(null)
      load()
    } catch (e) {
      toast.error(e.response?.data?.detail || 'Something went wrong')
      throw e
    }
  }

  const handleDelete = async (id) => {
    try { await projectsApi.delete(id); toast.success('Project deleted'); load() }
    catch (e) { toast.error(e.response?.data?.detail || 'Failed to delete') }
  }

  if (loading) return <Spinner />

  return (
    <div>
      <PageHeader
        title="Projects"
        action={isCreator && (
          <button className="btn-primary" onClick={() => setModal({ mode: 'create' })}>
            + New Project
          </button>
        )}
      />

      {projects.length === 0 ? (
        <EmptyState icon="📁" title="No projects yet" description="Create your first project to get started." />
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
          {projects.map(p => (
            <div key={p.id} className="card hover:border-indigo-500/50 transition-colors group">
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-semibold text-white group-hover:text-indigo-300 transition-colors">{p.name}</h3>
              </div>
              <p className="text-gray-500 text-sm mb-4 line-clamp-2">
                {p.description || <em>No description</em>}
              </p>
              <div className="text-xs text-gray-600 mb-4 space-y-1">
                <div>📅 {p.start_date || '?'} → {p.end_date || '?'}</div>
              </div>
              <div className="flex gap-2 flex-wrap">
                {isCreator && (
                  <button className="btn-secondary btn-sm" onClick={() => setModal({ mode: 'edit', project: p })}>
                    Edit
                  </button>
                )}
                {isAdmin && (
                  <button className="btn-danger btn-sm" onClick={() => setConfirm(p.id)}>
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit Modal */}
      <Modal
        open={!!modal}
        onClose={() => setModal(null)}
        title={modal?.mode === 'edit' ? 'Edit Project' : 'New Project'}
      >
        {modal && (
          <ProjectForm
            defaultValues={modal.project || {}}
            onSubmit={handleSave}
            onClose={() => setModal(null)}
          />
        )}
      </Modal>

      {/* Delete Confirm */}
      <ConfirmModal
        open={!!confirm}
        onClose={() => setConfirm(null)}
        onConfirm={() => handleDelete(confirm)}
        title="Delete Project"
        message="This will permanently delete the project and all its tasks. This action cannot be undone."
      />
    </div>
  )
}
