import { useCallback, useEffect, useState } from 'react'
import { ApiProvider } from './api/ApiContext'
import { ApiError, createApiClient } from './api/client'
import LoginScreen from './auth/LoginScreen'
import { clearToken, clearTokenIfCurrent, readToken, subscribeToTokenChanges } from './auth/token'

export default function App() {
  const [token, setToken] = useState<string | null>(() => readToken())
  // Último token confirmado contra la API en esta carga de la app.
  const [verified, setVerified] = useState<string | null>(null)

  // Otra pestaña entró o salió: esta sigue su estado.
  useEffect(() => subscribeToTokenChanges(setToken), [])

  const logout = useCallback(() => {
    clearToken()
    setVerified(null)
    setToken(null)
  }, [])

  // Un 401 del token vigente cierra la sesión. Un 401 de un token que ya no es el
  // vigente se ignora. Si el storage guarda otro token (otra pestaña), no se borra.
  const handleUnauthorized = useCallback(
    (used: string | null) => {
      if (used !== token) return
      clearTokenIfCurrent(used)
      setVerified(null)
      setToken(null)
    },
    [token],
  )

  // Al entrar, LoginScreen ya validó el token.
  const login = useCallback((next: string) => {
    setVerified(next)
    setToken(next)
  }, [])

  // Un token que viene del storage al cargar (o de otra pestaña) se valida una vez.
  useEffect(() => {
    if (!token || verified === token) return
    let cancelled = false
    const api = createApiClient({ getToken: () => token })
    api.listProjects({ status: 'active' }).then(
      () => {
        if (!cancelled) setVerified(token)
      },
      (error: unknown) => {
        if (cancelled) return
        if (error instanceof ApiError && error.status === 401) {
          handleUnauthorized(token)
          return
        }
        // Sin 401 (API caída, red): se entra igual; las llamadas mostrarán el error.
        setVerified(token)
      },
    )
    return () => {
      cancelled = true
    }
  }, [token, verified, handleUnauthorized])

  if (!token) {
    return <LoginScreen onLogin={login} />
  }

  if (verified !== token) {
    return (
      <>
        <header className="app-header">
          <h1>Life OS</h1>
        </header>
        <main className="app-main">
          <p>Verificando sesión…</p>
        </main>
      </>
    )
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
        <p>Nada por aquí todavía.</p>
      </main>
    </ApiProvider>
  )
}
