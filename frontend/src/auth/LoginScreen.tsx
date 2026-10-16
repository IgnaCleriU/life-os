import { useState, type FormEvent } from 'react'
import { ApiError, createApiClient } from '../api/client'
import { writeToken } from './token'

interface LoginScreenProps {
  onLogin: (token: string) => void
}

/** Mensaje para el usuario según el error de validar el token. */
function messageFor(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) return 'Token inválido'
    if (error.status === 403) {
      return 'Este host no está en LIFEOS_ALLOWED_HOSTS de la API'
    }
  }
  return 'No se pudo conectar con la API'
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [value, setValue] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const token = value.trim()
    if (!token) {
      setError('Ingresá el token de la API')
      return
    }

    setBusy(true)
    setError(null)
    // Cliente propio con el token candidato: un 401 acá no debe cerrar una sesión existente.
    const api = createApiClient({ getToken: () => token })
    try {
      await api.listProjects()
    } catch (err) {
      setError(messageFor(err))
      setBusy(false)
      return
    }
    writeToken(token)
    onLogin(token)
  }

  return (
    <>
      <header className="app-header">
        <h1>Life OS</h1>
      </header>
      <main className="app-main">
        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <label htmlFor="api-token">API token</label>
          <input
            id="api-token"
            name="api-token"
            type="password"
            autoComplete="off"
            autoCapitalize="none"
            spellCheck={false}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            aria-invalid={error !== null}
            aria-describedby={error ? 'login-error' : undefined}
          />
          {error && (
            <p id="login-error" role="alert" className="form-error">
              {error}
            </p>
          )}
          <button type="submit" disabled={busy}>
            {busy ? 'Verificando…' : 'Entrar'}
          </button>
        </form>
      </main>
    </>
  )
}
