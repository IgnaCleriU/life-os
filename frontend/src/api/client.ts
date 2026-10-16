import type {
  ApiErrorBody,
  CreateProjectBody,
  CreateTaskBody,
  HealthResponse,
  MoveTaskBody,
  Project,
  ProjectFilter,
  Task,
  TaskFilter,
  UpdateProjectBody,
  UpdateTaskBody,
} from './types'

/** Error devuelto por la API (cualquier respuesta no 2xx). */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export interface ApiClientOptions {
  /** Token que se envía como `Authorization: Bearer`. Si devuelve null, no se envía el header. */
  getToken: () => string | null
  /**
   * Se llama cuando una ruta autenticada responde 401, con el token que hizo la
   * petición. Permite ignorar un 401 tardío de un token ya reemplazado.
   */
  onUnauthorized?: (token: string | null) => void
}

type QueryValue = string | readonly string[] | undefined | null

/** Arma la query string; cada elemento de un array es un parámetro repetido. */
function buildQuery(params: Record<string, QueryValue>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue
    if (typeof value === 'string') {
      search.append(key, value)
    } else {
      for (const item of value) search.append(key, item)
    }
  }
  const query = search.toString()
  return query ? `?${query}` : ''
}

async function readError(response: Response): Promise<ApiError> {
  try {
    const data = (await response.json()) as Partial<ApiErrorBody> | null
    const error = data?.error
    if (error && typeof error.code === 'string' && typeof error.message === 'string') {
      return new ApiError(response.status, error.code, error.message)
    }
  } catch {
    // Cuerpo que no es JSON (p. ej. un proxy): se usa el fallback de abajo.
  }
  return new ApiError(
    response.status,
    `http_${response.status}`,
    response.statusText || `HTTP ${response.status}`,
  )
}

/**
 * Cliente tipado de la API. Usa `fetch` con rutas absolutas (la API vive en la
 * raíz del mismo origen, no bajo /app). Todas las funciones lanzan `ApiError`
 * si la respuesta no es 2xx; un fallo de red se propaga como `TypeError`.
 */
export function createApiClient(options: ApiClientOptions) {
  async function request<T>(
    method: string,
    path: string,
    { body, auth = true }: { body?: unknown; auth?: boolean } = {},
  ): Promise<T> {
    const headers: Record<string, string> = { Accept: 'application/json' }
    if (body !== undefined) headers['Content-Type'] = 'application/json'
    const token = auth ? options.getToken() : null
    if (token) headers.Authorization = `Bearer ${token}`

    const response = await fetch(path, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await readError(response)
      if (auth && response.status === 401) options.onUnauthorized?.(token)
      throw error
    }
    if (response.status === 204) return undefined as T
    try {
      return (await response.json()) as T
    } catch {
      // 2xx con un cuerpo que no es JSON (p. ej. el index.html de un proxy mal configurado).
      throw new ApiError(
        response.status,
        'invalid_response',
        'La API devolvió una respuesta inesperada que no es JSON',
      )
    }
  }

  const enc = encodeURIComponent

  return {
    /** `GET /health`: no requiere token. */
    health: () => request<HealthResponse>('GET', '/health', { auth: false }),

    // Proyectos

    listProjects: (filter: ProjectFilter = {}) =>
      request<Project[]>('GET', `/projects${buildQuery({ status: filter.status, q: filter.q })}`),
    getProject: (projectId: string) => request<Project>('GET', `/projects/${enc(projectId)}`),
    createProject: (body: CreateProjectBody) => request<Project>('POST', '/projects', { body }),
    updateProject: (projectId: string, body: UpdateProjectBody) =>
      request<Project>('PATCH', `/projects/${enc(projectId)}`, { body }),
    deleteProject: (projectId: string) => request<void>('DELETE', `/projects/${enc(projectId)}`),
    completeProject: (projectId: string) =>
      request<Project>('POST', `/projects/${enc(projectId)}/complete`),
    archiveProject: (projectId: string) =>
      request<Project>('POST', `/projects/${enc(projectId)}/archive`),
    activateProject: (projectId: string) =>
      request<Project>('POST', `/projects/${enc(projectId)}/activate`),
    restoreProject: (projectId: string) =>
      request<Project>('POST', `/projects/${enc(projectId)}/restore`),

    // Tareas

    /** `GET /projects/{id}/tasks`: las tareas de un proyecto, con los filtros de `GET /tasks`. */
    listProjectTasks: (projectId: string, filter: Omit<TaskFilter, 'project_id'> = {}) =>
      request<Task[]>(
        'GET',
        `/projects/${enc(projectId)}/tasks${buildQuery({
          status: filter.status,
          due_before: filter.due_before,
          q: filter.q,
        })}`,
      ),
    /** `GET /tasks`: tareas de todos los proyectos (o de uno, con `project_id`). */
    listTasks: (filter: TaskFilter = {}) =>
      request<Task[]>(
        'GET',
        `/tasks${buildQuery({
          project_id: filter.project_id,
          status: filter.status,
          due_before: filter.due_before,
          q: filter.q,
        })}`,
      ),
    getTask: (taskId: string) => request<Task>('GET', `/tasks/${enc(taskId)}`),
    createTask: (projectId: string, body: CreateTaskBody) =>
      request<Task>('POST', `/projects/${enc(projectId)}/tasks`, { body }),
    updateTask: (taskId: string, body: UpdateTaskBody) =>
      request<Task>('PATCH', `/tasks/${enc(taskId)}`, { body }),
    deleteTask: (taskId: string) => request<void>('DELETE', `/tasks/${enc(taskId)}`),
    completeTask: (taskId: string) => request<Task>('POST', `/tasks/${enc(taskId)}/complete`),
    startTask: (taskId: string) => request<Task>('POST', `/tasks/${enc(taskId)}/start`),
    reopenTask: (taskId: string) => request<Task>('POST', `/tasks/${enc(taskId)}/reopen`),
    restoreTask: (taskId: string) => request<Task>('POST', `/tasks/${enc(taskId)}/restore`),
    moveTask: (taskId: string, body: MoveTaskBody) =>
      request<Task>('POST', `/tasks/${enc(taskId)}/move`, { body }),
  }
}

export type ApiClient = ReturnType<typeof createApiClient>
