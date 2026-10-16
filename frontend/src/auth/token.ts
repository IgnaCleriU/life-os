const TOKEN_KEY = 'lifeos.token'

/**
 * Respaldo en memoria: se usa cuando localStorage no está disponible (ventana
 * privada, datos bloqueados) o falla. El token dura entonces solo esta sesión.
 */
let memoryToken: string | null = null

/** Lee el token guardado. Nunca lanza: si el storage falla, devuelve el respaldo en memoria. */
export function readToken(): string | null {
  try {
    const stored = window.localStorage.getItem(TOKEN_KEY)
    if (stored) return stored
  } catch {
    // Storage no disponible: se usa el respaldo en memoria.
  }
  return memoryToken
}

/** Guarda el token. Nunca lanza. */
export function writeToken(token: string): void {
  memoryToken = token
  try {
    window.localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // Storage no disponible: queda solo en memoria.
  }
}

/** Borra el token. Nunca lanza. */
export function clearToken(): void {
  memoryToken = null
  try {
    window.localStorage.removeItem(TOKEN_KEY)
  } catch {
    // Storage no disponible: nada que borrar.
  }
}
