import { useCallback, useState } from 'react'
import { ApiProvider } from './api/ApiContext'
import LoginScreen from './auth/LoginScreen'
import { clearToken, readToken } from './auth/token'

export default function App() {
  const [token, setToken] = useState<string | null>(() => readToken())

  const logout = useCallback(() => {
    clearToken()
    setToken(null)
  }, [])

  // LoginScreen ya guardó el token al validarlo.
  const login = useCallback((next: string) => setToken(next), [])

  if (!token) {
    return <LoginScreen onLogin={login} />
  }

  return (
    <ApiProvider token={token} onUnauthorized={logout}>
      <header className="app-header">
        <h1>Life OS</h1>
        <button type="button" className="secondary" onClick={logout}>
          Salir
        </button>
      </header>
      <main className="app-main">
        <p>Nada por aquí todavía.</p>
      </main>
    </ApiProvider>
  )
}
