/**
 * Lumiq - Cliente HTTP centralizado
 * Toda comunicación con el backend pasa por aquí.
 * Maneja automáticamente: base URL, tokens JWT, refresh, errores.
 */
import axios from 'axios'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ─── Instancia principal ────────────────────────────────────────────────────
const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
})

// ─── Interceptor de REQUEST: adjunta el JWT a cada llamada ──────────────────
apiClient.interceptors.request.use(
  (config) => {
    // Solo en browser (no en SSR)
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('lumiq_access_token')
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ─── Interceptor de RESPONSE: maneja token expirado (401) ───────────────────
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('lumiq_refresh_token')
        if (!refreshToken) throw new Error('No refresh token')

        const { data } = await axios.post(`${API_URL}/api/auth/token/refresh/`, {
          refresh: refreshToken,
        })

        localStorage.setItem('lumiq_access_token', data.access)
        originalRequest.headers.Authorization = `Bearer ${data.access}`
        return apiClient(originalRequest)
      } catch {
        // Token de refresh inválido → limpiar sesión
        if (typeof window !== 'undefined') {
          localStorage.removeItem('lumiq_access_token')
          localStorage.removeItem('lumiq_refresh_token')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient