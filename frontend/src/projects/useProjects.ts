import { useEffect, useState } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Project, ProjectStatus } from '../api/types'
import { useApi } from '../api/useApi'
import type { StatusFilter } from './projectStatus'

const ALL_STATUSES: readonly ProjectStatus[] = ['active', 'completed', 'archived']

interface ProjectsResult {
  /** Clave de la petición que produjo este resultado (filtro + recargas). */
  key: string
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
  const [reloads, setReloads] = useState(0)
  const [result, setResult] = useState<ProjectsResult | null>(null)
  const key = `${filter}:${reloads}`

  useEffect(() => {
    let stale = false
    // "Todos" pide los tres estados de forma explícita, sin depender del default de la API.
    const status = filter === 'all' ? ALL_STATUSES : filter
    api.listProjects({ status }).then(
      (projects) => {
        if (!stale) setResult({ key, filter, projects, error: null })
      },
      (error: unknown) => {
        if (!stale) setResult({ key, filter, projects: [], error: errorMessage(error) })
      },
    )
    return () => {
      stale = true
    }
  }, [api, filter, key])

  const current = result && result.filter === filter ? result : null
  const loading = result?.key !== key

  return {
    projects: current?.projects ?? [],
    loading,
    error: !loading && current ? current.error : null,
    reload: () => setReloads((count) => count + 1),
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
