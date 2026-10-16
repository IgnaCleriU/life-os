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
    // No se pudo guardar el nuevo: si queda uno viejo en storage, se borra para
    // que no vuelva a leerse tras recargar. El token nuevo queda en memoria.
    try {
      window.localStorage.removeItem(TOKEN_KEY)
    } catch {
      // Storage no disponible del todo.
    }
  }
}

/**
 * Avisa cuando otra pestaña cambia el token guardado (evento `storage`). Recibe
 * el valor nuevo, o null si se borró. Devuelve la función para dejar de escuchar.
 */
export function subscribeToTokenChanges(onChange: (token: string | null) => void): () => void {
  const listener = (event: StorageEvent) => {
    // key null: localStorage.clear() en otra pestaña.
    if (event.key === null || event.key === TOKEN_KEY) onChange(event.newValue)
  }
  window.addEventListener('storage', listener)
  return () => window.removeEventListener('storage', listener)
}

/**
 * Borra el token solo si el guardado sigue siendo `expected`. Evita que un 401
 * tardío de un token anterior cierre la sesión del token nuevo. Devuelve si borró.
 */
export function clearTokenIfCurrent(expected: string | null): boolean {
  if (readToken() !== expected) return false
  clearToken()
  return true
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
