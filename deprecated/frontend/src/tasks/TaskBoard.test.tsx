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

function card(title: string): HTMLElement {
  return screen.getByText(title).closest('li') as HTMLElement
}

function dataTransfer() {
  const data: Record<string, string> = {}
  return {
    setData: (type: string, value: string) => {
      data[type] = value
    },
    getData: (type: string) => data[type] ?? '',
    get types() {
      return Object.keys(data)
    },
    effectAllowed: 'all',
    dropEffect: 'none',
  }
}

describe('TaskBoard moves', () => {
  it('offers every other column and no move to the current one', async () => {
    renderBoard(createMockApi())
    await screen.findByText('En marcha')

    const todo = within(card('Baja sin fecha'))
    expect(todo.getByRole('button', { name: 'Mover a En curso' })).toBeInTheDocument()
    expect(todo.getByRole('button', { name: 'Mover a Hecho' })).toBeInTheDocument()
    expect(todo.queryByRole('button', { name: 'Mover a Por hacer' })).not.toBeInTheDocument()

    const done = within(card('Terminada'))
    expect(done.getByRole('button', { name: 'Mover a En curso' })).toBeInTheDocument()
    expect(done.getByRole('button', { name: 'Mover a Por hacer' })).toBeInTheDocument()
    expect(done.queryByRole('button', { name: 'Mover a Hecho' })).not.toBeInTheDocument()
  })

  it.each([
    ['Baja sin fecha', 'Mover a En curso', 'startTask', 'En curso'],
    ['Baja sin fecha', 'Mover a Hecho', 'completeTask', 'Hecho'],
    ['Terminada', 'Mover a Por hacer', 'reopenTask', 'Por hacer'],
    ['Terminada', 'Mover a En curso', 'startTask', 'En curso'],
  ] as const)('%s: "%s" calls %s', async (title, label, method, columnName) => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')

    fireEvent.click(within(card(title)).getByRole('button', { name: label }))

    await waitFor(() => expect(titlesIn(columnName)).toContain(title))
    const id = TASKS.find((item) => item.title === title)?.id
    expect(api[method]).toHaveBeenCalledWith(id)
  })

  it('rolls back and shows an error when the move fails', async () => {
    const api = createMockApi()
    api.startTask.mockRejectedValueOnce(new ApiError(500, 'boom', 'No anduvo'))
    renderBoard(api)
    await screen.findByText('En marcha')

    fireEvent.click(
      within(card('Baja sin fecha')).getByRole('button', { name: 'Mover a En curso' }),
    )

    expect(await screen.findByRole('alert')).toHaveTextContent('No anduvo')
    expect(titlesIn('Por hacer')).toContain('Baja sin fecha')
    expect(titlesIn('En curso')).toEqual(['En marcha'])
  })

  it('moves a card by drag and drop', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const transfer = dataTransfer()

    fireEvent.dragStart(card('Baja sin fecha'), { dataTransfer: transfer })
    fireEvent.dragOver(column('Hecho'), { dataTransfer: transfer })
    expect(column('Hecho')).toHaveClass('drop-target')
    fireEvent.drop(column('Hecho'), { dataTransfer: transfer })

    await waitFor(() => expect(titlesIn('Hecho')).toContain('Baja sin fecha'))
    expect(api.completeTask).toHaveBeenCalledWith('t1')
    expect(column('Hecho')).not.toHaveClass('drop-target')
  })

  it('dropping on the same column does nothing', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const transfer = dataTransfer()

    fireEvent.dragStart(card('En marcha'), { dataTransfer: transfer })
    fireEvent.drop(column('En curso'), { dataTransfer: transfer })

    expect(api.startTask).not.toHaveBeenCalled()
  })
})

