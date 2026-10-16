import { useCallback, useState } from 'react'
import { ApiProvider } from './api/ApiContext'
import LoginScreen from './auth/LoginScreen'
import { clearToken, clearTokenIfCurrent, readToken } from './auth/token'
import ProjectsPage from './projects/ProjectsPage'

export default function App() {
  const [token, setToken] = useState<string | null>(() => readToken())

  const logout = useCallback(() => {
    clearToken()
    setToken(null)
  }, [])

  // Un 401 de un token que ya no es el vigente (p. ej. tras volver a entrar) no cierra la sesión nueva.
  const handleUnauthorized = useCallback((used: string | null) => {
    if (clearTokenIfCurrent(used)) setToken(null)
  }, [])

  // LoginScreen ya guardó el token al validarlo.
  const login = useCallback((next: string) => setToken(next), [])

  if (!token) {
    return <LoginScreen onLogin={login} />
  }

  return (
    <ApiProvider token={token} onUnauthorized={handleUnauthorized}>
      <header className="app-header">
        <h1>Life OS</h1>
        <button type="button" className="secondary" onClick={logout}>
          Salir
        </button>
      </header>
      <main className="app-main">
        <ProjectsPage />
      </main>
    </ApiProvider>
  )
}
