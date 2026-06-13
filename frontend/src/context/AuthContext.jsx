import { createContext, useContext, useState, useCallback, useRef, useEffect } from 'react'
import { apiClient, setRefreshHandler, setTokenGetter, setUnauthorizedHandler } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const tokenRef        = useRef(null)
  const [user,  setUser]  = useState(null)
  const [isInitializing, setIsInitializing] = useState(true)
  // isLoggedIn is a plain boolean state — triggers re-renders for route guards
  // The actual token stays in the ref (never in storage)
  const [isLoggedIn, setIsLoggedIn] = useState(false)

  const clearAuth = useCallback(() => {
    tokenRef.current = null
    setUser(null)
    setIsLoggedIn(false)
  }, [])

  const refreshSession = useCallback(async () => {
    const { data } = await apiClient.post('/auth/refresh')
    tokenRef.current = data.access_token
    setUser({
      id:        data.user.id,
      username:  data.user.username,
      full_name: data.user.full_name ?? null,
      email:     data.user.email,
      roles:     data.user.roles    ?? [],
    })
    setIsLoggedIn(true)
    return data.access_token
  }, [])

  // Wire the token bridge once on mount
  useEffect(() => {
    setTokenGetter(() => tokenRef.current)
    setRefreshHandler(refreshSession)
    setUnauthorizedHandler(() => {
      clearAuth()
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    })
  }, [clearAuth, refreshSession])

  useEffect(() => {
    let mounted = true

    const init = async () => {
      if (window.location.pathname === '/login') {
        if (mounted) setIsInitializing(false)
        return
      }
      try {
        await refreshSession()
      } catch {
        if (mounted) clearAuth()
      } finally {
        if (mounted) setIsInitializing(false)
      }
    }

    init()
    return () => {
      mounted = false
    }
  }, [clearAuth, refreshSession])

  const login = useCallback(async (username, password) => {
    const { data } = await apiClient.post('/auth/login', { username, password })
    tokenRef.current = data.access_token
    setUser({
      id:        data.user.id,
      username:  data.user.username,
      full_name: data.user.full_name ?? null,
      email:     data.user.email,
      roles:     data.user.roles    ?? [],
    })
    setIsLoggedIn(true)   // ← triggers PrivateRoute re-render
    return data.user
  }, [])

  const logout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout')
    } finally {
      clearAuth()
    }
  }, [clearAuth])

  const isAdmin   = user?.roles?.includes('admin')        ?? false
  const isCreator = isAdmin || (user?.roles?.includes('task_creator') ?? false)

  return (
    <AuthContext.Provider value={{ user, isLoggedIn, isInitializing, login, logout, isAdmin, isCreator }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be inside AuthProvider')
  return ctx
}