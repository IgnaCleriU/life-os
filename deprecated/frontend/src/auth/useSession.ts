import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, createApiClient } from '../api/client'
import { clearToken, clearTokenIfCurrent, readToken, subscribeToTokenChanges } from './token'

/** Estado de sesión de la app: token vigente, si ya fue validado y las acciones para cambiarlo. */
export function useSession() {
  const [token, setToken] = useState<string | null>(() => readToken())
  // Último token confirmado contra la API en esta carga de la app.
  const [verified, setVerified] = useState<string | null>(null)

  // Lo que leen los 401 tardíos: el token vigente ahora, no el de la closure que los disparó.
  const tokenRef = useRef(token)
  useEffect(() => {
    tokenRef.current = token
  }, [token])

  // Otra pestaña entró o salió: esta sigue su estado.
  useEffect(() => subscribeToTokenChanges(setToken), [])

  const logout = useCallback(() => {
    clearToken()
    setVerified(null)
    setToken(null)
  }, [])

  // Un 401 del token vigente cierra la sesión. Un 401 de un token que ya no es el
  // vigente se ignora. Si el storage guarda otro token (otra pestaña), no se borra.
  const handleUnauthorized = useCallback((used: string | null) => {
    if (used !== tokenRef.current) return
    clearTokenIfCurrent(used)
    setVerified(null)
    setToken(null)
  }, [])

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

  return { token, verified, login, logout, handleUnauthorized }
}
