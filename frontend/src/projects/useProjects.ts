import { useEffect, useState } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Project, ProjectStatus } from '../api/types'
import { useApi } from '../api/useApi'
import type { StatusFilter } from './projectStatus'

const ALL_STATUSES: readonly ProjectStatus[] = ['active', 'completed', 'archived']

interface ProjectsResult {
  /** Número de la petición que produjo este resultado. */
  key: number
  filter: StatusFilter
  projects: Project[]
  error: string | null
}

/**
 * Carga los proyectos con el filtro de estado dado. Las respuestas de peticiones
 * superadas (cambio de filtro o recarga) se descartan. Durante una recarga se
 * siguen mostrando los proyectos anteriores.
 */
export function useProjects(filter: StatusFilter) {
  const api = useApi()
  // Cada cambio de filtro y cada recarga es una petición nueva con un número mayor, así volver
  // a un filtro anterior no se confunde con el resultado viejo.
  const [request, setRequest] = useState({ id: 0, filter })
  if (request.filter !== filter) setRequest({ id: request.id + 1, filter })
  const requestId = request.id
  const [result, setResult] = useState<ProjectsResult | null>(null)

  useEffect(() => {
    let stale = false
    // "Todos" pide los tres estados de forma explícita, sin depender del default de la API.
    const status = filter === 'all' ? ALL_STATUSES : filter
    api.listProjects({ status }).then(
      (projects) => {
        if (!stale) setResult({ key: requestId, filter, projects, error: null })
      },
      (error: unknown) => {
        if (!stale) setResult({ key: requestId, filter, projects: [], error: errorMessage(error) })
      },
    )
    return () => {
      stale = true
    }
  }, [api, filter, requestId])

  const current = result && result.filter === filter ? result : null
  const loading = result?.key !== requestId

  return {
    projects: current?.projects ?? [],
    loading,
    error: !loading && current ? current.error : null,
    reload: () => setRequest((previous) => ({ id: previous.id + 1, filter: previous.filter })),
    /** Reemplaza en la lista un proyecto ya cargado (si está), sin esperar a una recarga. */
    replaceProject: (project: Project) =>
      setResult((previous) =>
        previous && previous.projects.some((item) => item.id === project.id)
          ? {
              ...previous,
              projects: previous.projects.map((item) => (item.id === project.id ? project : item)),
            }
          : previous,
      ),
  }
}

/** ¿Un proyecto aparece en la lista con este filtro? */
export function matchesStatusFilter(project: Project, filter: StatusFilter): boolean {
  return filter === 'all' || project.status === filter
}
