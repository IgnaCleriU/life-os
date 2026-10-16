import { act, fireEvent, render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { ApiProvider } from './api/ApiContext'
import { useApi } from './api/useApi'
import { clearToken, writeToken } from './auth/token'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

/** Respuesta de GET /projects?status=active usada por la validación al cargar. */
function projectsOk() {
  return jsonResponse(200, [])
}

function unauthorized() {
  return jsonResponse(401, { error: { code: 'unauthorized', message: 'Missing or invalid bearer token.' } })
}

function bearerOf(init: unknown): string | null {
  return new Headers((init as RequestInit).headers).get('Authorization')
}

afterEach(() => {
  vi.unstubAllGlobals()
  clearToken()
  window.localStorage.clear()
})

describe('App without a stored token', () => {
  it('shows the login screen and does not call the API', () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    expect(screen.getByLabelText('API token')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Salir' })).not.toBeInTheDocument()
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('logs in through the login screen and shows the shell without validating twice', async () => {
    const fetchMock = vi.fn(async () => projectsOk())
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)

    fireEvent.change(screen.getByLabelText('API token'), { target: { value: 'fresh' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(window.localStorage.getItem('lifeos.token')).toBe('fresh')
    expect(fetchMock).toHaveBeenCalledOnce()
  })
})

describe('App with a stored token', () => {
  it('validates the stored token once on mount, then shows the shell', async () => {
    writeToken('stored')
    const fetchMock = vi.fn(async () => projectsOk())
    vi.stubGlobal('fetch', fetchMock)

    render(<App />)

    expect(screen.getByText('Verificando sesión…')).toBeInTheDocument()
    expect(await screen.findByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/projects?status=active')
    expect(bearerOf(init)).toBe('Bearer stored')
  })

  it('goes back to login when the stored token is rejected on mount', async () => {
    writeToken('stored')
    vi.stubGlobal('fetch', vi.fn(async () => unauthorized()))

    render(<App />)

    expect(await screen.findByLabelText('API token')).toBeInTheDocument()
    expect(window.localStorage.getItem('lifeos.token')).toBeNull()
  })

  it('enters the shell when validation fails without a 401 (API down)', async () => {
    writeToken('stored')
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )

    render(<App />)

    expect(await screen.findByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(window.localStorage.getItem('lifeos.token')).toBe('stored')
  })

  it('logs out: clears the token and shows the login screen again', async () => {
    writeToken('stored')
    vi.stubGlobal('fetch', vi.fn(async () => projectsOk()))
    render(<App />)

    fireEvent.click(await screen.findByRole('button', { name: 'Salir' }))

    expect(window.localStorage.getItem('lifeos.token')).toBeNull()
    expect(screen.getByLabelText('API token')).toBeInTheDocument()
  })

  it('keeps the stored token untouched when a 401 comes from a different token', async () => {
    writeToken('stored')
    // Otra pestaña guardó un token nuevo mientras esta validaba el anterior.
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        window.localStorage.setItem('lifeos.token', 'newer')
        return unauthorized()
      }),
    )

    render(<App />)

    expect(await screen.findByLabelText('API token')).toBeInTheDocument()
    expect(window.localStorage.getItem('lifeos.token')).toBe('newer')
  })
})

describe('App across tabs', () => {
  it('goes back to login when another tab logs out', async () => {
    writeToken('stored')
    vi.stubGlobal('fetch', vi.fn(async () => projectsOk()))
    render(<App />)
    await screen.findByRole('button', { name: 'Salir' })

    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'lifeos.token', newValue: null }))
    })

    expect(screen.getByLabelText('API token')).toBeInTheDocument()
  })

  it('validates and follows the token when another tab logs in with a different one', async () => {
    writeToken('stored')
    const fetchMock = vi.fn(async () => projectsOk())
    vi.stubGlobal('fetch', fetchMock)
    render(<App />)
    await screen.findByRole('button', { name: 'Salir' })

    act(() => {
      window.dispatchEvent(new StorageEvent('storage', { key: 'lifeos.token', newValue: 'other' }))
    })

    expect(await screen.findByRole('button', { name: 'Salir' })).toBeInTheDocument()
    const last = fetchMock.mock.calls.at(-1) as unknown as [string, RequestInit]
    expect(bearerOf(last[1])).toBe('Bearer other')
  })
})

describe('ApiProvider', () => {
  it('calls onUnauthorized with the token that made the request', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => unauthorized()))
    const onUnauthorized = vi.fn()

    function Probe() {
      const api = useApi()
      useEffect(() => {
        api.listProjects().catch(() => undefined)
      }, [api])
      return null
    }

    render(
      <ApiProvider token="stored" onUnauthorized={onUnauthorized}>
        <Probe />
      </ApiProvider>,
    )

    await vi.waitFor(() => expect(onUnauthorized).toHaveBeenCalledWith('stored'))
  })
})
