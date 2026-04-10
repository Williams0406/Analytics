/**
 * Lumiq - Utilidades de autenticación
 * Funciones para manejar tokens, sesión y estado del usuario.
 */
import apiClient from './axios'

const TOKEN_KEY = 'lumiq_access_token'
const REFRESH_KEY = 'lumiq_refresh_token'
const USER_KEY = 'lumiq_user'

// ─── Tokens ─────────────────────────────────────────────────────────────────
export const saveTokens = (access, refresh) => {
  localStorage.setItem(TOKEN_KEY, access)
  localStorage.setItem(REFRESH_KEY, refresh)
}

export const getAccessToken = () =>
  typeof window !== 'undefined' ? localStorage.getItem(TOKEN_KEY) : null

export const getRefreshToken = () =>
  typeof window !== 'undefined' ? localStorage.getItem(REFRESH_KEY) : null

export const clearSession = () => {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(USER_KEY)
}

// ─── Usuario ─────────────────────────────────────────────────────────────────
export const saveUser = (user) =>
  localStorage.setItem(USER_KEY, JSON.stringify(user))

export const getStoredUser = () => {
  if (typeof window === 'undefined') return null
  try {
    return JSON.parse(localStorage.getItem(USER_KEY))
  } catch {
    return null
  }
}

// ─── Acciones de Auth ────────────────────────────────────────────────────────
export const login = async (email, password) => {
  const { data } = await apiClient.post('/api/auth/login/', { email, password })
  saveTokens(data.access, data.refresh)
  // Fetch del perfil completo
  const profile = await apiClient.get('/api/auth/profile/')
  saveUser(profile.data)
  return profile.data
}

export const register = async (formData) => {
  const { data } = await apiClient.post('/api/auth/register/', formData)
  saveTokens(data.tokens.access, data.tokens.refresh)
  saveUser(data.user)
  return data.user
}

export const logout = async () => {
  try {
    const refresh = getRefreshToken()
    if (refresh) {
      await apiClient.post('/api/auth/logout/', { refresh })
    }
  } finally {
    clearSession()
  }
}

export const isAuthenticated = () => !!getAccessToken()