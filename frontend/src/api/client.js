import axios from 'axios'

// ── Token bridge ───────────────────────────────────────────────
// AuthContext calls setTokenGetter() once on mount, passing its
// in-memory getToken() function. The interceptor below calls it
// on every request. Token never touches any browser storage.
let _getToken = () => null
let _refreshSession = async () => null
let _onUnauthorized = () => {
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export function setTokenGetter(fn) {
  _getToken = fn
}

export function setRefreshHandler(fn) {
  _refreshSession = fn
}

export function setUnauthorizedHandler(fn) {
  _onUnauthorized = fn
}

export const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// Attach JWT to every request from in-memory token only
apiClient.interceptors.request.use((config) => {
  const token = _getToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On 401 — reload to login (clears all state automatically)
apiClient.interceptors.response.use(
  (res) => res,
  async (err) => {
    const originalRequest = err.config || {}
    const isAuthCall = originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')

    if (err.response?.status === 401 && !originalRequest._retry && !isAuthCall) {
      originalRequest._retry = true
      try {
        const newAccessToken = await _refreshSession()
        if (newAccessToken) {
          originalRequest.headers = originalRequest.headers || {}
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return apiClient(originalRequest)
        }
      } catch {
        // fall through to unauthorized handling
      }
      _onUnauthorized()
    }

    return Promise.reject(err)
  }
)