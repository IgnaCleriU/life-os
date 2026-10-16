import type { ProjectStatus } from '../api/types'

export const PROJECT_STATUS_LABELS: Record<ProjectStatus, string> = {
  active: 'Activo',
  completed: 'Completado',
  archived: 'Archivado',
}

/** Filtro de la lista: un estado, o todos. */
export type StatusFilter = ProjectStatus | 'all'

export const STATUS_FILTER_OPTIONS: readonly { value: StatusFilter; label: string }[] = [
  { value: 'active', label: 'Activos' },
  { value: 'completed', label: 'Completados' },
  { value: 'archived', label: 'Archivados' },
  { value: 'all', label: 'Todos' },
]
