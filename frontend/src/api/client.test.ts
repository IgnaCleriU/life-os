import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, createApiClient } from './client'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

function mockFetch(response: Response | (() => Response)) {
  const fetchMock = vi.fn(async () => (typeof response === 'function' ? response() : response.clone()))
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}

function lastCall(fetchMock: ReturnType<typeof mockFetch>) {
  const call = fetchMock.mock.calls.at(-1) as unknown as [string, RequestInit]
  const [url, init] = call
  return { url, init, headers: new Headers(init.headers) }
}

const PROJECT = {
  id: '11111111-1111-1111-1111-111111111111',
  name: 'Casa',
  description: null,
  status: 'active',
  created_at: '2026-10-01T10:00:00Z',
}

const TASK = {
  id: '22222222-2222-2222-2222-222222222222',
  project_id: PROJECT.id,
  title: 'Comprar pan',
  description: null,
  status: 'todo',
  priority: 'medium',
  due_date: null,
  created_at: '2026-10-01T10:00:00Z',
}

const TOKEN = 'secret-token'

function client(onUnauthorized?: () => void) {
  return createApiClient({ getToken: () => TOKEN, onUnauthorized })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('api client: requests', () => {
  it('sends the bearer token and parses JSON for a GET', async () => {
    const fetchMock = mockFetch(jsonResponse(200, [PROJECT]))

    const projects = await client().listProjects()

    expect(projects).toEqual([PROJECT])
    const { url, init, headers } = lastCall(fetchMock)
    expect(url).toBe('/projects')
    expect(init.method).toBe('GET')
    expect(headers.get('Authorization')).toBe(`Bearer ${TOKEN}`)
    expect(init.body).toBeUndefined()
  })

  it('omits the Authorization header when there is no token', async () => {
    const fetchMock = mockFetch(jsonResponse(200, { status: 'ok' }))
    const api = createApiClient({ getToken: () => null })

    await api.listProjects()

    expect(lastCall(fetchMock).headers.has('Authorization')).toBe(false)
  })

  it('does not send the token to /health', async () => {
    const fetchMock = mockFetch(jsonResponse(200, { status: 'ok' }))

    const result = await client().health()

    expect(result).toEqual({ status: 'ok' })
    const { url, headers } = lastCall(fetchMock)
    expect(url).toBe('/health')
    expect(headers.has('Authorization')).toBe(false)
  })

  it('sends a JSON body with Content-Type for a POST', async () => {
    const fetchMock = mockFetch(jsonResponse(201, PROJECT))

    await client().createProject({ name: 'Casa', description: null })

    const { url, init, headers } = lastCall(fetchMock)
    expect(url).toBe('/projects')
    expect(init.method).toBe('POST')
    expect(headers.get('Content-Type')).toBe('application/json')
    expect(JSON.parse(init.body as string)).toEqual({ name: 'Casa', description: null })
  })

  it('uses PATCH for updates and keeps null to clear a field', async () => {
    const fetchMock = mockFetch(jsonResponse(200, TASK))

    await client().updateTask(TASK.id, { due_date: null, title: 'Comprar pan y leche' })

    const { url, init } = lastCall(fetchMock)
    expect(url).toBe(`/tasks/${TASK.id}`)
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body as string)).toEqual({ due_date: null, title: 'Comprar pan y leche' })
  })

  it('builds the state transition routes as POST without a body', async () => {
    const fetchMock = mockFetch(jsonResponse(200, TASK))
    const api = client()

    await api.completeTask(TASK.id)
    expect(lastCall(fetchMock).url).toBe(`/tasks/${TASK.id}/complete`)
    expect(lastCall(fetchMock).init.method).toBe('POST')
    expect(lastCall(fetchMock).init.body).toBeUndefined()

    await api.startTask(TASK.id)
    expect(lastCall(fetchMock).url).toBe(`/tasks/${TASK.id}/start`)

    await api.reopenTask(TASK.id)
    expect(lastCall(fetchMock).url).toBe(`/tasks/${TASK.id}/reopen`)

    await api.restoreTask(TASK.id)
    expect(lastCall(fetchMock).url).toBe(`/tasks/${TASK.id}/restore`)
  })

  it('builds the project transition routes', async () => {
    const fetchMock = mockFetch(jsonResponse(200, PROJECT))
    const api = client()

    await api.completeProject(PROJECT.id)
    expect(lastCall(fetchMock).url).toBe(`/projects/${PROJECT.id}/complete`)

    await api.archiveProject(PROJECT.id)
    expect(lastCall(fetchMock).url).toBe(`/projects/${PROJECT.id}/archive`)

    await api.activateProject(PROJECT.id)
    expect(lastCall(fetchMock).url).toBe(`/projects/${PROJECT.id}/activate`)

    await api.restoreProject(PROJECT.id)
    expect(lastCall(fetchMock).url).toBe(`/projects/${PROJECT.id}/restore`)
  })

  it('posts the move body with project_id', async () => {
    const fetchMock = mockFetch(jsonResponse(200, TASK))
    const target = '33333333-3333-3333-3333-333333333333'

    await client().moveTask(TASK.id, { project_id: target })

    const { url, init } = lastCall(fetchMock)
    expect(url).toBe(`/tasks/${TASK.id}/move`)
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({ project_id: target })
  })

  it('creates a task under its project', async () => {
    const fetchMock = mockFetch(jsonResponse(201, TASK))

    await client().createTask(PROJECT.id, { title: 'Comprar pan', priority: 'high', due_date: '2026-10-20' })

    const { url, init } = lastCall(fetchMock)
    expect(url).toBe(`/projects/${PROJECT.id}/tasks`)
    expect(init.method).toBe('POST')
    expect(JSON.parse(init.body as string)).toEqual({
      title: 'Comprar pan',
      priority: 'high',
      due_date: '2026-10-20',
    })
  })

  it('encodes ids in the path', async () => {
    const fetchMock = mockFetch(jsonResponse(200, PROJECT))

    await client().getProject('a/b c')

    expect(lastCall(fetchMock).url).toBe('/projects/a%2Fb%20c')
  })
})