describe('TaskBoard quick create', () => {
  it('creates a task in "Por hacer" with priority and due date', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')

    const form = within(screen.getByRole('form', { name: 'Nueva tarea' }))
    fireEvent.change(form.getByLabelText('Título de la nueva tarea'), {
      target: { value: '  Comprar pintura  ' },
    })
    fireEvent.change(form.getByLabelText('Prioridad'), { target: { value: 'high' } })
    fireEvent.change(form.getByLabelText('Vencimiento'), { target: { value: '2099-05-01' } })
    fireEvent.click(form.getByRole('button', { name: 'Agregar tarea' }))

    await waitFor(() => expect(titlesIn('Por hacer')).toContain('Comprar pintura'))
    expect(api.createTask).toHaveBeenCalledWith('p1', {
      title: 'Comprar pintura',
      priority: 'high',
      due_date: '2099-05-01',
    })
    expect(form.getByLabelText('Título de la nueva tarea')).toHaveValue('')
  })

  it('sends a null due date when none is chosen and rejects empty titles', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const form = within(screen.getByRole('form', { name: 'Nueva tarea' }))

    fireEvent.click(form.getByRole('button', { name: 'Agregar tarea' }))
    expect(await form.findByRole('alert')).toHaveTextContent('Ingresá un título')
    expect(api.createTask).not.toHaveBeenCalled()

    fireEvent.change(form.getByLabelText('Título de la nueva tarea'), { target: { value: 'X' } })
    fireEvent.click(form.getByRole('button', { name: 'Agregar tarea' }))
    await waitFor(() =>
      expect(api.createTask).toHaveBeenCalledWith('p1', {
        title: 'X',
        priority: 'medium',
        due_date: null,
      }),
    )
  })

  it('shows the API error and keeps the typed title', async () => {
    const api = createMockApi()
    api.createTask.mockRejectedValueOnce(new ApiError(404, 'not_found', 'Proyecto no encontrado'))
    renderBoard(api)
    await screen.findByText('En marcha')
    const form = within(screen.getByRole('form', { name: 'Nueva tarea' }))

    fireEvent.change(form.getByLabelText('Título de la nueva tarea'), { target: { value: 'Y' } })
    fireEvent.click(form.getByRole('button', { name: 'Agregar tarea' }))

    expect(await form.findByRole('alert')).toHaveTextContent('Proyecto no encontrado')
    expect(form.getByLabelText('Título de la nueva tarea')).toHaveValue('Y')
  })

  it('is available on completed projects too (the domain does not forbid it)', async () => {
    renderBoard(createMockApi(), { ...PROJECT, status: 'completed' })
    await screen.findByText('En marcha')

    expect(screen.getByRole('button', { name: 'Agregar tarea' })).toBeEnabled()
  })
})

async function openEditor(title: string) {
  fireEvent.click(within(card(title)).getByRole('button', { name: title }))
  return within(await screen.findByRole('dialog', { name: 'Editar tarea' }))
}

