import { fireEvent, render, screen } from '@testing-library/react'
import { useEffect } from 'react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import App from './App'
import { ApiProvider } from './api/ApiContext'
import { useApi } from './api/useApi'
import { clearToken, writeToken } from './auth/token'

afterEach(() => {
  vi.unstubAllGlobals()
  clearToken()
  window.localStorage.clear()
})

describe('App', () => {
  it('shows the login screen when there is no token', () => {
    render(<App />)

    expect(screen.getByLabelText('API token')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Salir' })).not.toBeInTheDocument()
  })

  it('shows the shell with a logout button when a token is stored', () => {
    writeToken('stored')
    render(<App />)

    expect(screen.getByRole('heading', { name: 'Life OS' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(screen.queryByLabelText('API token')).not.toBeInTheDocument()
  })

  it('logs out: clears the token and shows the login screen again', () => {
    writeToken('stored')
    render(<App />)

    fireEvent.click(screen.getByRole('button', { name: 'Salir' }))

    expect(window.localStorage.getItem('lifeos.token')).toBeNull()
    expect(screen.getByLabelText('API token')).toBeInTheDocument()
  })

  it('logs in through the login screen and shows the shell', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response('[]', { status: 200 })))
    render(<App />)

    fireEvent.change(screen.getByLabelText('API token'), { target: { value: 'fresh' } })
    fireEvent.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('button', { name: 'Salir' })).toBeInTheDocument()
    expect(window.localStorage.getItem('lifeos.token')).toBe('fresh')
  })
})

describe('ApiProvider', () => {
  it('calls onUnauthorized when an authenticated call answers 401', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () =>
        new Response(JSON.stringify({ error: { code: 'unauthorized', message: 'x' } }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        }),
      ),
    )
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

    await vi.waitFor(() => expect(onUnauthorized).toHaveBeenCalledOnce())
  })
})
