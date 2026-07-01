import axios from 'axios'

const ACCESS_KEY = 'otsu_access'
const REFRESH_KEY = 'otsu_refresh'

export const tokens = {
  get access() {
    return localStorage.getItem(ACCESS_KEY)
  },
  get refresh() {
    return localStorage.getItem(REFRESH_KEY)
  },
  set({ access, refresh }) {
    if (access) localStorage.setItem(ACCESS_KEY, access)
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh)
  },
  clear() {
    localStorage.removeItem(ACCESS_KEY)
    localStorage.removeItem(REFRESH_KEY)
  },
}

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use((config) => {
  const token = tokens.access
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// On a 401, try the refresh token once, then replay the original request.
let refreshing = null

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    const isAuthCall = original?.url?.includes('/auth/')
    if (error.response?.status !== 401 || original._retry || isAuthCall) {
      return Promise.reject(error)
    }
    if (!tokens.refresh) {
      tokens.clear()
      return Promise.reject(error)
    }
    original._retry = true
    try {
      refreshing =
        refreshing ||
        axios.post('/api/auth/refresh/', { refresh: tokens.refresh })
      const { data } = await refreshing
      refreshing = null
      tokens.set({ access: data.access })
      original.headers.Authorization = `Bearer ${data.access}`
      return api(original)
    } catch (refreshError) {
      refreshing = null
      tokens.clear()
      return Promise.reject(refreshError)
    }
  },
)

export default api