describe('api client: query strings', () => {
  it('repeats multi-value filters as separate params', async () => {
    const fetchMock = mockFetch(jsonResponse(200, []))

    await client().listTasks({ status: ['todo', 'doing'], due_before: '2026-10-31', q: 'pan' })

    const url = new URL(lastCall(fetchMock).url, 'http://localhost')
    expect(url.pathname).toBe('/tasks')
    expect(url.searchParams.getAll('status')).toEqual(['todo', 'doing'])
    expect(url.searchParams.get('due_before')).toBe('2026-10-31')
    expect(url.searchParams.get('q')).toBe('pan')
  })

  it('accepts a single status value', async () => {
    const fetchMock = mockFetch(jsonResponse(200, []))

    await client().listProjects({ status: 'archived' })

    expect(lastCall(fetchMock).url).toBe('/projects?status=archived')
  })

  it('omits undefined filters and produces no query string when empty', async () => {
    const fetchMock = mockFetch(jsonResponse(200, []))
    const api = client()

    await api.listProjects()
    expect(lastCall(fetchMock).url).toBe('/projects')

    await api.listProjects({ status: undefined, q: undefined })
    expect(lastCall(fetchMock).url).toBe('/projects')
  })

  it('lists a project tasks with filters on the project route', async () => {
    const fetchMock = mockFetch(jsonResponse(200, [TASK]))

    await client().listProjectTasks(PROJECT.id, { status: ['done'], q: 'pan' })

    const url = new URL(lastCall(fetchMock).url, 'http://localhost')
    expect(url.pathname).toBe(`/projects/${PROJECT.id}/tasks`)
    expect(url.searchParams.getAll('status')).toEqual(['done'])
    expect(url.searchParams.get('q')).toBe('pan')
    expect(url.searchParams.has('project_id')).toBe(false)
  })

  it('passes project_id to the global task listing', async () => {
    const fetchMock = mockFetch(jsonResponse(200, []))

    await client().listTasks({ project_id: PROJECT.id })

    expect(lastCall(fetchMock).url).toBe(`/tasks?project_id=${PROJECT.id}`)
  })
})

describe('api client: responses and errors', () => {
  it('handles 204 as void', async () => {
    mockFetch(new Response(null, { status: 204 }))

    await expect(client().deleteProject(PROJECT.id)).resolves.toBeUndefined()
  })

  it('throws ApiError with status, code and message from the error body', async () => {
    mockFetch(
      jsonResponse(404, { error: { code: 'project_not_found', message: 'No existe el proyecto' } }),
    )

    const error = await client()
      .getProject(PROJECT.id)
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 404,
      code: 'project_not_found',
      message: 'No existe el proyecto',
    })
  })

  it('falls back to an http_<status> code when the error body is not JSON', async () => {
    mockFetch(new Response('<html>Bad gateway</html>', { status: 502, statusText: 'Bad Gateway' }))

    const error = await client()
      .listProjects()
      .catch((e: unknown) => e)

    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 502, code: 'http_502', message: 'Bad Gateway' })
  })

  it('calls onUnauthorized on 401 and still throws', async () => {
    mockFetch(jsonResponse(401, { error: { code: 'unauthorized', message: 'Missing or invalid bearer token.' } }))
    const onUnauthorized = vi.fn()

    await expect(client(onUnauthorized).listProjects()).rejects.toMatchObject({
      status: 401,
      code: 'unauthorized',
    })
    expect(onUnauthorized).toHaveBeenCalledOnce()
  })

  it('does not call onUnauthorized for other errors', async () => {
    mockFetch(jsonResponse(403, { error: { code: 'forbidden_host', message: 'Host no permitido' } }))
    const onUnauthorized = vi.fn()

    await expect(client(onUnauthorized).listProjects()).rejects.toMatchObject({ code: 'forbidden_host' })
    expect(onUnauthorized).not.toHaveBeenCalled()
  })

  it('does not call onUnauthorized when /health answers 401', async () => {
    mockFetch(jsonResponse(401, { error: { code: 'unauthorized', message: 'x' } }))
    const onUnauthorized = vi.fn()

    await expect(client(onUnauthorized).health()).rejects.toBeInstanceOf(ApiError)
    expect(onUnauthorized).not.toHaveBeenCalled()
  })
})
