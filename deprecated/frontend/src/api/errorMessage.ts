import { ApiError } from './client'

const CONNECTION_ERROR = 'No se pudo conectar con la API.'

/** Mensaje en español para mostrar al usuario: el de la API, o un fallo de conexión. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message
  return CONNECTION_ERROR
}