describe('TaskBoard editor', () => {
  it('opens a dialog with the task data', async () => {
    renderBoard(createMockApi())
    await screen.findByText('En marcha')

    const dialog = await openEditor('En marcha')

    expect(dialog.getByLabelText('Título')).toHaveValue('En marcha')
    expect(dialog.getByLabelText('Descripción')).toHaveValue('Detalle de la tarea en curso')
    expect(dialog.getByLabelText('Prioridad')).toHaveValue('medium')
    expect(dialog.getByLabelText('Vencimiento')).toHaveValue('2020-01-01')
  })

  it('sends only the changed fields', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.change(dialog.getByLabelText('Título'), { target: { value: 'Renombrada' } })
    fireEvent.change(dialog.getByLabelText('Prioridad'), { target: { value: 'high' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))

    await waitFor(() =>
      expect(api.updateTask).toHaveBeenCalledWith('t5', { title: 'Renombrada', priority: 'high' }),
    )
    expect(await screen.findByText('Renombrada')).toBeInTheDocument()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('clears the due date and the description with null', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.click(dialog.getByRole('button', { name: 'Quitar fecha' }))
    fireEvent.change(dialog.getByLabelText('Descripción'), { target: { value: '  ' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))

    await waitFor(() =>
      expect(api.updateTask).toHaveBeenCalledWith('t5', { description: null, due_date: null }),
    )
  })

  it('does not call the API when nothing changed', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))

    expect(api.updateTask).not.toHaveBeenCalled()
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('shows save errors inside the dialog', async () => {
    const api = createMockApi()
    api.updateTask.mockRejectedValueOnce(new ApiError(400, 'validation', 'Título inválido'))
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.change(dialog.getByLabelText('Título'), { target: { value: 'Otro' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))

    expect(await dialog.findByRole('alert')).toHaveTextContent('Título inválido')
    expect(screen.getByRole('dialog')).toBeInTheDocument()
  })

  it('moves the task to another active project', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    await waitFor(() => expect(api.listProjects).toHaveBeenCalledWith({ status: 'active' }))
    const select = await dialog.findByLabelText('Mover a proyecto')
    // Solo se ofrecen los otros proyectos activos.
    expect(within(select).queryByRole('option', { name: 'Casa' })).not.toBeInTheDocument()
    fireEvent.change(select, { target: { value: 'p2' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Mover' }))

    await waitFor(() => expect(api.moveTask).toHaveBeenCalledWith('t5', { project_id: 'p2' }))
    await waitFor(() => expect(screen.queryByText('En marcha')).not.toBeInTheDocument())
  })

  it('deletes after confirmation', async () => {
    const api = createMockApi()
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.click(dialog.getByRole('button', { name: 'Eliminar' }))

    await waitFor(() => expect(api.deleteTask).toHaveBeenCalledWith('t5'))
    expect(confirm).toHaveBeenCalled()
    await waitFor(() => expect(screen.queryByText('En marcha')).not.toBeInTheDocument())
  })

  it('does not delete when the confirmation is declined', async () => {
    const api = createMockApi()
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.click(dialog.getByRole('button', { name: 'Eliminar' }))

    expect(api.deleteTask).not.toHaveBeenCalled()
    expect(screen.getByText('En marcha')).toBeInTheDocument()
  })

  it('keeps the dialog open on Escape while saving, so the error is visible', async () => {
    const api = createMockApi()
    let fail: (error: Error) => void = () => {}
    api.updateTask.mockImplementationOnce(() => new Promise<Task>((_, reject) => (fail = reject)))
    renderBoard(api)
    await screen.findByText('En marcha')
    const dialog = await openEditor('En marcha')

    fireEvent.change(dialog.getByLabelText('Título'), { target: { value: 'Otro' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))
    const cancel = new Event('cancel', { cancelable: true })
    screen.getByRole('dialog').dispatchEvent(cancel)

    expect(cancel.defaultPrevented).toBe(true)
    fail(new ApiError(500, 'boom', 'Se cayó'))
    expect(await dialog.findByRole('alert')).toHaveTextContent('Se cayó')

    // Con el guardado terminado, Escape sí cierra.
    screen.getByRole('dialog').dispatchEvent(new Event('cancel', { cancelable: true }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
  })

  it('returns focus to the card that opened the dialog', async () => {
    renderBoard(createMockApi())
    await screen.findByText('En marcha')
    const opener = within(card('En marcha')).getByRole('button', { name: 'En marcha' })
    opener.focus()
    const dialog = await openEditor('En marcha')

    fireEvent.click(dialog.getByRole('button', { name: 'Cancelar' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(opener).toHaveFocus()
  })

  it('does not resend an unchanged description that has trailing spaces', async () => {
    const api = createMockApi([task({ id: 'd1', title: 'Con espacio', description: 'Texto  ' })])
    renderBoard(api)
    await screen.findByText('Con espacio')
    const dialog = await openEditor('Con espacio')

    fireEvent.change(dialog.getByLabelText('Título'), { target: { value: 'Nuevo' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(api.updateTask).toHaveBeenCalledWith('d1', { title: 'Nuevo' }))
  })
})

describe('TaskBoard robustness', () => {
  const T1 = (status: Task['status'], title = 'Baja sin fecha') =>
    task({ id: 't1', title, priority: 'low', status })

  function clickMove(title: string, label: string) {
    fireEvent.click(within(card(title)).getByRole('button', { name: label }))
  }

  it('serializes overlapping moves of one card and ends on the last target', async () => {
    const api = createMockApi()
    const first = deferred<Task>()
    const second = deferred<Task>()
    api.startTask.mockImplementationOnce(() => first.promise)
    api.completeTask.mockImplementationOnce(() => second.promise)
    renderBoard(api)
    await screen.findByText('En marcha')

    clickMove('Baja sin fecha', 'Mover a En curso')
    clickMove('Baja sin fecha', 'Mover a Hecho')
    expect(titlesIn('Hecho')).toContain('Baja sin fecha')
    // La segunda petición espera a que la primera termine.
    expect(api.completeTask).not.toHaveBeenCalled()

    first.resolve(T1('doing'))
    await waitFor(() => expect(api.completeTask).toHaveBeenCalledWith('t1'))
    expect(titlesIn('Hecho')).toContain('Baja sin fecha')
    second.resolve(T1('done'))
    await waitFor(() => expect(api.completeTask).toHaveBeenCalledTimes(1))
    expect(titlesIn('Hecho')).toContain('Baja sin fecha')
  })

  it('a failed last move falls back to the last server-confirmed status', async () => {
    const api = createMockApi()
    const first = deferred<Task>()
    const second = deferred<Task>()
    api.startTask.mockImplementationOnce(() => first.promise)
    api.completeTask.mockImplementationOnce(() => second.promise)
    renderBoard(api)
    await screen.findByText('En marcha')

    clickMove('Baja sin fecha', 'Mover a En curso')
    clickMove('Baja sin fecha', 'Mover a Hecho')
    first.resolve(T1('doing'))
    await waitFor(() => expect(api.completeTask).toHaveBeenCalled())
    second.reject(new ApiError(500, 'boom', 'Falló'))

    expect(await screen.findByRole('alert')).toHaveTextContent('Falló')
    await waitFor(() => expect(titlesIn('En curso')).toContain('Baja sin fecha'))
    expect(titlesIn('Hecho')).not.toContain('Baja sin fecha')
  })

  it('a failed first move does not stop the next one', async () => {
    const api = createMockApi()
    const first = deferred<Task>()
    api.startTask.mockImplementationOnce(() => first.promise)
    renderBoard(api)
    await screen.findByText('En marcha')

    clickMove('Baja sin fecha', 'Mover a En curso')
    clickMove('Baja sin fecha', 'Mover a Hecho')
    first.reject(new ApiError(500, 'boom', 'Falló'))

    await waitFor(() => expect(api.completeTask).toHaveBeenCalledWith('t1'))
    await waitFor(() => expect(titlesIn('Hecho')).toContain('Baja sin fecha'))
  })

  it('a move response only contributes the status, not a stale title', async () => {
    const api = createMockApi()
    const move = deferred<Task>()
    api.startTask.mockImplementationOnce(() => move.promise)
    renderBoard(api)
    await screen.findByText('En marcha')

    clickMove('Baja sin fecha', 'Mover a En curso')
    const dialog = await openEditor('Baja sin fecha')
    fireEvent.change(dialog.getByLabelText('Título'), { target: { value: 'Renombrada' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument())
    expect(titlesIn('En curso')).toContain('Renombrada')

    move.resolve(T1('doing', 'Baja sin fecha'))
    await waitFor(() => expect(api.startTask).toHaveBeenCalled())
    await Promise.resolve()
    await waitFor(() => expect(titlesIn('En curso')).toContain('Renombrada'))
    expect(screen.queryByText('Baja sin fecha')).not.toBeInTheDocument()
  })

  it('a save response never changes the status, even if the move finished meanwhile', async () => {
    const api = createMockApi()
    const save = deferred<Task>()
    api.updateTask.mockImplementationOnce(() => save.promise)
    renderBoard(api)
    await screen.findByText('En marcha')

    const dialog = await openEditor('Baja sin fecha')
    fireEvent.change(dialog.getByLabelText('Título'), { target: { value: 'Renombrada' } })
    fireEvent.click(dialog.getByRole('button', { name: 'Guardar' }))
    await waitFor(() => expect(api.updateTask).toHaveBeenCalled())

    // El movimiento se confirma mientras el PATCH sigue en vuelo.
    clickMove('Baja sin fecha', 'Mover a En curso')
    await waitFor(() => expect(api.startTask).toHaveBeenCalled())
    await waitFor(() => expect(titlesIn('En curso')).toContain('Baja sin fecha'))

    save.resolve(T1('todo', 'Renombrada'))
    await waitFor(() => expect(titlesIn('En curso')).toContain('Renombrada'))
    expect(titlesIn('Por hacer')).not.toContain('Renombrada')
  })

  it('ignores drags that do not carry a task', async () => {
    const api = createMockApi()
    renderBoard(api)
    await screen.findByText('En marcha')
    const foreign = { ...dataTransfer(), types: ['Files'] }

    const over = fireEvent.dragOver(column('Hecho'), { dataTransfer: foreign })

    expect(over).toBe(true) // sin preventDefault: no es un destino válido
    expect(column('Hecho')).not.toHaveClass('drop-target')
  })

  it('keeps the highlight while moving over children and clears it on leaving', async () => {
    renderBoard(createMockApi())
    await screen.findByText('En marcha')
    const transfer = dataTransfer()
    transfer.setData('application/x-lifeos-task', 't1')
    const target = column('Hecho')

    fireEvent.dragEnter(target, { dataTransfer: transfer })
    fireEvent.dragOver(target, { dataTransfer: transfer })
    fireEvent.dragEnter(card('Terminada'), { dataTransfer: transfer })
    fireEvent.dragLeave(target, { dataTransfer: transfer, relatedTarget: null })
    expect(target).toHaveClass('drop-target')
    fireEvent.dragLeave(card('Terminada'), { dataTransfer: transfer, relatedTarget: null })
    expect(target).not.toHaveClass('drop-target')
  })

  it('quick create keeps what was typed while the request was in flight', async () => {
    const api = createMockApi()
    const pending = deferred<Task>()
    api.createTask.mockImplementationOnce(() => pending.promise)
    renderBoard(api)
    await screen.findByText('En marcha')
    const form = within(screen.getByRole('form', { name: 'Nueva tarea' }))
    const input = form.getByLabelText('Título de la nueva tarea')

    fireEvent.change(input, { target: { value: 'Primera' } })
    fireEvent.click(form.getByRole('button', { name: 'Agregar tarea' }))
    fireEvent.change(input, { target: { value: 'Segunda' } })
    pending.resolve(task({ id: 'n1', title: 'Primera' }))

    await waitFor(() => expect(titlesIn('Por hacer')).toContain('Primera'))
    expect(input).toHaveValue('Segunda')
  })
})

function deferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (error: unknown) => void
  const promise = new Promise<T>((res, rej) => {
    resolve = res
    reject = rej
  })
  return { promise, resolve, reject }
}
