import { apiClient } from './client'

// ── Auth ──────────────────────────────────────────────────────
export const authApi = {
  login:    (data) => apiClient.post('/auth/login', data),
  refresh:  ()     => apiClient.post('/auth/refresh'),
  logout:   ()     => apiClient.post('/auth/logout'),
  register: (data) => apiClient.post('/auth/register', data),
  me:       ()     => apiClient.get('/users/me'),
}

// ── Users ─────────────────────────────────────────────────────
export const usersApi = {
  list:       ()           => apiClient.get('/users/'),
  get:        (id)         => apiClient.get(`/users/${id}`),
  update:     (id, data)   => apiClient.patch(`/users/${id}`, data),
  delete:     (id)         => apiClient.delete(`/users/${id}`),
  assignRole: (id, roleId) => apiClient.post(`/users/${id}/roles`, { role_id: roleId }),
  removeRole: (id, roleId) => apiClient.delete(`/users/${id}/roles/${roleId}`),
}

// ── Roles ─────────────────────────────────────────────────────
export const rolesApi = {
  list:   ()       => apiClient.get('/roles/'),
  create: (data)   => apiClient.post('/roles/', data),
  delete: (id)     => apiClient.delete(`/roles/${id}`),
}

// ── Projects ──────────────────────────────────────────────────
export const projectsApi = {
  list:   ()         => apiClient.get('/projects/'),
  get:    (id)       => apiClient.get(`/projects/${id}`),
  create: (data)     => apiClient.post('/projects/', data),
  update: (id, data) => apiClient.patch(`/projects/${id}`, data),
  delete: (id)       => apiClient.delete(`/projects/${id}`),
}

// ── Tasks ─────────────────────────────────────────────────────
export const tasksApi = {
  list:     (projectId) => apiClient.get('/tasks/', { params: projectId ? { project_id: projectId } : {} }),
  get:      (id)        => apiClient.get(`/tasks/${id}`),
  create:   (data)      => apiClient.post('/tasks/', data),
  update:   (id, data)  => apiClient.patch(`/tasks/${id}`, data),
  setStatus:(id, status)=> apiClient.patch(`/tasks/${id}/status`, { status }),
  delete:   (id)        => apiClient.delete(`/tasks/${id}`),
  complete: (id)        => apiClient.post(`/tasks/${id}/complete`),
  assign:   (id, uid)   => apiClient.post(`/tasks/${id}/assign/${uid}`),
}