import { createContext, useContext } from 'react'
import type { ApiClient } from './client'

// El contexto y el hook viven fuera de ApiContext.tsx: ese archivo solo exporta
// componentes, para que Fast Refresh funcione.
export const ApiContext = createContext<ApiClient | null>(null)

/** Devuelve el cliente de API del `ApiProvider` más cercano. */
export function useApi(): ApiClient {
  const client = useContext(ApiContext)
  if (!client) {
    throw new Error('useApi debe usarse dentro de <ApiProvider>')
  }
  return client
}
