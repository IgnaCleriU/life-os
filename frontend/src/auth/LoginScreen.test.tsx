import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import LoginScreen from './LoginScreen'
import { clearToken, readToken } from './token'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
  clearToken()
  window.localStorage.clear()
})

async function submitToken(token: string) {
  fireEvent.change(screen.getByLabelText('API token'), { target: { value: token } })
  fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))
}

describe('LoginScreen', () => {
  it('uses a password input labelled "API token"', () => {
    render(<LoginScreen onLogin={vi.fn()} />)

    expect(screen.getByLabelText('API token')).toHaveAttribute('type', 'password')
  })

  it('validates the token with GET /projects, stores it and calls onLogin on success', async () => {
    const fetchMock = vi.fn(async () => jsonResponse(200, []))
    vi.stubGlobal('fetch', fetchMock)
    const onLogin = vi.fn()
    render(<LoginScreen onLogin={onLogin} />)

    await submitToken('good-token')

    await waitFor(() => expect(onLogin).toHaveBeenCalledWith('good-token'))
    expect(fetchMock).toHaveBeenCalledOnce()
    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit]
    expect(url).toBe('/projects')
    expect(new Headers(init.headers).get('Authorization')).toBe('Bearer good-token')
    expect(readToken()).toBe('good-token')
  })

  it('shows "Token inválido" on 401 and does not store the token', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(401, { error: { code: 'unauthorized', message: 'x' } })),
    )
    const onLogin = vi.fn()
    render(<LoginScreen onLogin={onLogin} />)

    await submitToken('bad-token')

    expect(await screen.findByRole('alert')).toHaveTextContent('Token inválido')
    expect(onLogin).not.toHaveBeenCalled()
    expect(readToken()).toBeNull()
  })

  it('explains LIFEOS_ALLOWED_HOSTS on 403', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(403, { error: { code: 'forbidden_host', message: 'x' } })),
    )
    const onLogin = vi.fn()
    render(<LoginScreen onLogin={onLogin} />)

    await submitToken('any-token')

    expect(await screen.findByRole('alert')).toHaveTextContent('LIFEOS_ALLOWED_HOSTS')
    expect(onLogin).not.toHaveBeenCalled()
    expect(readToken()).toBeNull()
  })

  it('shows a connection error when the network request fails', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    const onLogin = vi.fn()
    render(<LoginScreen onLogin={onLogin} />)

    await submitToken('any-token')

    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar con la API')
    expect(onLogin).not.toHaveBeenCalled()
  })

  it('does not call the API when the token is empty', async () => {
    const fetchMock = vi.fn()
    vi.stubGlobal('fetch', fetchMock)
    render(<LoginScreen onLogin={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Ingresá el token')
    expect(fetchMock).not.toHaveBeenCalled()
  })
})
