import { ApiProvider } from './api/ApiContext'
import LoginScreen from './auth/LoginScreen'
import { useSession } from './auth/useSession'

export default function App() {
  const { token, verified, login, logout, handleUnauthorized } = useSession()

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
