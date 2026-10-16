import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ApiClient } from '../api/client'
import { ApiError } from '../api/client'
import type { Project, ProjectFilter } from '../api/types'
import { ApiContext } from '../api/useApi'
import ProjectsPage from './ProjectsPage'

const CASA: Project = {
  id: 'p1',
  name: 'Casa',
  description: 'Reformas',
  status: 'active',
  created_at: '2026-01-10T12:00:00Z',
}
const VIAJE: Project = {
  id: 'p2',
  name: 'Viaje',
  description: null,
  status: 'completed',
  created_at: '2026-02-03T12:00:00Z',
}

/** Simula GET /projects con el filtro de estado (string o lista). */
function listFrom(store: Project[], filter: ProjectFilter = {}): Project[] {
  const { status } = filter
  const wanted = status === undefined ? null : typeof status === 'string' ? [status] : status
  return store.filter((project) => wanted === null || wanted.includes(project.status))
}

/** Cambia un proyecto del almacén simulado y devuelve la versión nueva. */
function patchStore(store: Project[], id: string, changes: Partial<Project>): Project {
  const index = store.findIndex((project) => project.id === id)
  if (index === -1) throw new ApiError(404, 'not_found', 'Proyecto no encontrado')
  const updated = { ...store[index], ...changes }
  store[index] = updated
  return updated
}

function createMockApi(store: Project[]) {
  return {
    listProjectTasks: vi.fn(async () => []),
    listProjects: vi.fn(async (filter?: ProjectFilter) => listFrom(store, filter)),
    updateProject: vi.fn(async (id: string, body: { name?: string; description?: string | null }) =>
      patchStore(store, id, body),
    ),
    archiveProject: vi.fn(async (id: string) => patchStore(store, id, { status: 'archived' })),
    getProject: vi.fn(async (id: string) => {
      const found = store.find((project) => project.id === id)
      if (!found) throw new ApiError(404, 'not_found', 'Proyecto no encontrado')
      return found
    }),
    createProject: vi.fn(async (body: { name: string; description?: string | null }) => {
      const created: Project = {
        id: 'new1',
        name: body.name,
        description: body.description ?? null,
        status: 'active',
        created_at: '2026-10-01T10:00:00Z',
      }
      store.push(created)
      return created
    }),
  }
}

function renderPage(api: ReturnType<typeof createMockApi>) {
  return render(
    <ApiContext.Provider value={api as unknown as ApiClient}>
      <ProjectsPage />
    </ApiContext.Provider>,
  )
}

afterEach(() => {
  window.history.replaceState(null, '', '/')
})

describe('ProjectsPage list', () => {
  it('lists the active projects by default', async () => {
    const api = createMockApi([CASA, VIAJE])
    renderPage(api)

    expect(await screen.findByRole('button', { name: 'Casa' })).toBeInTheDocument()
    expect(api.listProjects).toHaveBeenCalledWith({ status: 'active' })
    expect(screen.queryByRole('button', { name: 'Viaje' })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Estado')).toHaveValue('active')
  })

  it('changing the status filter requests that status', async () => {
    const api = createMockApi([CASA, VIAJE])
    renderPage(api)
    await screen.findByRole('button', { name: 'Casa' })

    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'completed' } })

    expect(await screen.findByRole('button', { name: 'Viaje' })).toBeInTheDocument()
    expect(api.listProjects).toHaveBeenLastCalledWith({ status: 'completed' })
    expect(screen.queryByRole('button', { name: 'Casa' })).not.toBeInTheDocument()
  })

  it('"Todos" requests the three statuses explicitly', async () => {
    const api = createMockApi([CASA, VIAJE])
    renderPage(api)
    await screen.findByRole('button', { name: 'Casa' })

    fireEvent.change(screen.getByLabelText('Estado'), { target: { value: 'all' } })

    expect(await screen.findByRole('button', { name: 'Viaje' })).toBeInTheDocument()
    expect(api.listProjects).toHaveBeenLastCalledWith({
      status: ['active', 'completed', 'archived'],
    })
  })

  it('shows the API error with a retry button that reloads the list', async () => {
    const api = createMockApi([CASA])
    api.listProjects
      .mockRejectedValueOnce(new ApiError(500, 'internal_error', 'La base no responde'))
      .mockImplementation(async (filter?: ProjectFilter) => listFrom([CASA], filter))
    renderPage(api)

    expect(await screen.findByRole('alert')).toHaveTextContent('La base no responde')
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByRole('button', { name: 'Casa' })).toBeInTheDocument()
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(api.listProjects).toHaveBeenCalledTimes(2)
  })
})

