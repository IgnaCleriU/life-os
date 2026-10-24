import type { Priority, Task, TaskStatus } from '../api/types'

export const COLUMNS: readonly { status: TaskStatus; label: string }[] = [
  { status: 'todo', label: 'Por hacer' },
  { status: 'doing', label: 'En curso' },
  { status: 'done', label: 'Hecho' },
]

export const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'Por hacer',
  doing: 'En curso',
  done: 'Hecho',
}

export const PRIORITY_LABELS: Record<Priority, string> = {
  low: 'Baja',
  medium: 'Media',
  high: 'Alta',
}

const PRIORITY_RANK: Record<Priority, number> = { high: 0, medium: 1, low: 2 }

/**
 * Transiciones de estado. El dominio (`Task.start/complete/reopen`) no impone
 * restricciones: cualquier estado puede pasar a cualquier otro, y cada destino
 * tiene su endpoint. Un movimiento al mismo estado no se ofrece.
 */
export function allowedMoves(from: TaskStatus): TaskStatus[] {
  return COLUMNS.map((column) => column.status).filter((status) => status !== from)
}

/** Prioridad alta→baja, luego vencimiento (sin fecha al final), luego creación. */
export function compareTasks(a: Task, b: Task): number {
  const byPriority = PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority]
  if (byPriority !== 0) return byPriority
  if (a.due_date !== b.due_date) {
    if (a.due_date === null) return 1
    if (b.due_date === null) return -1
    return a.due_date < b.due_date ? -1 : 1
  }
  if (a.created_at === b.created_at) return 0
  return a.created_at < b.created_at ? -1 : 1
}

export function tasksOfColumn(tasks: readonly Task[], status: TaskStatus): Task[] {
  return tasks.filter((task) => task.status === status).sort(compareTasks)
}

/** Hoy como `YYYY-MM-DD` en hora local. */
export function todayIso(now: Date = new Date()): string {
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

export function isOverdue(task: Task, today: string = todayIso()): boolean {
  return task.status !== 'done' && task.due_date !== null && task.due_date < today
}

const DUE_FORMAT = new Intl.DateTimeFormat('es-AR', {
  dateStyle: 'medium',
  timeZone: 'UTC',
})

export function formatDueDate(iso: string): string {
  const date = new Date(`${iso}T00:00:00Z`)
  return Number.isNaN(date.getTime()) ? iso : DUE_FORMAT.format(date)
}
