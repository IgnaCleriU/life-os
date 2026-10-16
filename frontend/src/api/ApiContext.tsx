import { useMemo, type ReactNode } from 'react'
import { createApiClient } from './client'
import { ApiContext } from './useApi'

interface ApiProviderProps {
  token: string
  /** Se llama ante un 401 de cualquier ruta autenticada, con el token que lo causó. */
  onUnauthorized: (token: string | null) => void
  children: ReactNode
}

/** Provee un cliente de API autenticado con `token` a los componentes hijos. */
export function ApiProvider({ token, onUnauthorized, children }: ApiProviderProps) {
  const client = useMemo(
    () => createApiClient({ getToken: () => token, onUnauthorized }),
    [token, onUnauthorized],
  )
  return <ApiContext.Provider value={client}>{children}</ApiContext.Provider>
}
