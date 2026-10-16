import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ApiClient } from '../api/client'
import { ApiError } from '../api/client'
import type { Project, Task } from '../api/types'
import { ApiContext } from '../api/useApi'
import TaskBoard from './TaskBoard'

const PROJECT: Project = {
  id: 'p1',
  name: 'Casa',
  description: null,
  status: 'active',
  created_at: '2026-01-10T12:00:00Z',
}
const OTHER: Project = { ...PROJECT, id: 'p2', name: 'Viaje' }

function task(overrides: Partial<Task> & Pick<Task, 'id' | 'title'>): Task {
  return {
    project_id: 'p1',
    description: null,
    status: 'todo',
    priority: 'medium',
    due_date: null,
    created_at: '2026-03-01T10:00:00Z',
    ...overrides,
  }
}

const TASKS: Task[] = [
  task({ id: 't1', title: 'Baja sin fecha', priority: 'low' }),
  task({
    id: 't2',
    title: 'Alta tarde',
    priority: 'high',
    due_date: '2099-12-31',
  }),
  task({
    id: 't3',
    title: 'Alta pronto',
    priority: 'high',
    due_date: '2099-01-01',
  }),
  task({ id: 't4', title: 'Alta sin fecha', priority: 'high' }),
  task({
    id: 't5',
    title: 'En marcha',
    status: 'doing',
    due_date: '2020-01-01',
    description: 'Detalle de la tarea en curso',
  }),
  task({
    id: 't6',
    title: 'Terminada',
    status: 'done',
    due_date: '2020-01-01',
  }),
]

function createMockApi(initial: Task[] = TASKS, projects: Project[] = [PROJECT, OTHER]) {
  let store = initial.map((item) => ({ ...item }))
  const change = (id: string, changes: Partial<Task>) => {
    const index = store.findIndex((item) => item.id === id)
    store[index] = { ...store[index], ...changes }
    return store[index]
  }
  return {
    listProjectTasks: vi.fn(async (projectId: string) =>
      store.filter((item) => item.project_id === projectId),
    ),
    listProjects: vi.fn(async () => projects),
    startTask: vi.fn(async (id: string) => change(id, { status: 'doing' })),
    completeTask: vi.fn(async (id: string) => change(id, { status: 'done' })),
    reopenTask: vi.fn(async (id: string) => change(id, { status: 'todo' })),
    createTask: vi.fn(
      async (
        projectId: string,
        body: {
          title: string
          priority?: Task['priority']
          due_date?: string | null
        },
      ) => {
        const created = task({
          id: 'new1',
          title: body.title,
          project_id: projectId,
          priority: body.priority ?? 'medium',
          due_date: body.due_date ?? null,
        })
        store = [...store, created]
        return created
      },
    ),
    updateTask: vi.fn(async (id: string, body: Partial<Task>) => change(id, body)),
    moveTask: vi.fn(async (id: string, body: { project_id: string }) =>
      change(id, { project_id: body.project_id }),
    ),
    deleteTask: vi.fn(async (id: string) => {
      store = store.filter((item) => item.id !== id)
    }),
  }
}

type MockApi = ReturnType<typeof createMockApi>

function renderBoard(api: MockApi, project: Project = PROJECT) {
  return render(
    <ApiContext.Provider value={api as unknown as ApiClient}>
      <TaskBoard project={project} />
    </ApiContext.Provider>,
  )
}

function column(name: string): HTMLElement {
  return screen.getByRole('region', { name: new RegExp(name) })
}

function titlesIn(name: string): string[] {
  return within(column(name))
    .queryAllByRole('listitem')
    .map((item) => item.querySelector('.task-open')?.textContent ?? '')
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('TaskBoard columns', () => {
  it('groups tasks by status in three columns', async () => {
    renderBoard(createMockApi())

    await screen.findByText('En marcha')
    expect(titlesIn('Por hacer')).toHaveLength(4)
    expect(titlesIn('En curso')).toEqual(['En marcha'])
    expect(titlesIn('Hecho')).toEqual(['Terminada'])
  })

  it('sorts by priority, then due date (nulls last), then creation', async () => {
    const api = createMockApi([
      ...TASKS,
      task({
        id: 't7',
        title: 'Alta sin fecha, más nueva',
        priority: 'high',
        created_at: '2026-04-01T10:00:00Z',
      }),
    ])
    renderBoard(api)

    await screen.findByText('En marcha')
    expect(titlesIn('Por hacer')).toEqual([
      'Alta pronto',
      'Alta tarde',
      'Alta sin fecha',
      'Alta sin fecha, más nueva',
      'Baja sin fecha',
    ])
  })

  it('requests the tasks of the project', async () => {
    const api = createMockApi()
    renderBoard(api)

    await screen.findByText('En marcha')
    expect(api.listProjectTasks).toHaveBeenCalledWith('p1')
  })

  it('shows priority, due date, description preview and highlights overdue tasks', async () => {
    renderBoard(createMockApi())

    const card = (await screen.findByText('En marcha')).closest('li') as HTMLElement
    expect(within(card).getByText('Media')).toBeInTheDocument()
    expect(within(card).getByText('Detalle de la tarea en curso')).toBeInTheDocument()
    const due = within(card).getByText(/Vencida:/)
    expect(due).toHaveClass('overdue')
    expect(due).toHaveTextContent('2020')

    // Una tarea hecha con fecha pasada no se marca como vencida.
    const done = screen.getByText('Terminada').closest('li') as HTMLElement
    expect(within(done).queryByText(/Vencida:/)).not.toBeInTheDocument()
    expect(within(done).getByText(/Vence:/)).not.toHaveClass('overdue')
  })

  it('shows an error with a retry button when loading fails', async () => {
    const api = createMockApi()
    api.listProjectTasks.mockRejectedValueOnce(new ApiError(500, 'boom', 'Falló la carga'))
    renderBoard(api)

    expect(await screen.findByRole('alert')).toHaveTextContent('Falló la carga')
    fireEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('En marcha')).toBeInTheDocument()
  })

  it('reloads when the project changes and ignores stale responses', async () => {
    const api = createMockApi([...TASKS, task({ id: 'x1', title: 'De Viaje', project_id: 'p2' })])
    let release: (tasks: Task[]) => void = () => {}
    api.listProjectTasks.mockImplementationOnce(
      () => new Promise<Task[]>((resolve) => (release = resolve)),
    )
    const view = renderBoard(api)

    view.rerender(
      <ApiContext.Provider value={api as unknown as ApiClient}>
        <TaskBoard project={OTHER} />
      </ApiContext.Provider>,
    )
    expect(await screen.findByText('De Viaje')).toBeInTheDocument()

    release([task({ id: 'late', title: 'Respuesta vieja' })])
    await waitFor(() => expect(screen.queryByText('Respuesta vieja')).not.toBeInTheDocument())
    expect(screen.getByText('De Viaje')).toBeInTheDocument()
  })
})
