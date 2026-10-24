// Contrato de la API REST (backend-java, adapter-rest). El JSON usa snake_case.

export type ProjectStatus = 'active' | 'completed' | 'archived'
export type TaskStatus = 'todo' | 'doing' | 'done'
export type Priority = 'low' | 'medium' | 'high'

export interface Project {
  id: string
  name: string
  description: string | null
  status: ProjectStatus
  created_at: string
}

export interface Task {
  id: string
  project_id: string
  title: string
  description: string | null
  status: TaskStatus
  priority: Priority
  /** Fecha ISO `YYYY-MM-DD`, o null si no tiene vencimiento. */
  due_date: string | null
  created_at: string
}

export interface HealthResponse {
  status: string
}

/** Cuerpo de `POST /projects`. */
export interface CreateProjectBody {
  name: string
  description?: string | null
}

/** Cuerpo de `PATCH /projects/{id}`: las claves omitidas no se tocan; `description: null` la limpia. */
export interface UpdateProjectBody {
  name?: string
  description?: string | null
}

/** Cuerpo de `POST /projects/{id}/tasks`. */
export interface CreateTaskBody {
  title: string
  priority?: Priority
  due_date?: string | null
  description?: string | null
}

/**
 * Cuerpo de `PATCH /tasks/{id}`: las claves omitidas no se tocan. `description`
 * y `due_date` se limpian con null; `title` y `priority` en null no hacen nada.
 */
export interface UpdateTaskBody {
  title?: string
  priority?: Priority
  description?: string | null
  due_date?: string | null
}

/** Cuerpo de `POST /tasks/{id}/move`. */
export interface MoveTaskBody {
  project_id: string
}

/** Filtros de `GET /projects`. Un array se envía como `?status=a&status=b`. */
export interface ProjectFilter {
  status?: ProjectStatus | readonly ProjectStatus[]
  q?: string
}

/** Filtros de `GET /tasks` y `GET /projects/{id}/tasks` (este último no admite `project_id`). */
export interface TaskFilter {
  project_id?: string
  status?: TaskStatus | readonly TaskStatus[]
  /** Fecha ISO `YYYY-MM-DD`. */
  due_before?: string
  q?: string
}

/** Forma de error de la API: `{"error": {"code", "message"}}`. */
export interface ApiErrorBody {
  error: {
    code: string
    message: string
  }
}
