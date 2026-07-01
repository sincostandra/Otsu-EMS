import { createContext, useContext, useEffect, useState } from 'react'

import api, { tokens } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!tokens.access) {
      setLoading(false)
      return
    }
    api
      .get('/auth/me/')
      .then(({ data }) => setUser(data))
      .catch(() => tokens.clear())
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    const { data } = await api.post('/auth/login/', { email, password })
    tokens.set({ access: data.access, refresh: data.refresh })
    setUser(data.user)
    return data.user
  }

  const logout = () => {
    tokens.clear()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}
