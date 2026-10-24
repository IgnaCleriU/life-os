import { useCallback, useEffect, useState } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Task } from '../api/types'
import { useApi } from '../api/useApi'

interface Loaded {
  key: string
  projectId: string
  tasks: Task[]
  error: string | null
}

/**
 * Carga las tareas de un proyecto. Se recarga al cambiar el id y descarta las
 * respuestas de peticiones superadas. `setTasks` permite actualizar la lista
 * localmente (optimismo, altas, bajas) sin volver a pedirla.
 */
export function useProjectTasks(projectId: string) {
  const api = useApi()
  const [reloads, setReloads] = useState(0)
  const [result, setResult] = useState<Loaded | null>(null)
  const key = `${projectId}:${reloads}`

  useEffect(() => {
    let stale = false
    api.listProjectTasks(projectId).then(
      (tasks) => {
        if (!stale) setResult({ key, projectId, tasks, error: null })
      },
      (error: unknown) => {
        if (!stale) setResult({ key, projectId, tasks: [], error: errorMessage(error) })
      },
    )
    return () => {
      stale = true
    }
  }, [api, projectId, key])

  const loading = result?.key !== key
  const current = result && result.projectId === projectId ? result : null

  const setTasks = useCallback((update: (tasks: Task[]) => Task[]) => {
    setResult((previous) => (previous ? { ...previous, tasks: update(previous.tasks) } : previous))
  }, [])

  return {
    tasks: current?.tasks ?? [],
    loading,
    error: !loading && current ? current.error : null,
    setTasks,
    reload: () => setReloads((count) => count + 1),
  }
}