describe('ProjectsPage selection', () => {
  it('selecting a project marks it as current and shows its detail', async () => {
    renderPage(createMockApi([CASA]))

    fireEvent.click(await screen.findByRole('button', { name: 'Casa' }))

    expect(screen.getByRole('button', { name: 'Casa' })).toHaveAttribute('aria-current', 'true')
    expect(screen.getByRole('heading', { level: 2, name: 'Casa' })).toBeInTheDocument()
    expect(screen.getByText('Reformas')).toBeInTheDocument()
    expect(window.location.hash).toBe('#/projects/p1')
  })

  it('restores the selection from the URL hash on load', async () => {
    window.history.replaceState(null, '', '#/projects/p1')
    const api = createMockApi([CASA, VIAJE])
    renderPage(api)

    expect(await screen.findByRole('heading', { level: 2, name: 'Casa' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Casa' })).toHaveAttribute('aria-current', 'true')
    expect(window.location.hash).toBe('#/projects/p1')
  })

  it('keeps a hash selection that is outside the current filter', async () => {
    window.history.replaceState(null, '', '#/projects/p2')
    const api = createMockApi([CASA, VIAJE])
    renderPage(api)

    expect(await screen.findByRole('heading', { level: 2, name: 'Viaje' })).toBeInTheDocument()
    expect(api.getProject).toHaveBeenCalledWith('p2')
    expect(screen.queryByRole('button', { name: 'Viaje' })).not.toBeInTheDocument()
    expect(window.location.hash).toBe('#/projects/p2')
  })

  it('keeps a hash selection when loading it fails and offers a retry', async () => {
    window.history.replaceState(null, '', '#/projects/p2')
    const api = createMockApi([CASA, VIAJE])
    api.getProject.mockRejectedValueOnce(new ApiError(500, 'internal_error', 'Servidor caído'))
    renderPage(api)

    expect(await screen.findByRole('alert')).toHaveTextContent('Servidor caído')
    expect(window.location.hash).toBe('#/projects/p2')

    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))

    expect(await screen.findByRole('heading', { level: 2, name: 'Viaje' })).toBeInTheDocument()
    expect(api.getProject).toHaveBeenCalledTimes(2)
  })

  it('drops a hash selection whose project no longer exists', async () => {
    window.history.replaceState(null, '', '#/projects/gone')
    renderPage(createMockApi([CASA]))

    expect(await screen.findByText('Elegí un proyecto de la lista.')).toBeInTheDocument()
    expect(window.location.hash).toBe('')
  })

  it('renders the task board in the detail', async () => {
    renderPage(createMockApi([CASA]))

    fireEvent.click(await screen.findByRole('button', { name: 'Casa' }))

    const board = screen.getByRole('region', { name: 'Tablero' })
    expect(await within(board).findByRole('region', { name: /Por hacer/ })).toBeInTheDocument()
  })
})

describe('ProjectsPage after an action', () => {
  it('keeps the selection when the project still matches the filter', async () => {
    const store = [{ ...CASA }]
    const api = createMockApi(store)
    renderPage(api)
    fireEvent.click(await screen.findByRole('button', { name: 'Casa' }))

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Nombre', { selector: '#edit-project-name' }), {
      target: { value: 'Casa 2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByRole('button', { name: 'Casa 2' })).toHaveAttribute(
      'aria-current',
      'true',
    )
    expect(screen.getByRole('heading', { level: 2, name: 'Casa 2' })).toBeInTheDocument()
    expect(window.location.hash).toBe('#/projects/p1')
  })

  it('shows the updated project from the action response before the list reloads', async () => {
    const store = [{ ...CASA }]
    const api = createMockApi(store)
    renderPage(api)
    fireEvent.click(await screen.findByRole('button', { name: 'Casa' }))
    // Las recargas de la lista quedan colgadas: lo que se ve debe venir de la respuesta de PATCH.
    api.listProjects.mockImplementation(() => new Promise<Project[]>(() => undefined))

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Nombre', { selector: '#edit-project-name' }), {
      target: { value: 'Casa 2' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(await screen.findByRole('heading', { level: 2, name: 'Casa 2' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Casa 2' })).toHaveAttribute('aria-current', 'true')
  })

  it('removes the project from the list and clears the selection when it leaves the filter', async () => {
    const store = [{ ...CASA }]
    const api = createMockApi(store)
    renderPage(api)
    fireEvent.click(await screen.findByRole('button', { name: 'Casa' }))

    fireEvent.click(screen.getByRole('button', { name: 'Archivar' }))

    await waitFor(() =>
      expect(screen.queryByRole('button', { name: 'Casa' })).not.toBeInTheDocument(),
    )
    expect(api.archiveProject).toHaveBeenCalledWith('p1')
    expect(screen.getByText('Elegí un proyecto de la lista.')).toBeInTheDocument()
    expect(window.location.hash).toBe('')
    expect(screen.getByRole('heading', { name: 'Proyectos' })).toHaveFocus()
  })
})

describe('ProjectsPage create', () => {
  it('creates a project and selects it', async () => {
    const api = createMockApi([CASA])
    renderPage(api)
    await screen.findByRole('button', { name: 'Casa' })

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: '  Huerta  ' } })
    fireEvent.change(screen.getByLabelText('Descripción (opcional)'), {
      target: { value: 'Tomates' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Crear proyecto' }))

    expect(api.createProject).toHaveBeenCalledWith({ name: 'Huerta', description: 'Tomates' })
    expect(await screen.findByRole('heading', { level: 2, name: 'Huerta' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Huerta' })).toHaveAttribute('aria-current', 'true')
    expect(window.location.hash).toBe('#/projects/new1')
  })

  it('sends a null description when it is left empty', async () => {
    const api = createMockApi([])
    renderPage(api)
    await screen.findByText('No hay proyectos en este estado.')

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: 'Solo nombre' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear proyecto' }))

    await waitFor(() =>
      expect(api.createProject).toHaveBeenCalledWith({ name: 'Solo nombre', description: null }),
    )
  })

  it('requires a name before calling the API', async () => {
    const api = createMockApi([CASA])
    renderPage(api)
    await screen.findByRole('button', { name: 'Casa' })

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: '   ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Crear proyecto' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Ingresá un nombre')
    expect(api.createProject).not.toHaveBeenCalled()
  })
})
