import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { errorMessage } from '../api/errorMessage'
import type { Project } from '../api/types'
import { useApi } from '../api/useApi'
import TaskBoard from '../tasks/TaskBoard'
import ProjectDetail from './ProjectDetail'
import ProjectSidebar from './ProjectSidebar'
import type { StatusFilter } from './projectStatus'
import { useHashProjectId } from './useHashProjectId'
import { matchesStatusFilter, useProjects } from './useProjects'

/** Vista de proyectos: lista a la izquierda (arriba en pantallas angostas) y detalle a la derecha. */
export default function ProjectsPage() {
  const api = useApi()
  const [filter, setFilter] = useState<StatusFilter>('active')
  const [selectedId, selectProject] = useHashProjectId()
  const { projects, loading, error, reload, replaceProject } = useProjects(filter)
  const sidebarHeadingRef = useRef<HTMLHeadingElement>(null)

  // Proyecto seleccionado que no está en la lista filtrada (p. ej. un reload con el hash
  // de un proyecto completado, con el filtro en Activos): se pide por id para no perder la selección.
  const [opened, setOpened] = useState<Project | null>(null)
  // Fallo al pedir ese proyecto, con el id al que corresponde.
  const [lookupError, setLookupError] = useState<{ id: string; message: string } | null>(null)
  const lookupFailed = lookupError !== null && lookupError.id === selectedId
  const selected =
    projects.find((project) => project.id === selectedId) ??
    (opened?.id === selectedId ? opened : null)
  const needsLookup =
    selectedId !== null && selected === null && !loading && !error && !lookupFailed

  useEffect(() => {
    if (selectedId === null || !needsLookup) return
    let stale = false
    api.getProject(selectedId).then(
      (project) => {
        if (!stale) setOpened(project)
      },
      (lookupFailure: unknown) => {
        if (stale) return
        if (lookupFailure instanceof ApiError && lookupFailure.status === 404) {
          // El proyecto ya no existe: se quita la selección.
          selectProject(null)
        } else {
          setLookupError({ id: selectedId, message: errorMessage(lookupFailure) })
        }
      },
    )
    return () => {
      stale = true
    }
  }, [api, selectedId, needsLookup, selectProject])

  // Tras una acción sobre el detalle: se muestra el proyecto devuelto por la API y la lista se
  // recarga. El proyecto sigue seleccionado solo si aún cumple el filtro.
  function handleChanged(updated: Project | null) {
    if (updated === null || !matchesStatusFilter(updated, filter)) {
      selectProject(null)
      // El detalle desaparece: el foco va a la lista.
      sidebarHeadingRef.current?.focus()
    } else {
      replaceProject(updated)
      setOpened(updated)
    }
    reload()
  }

  function handleCreated(project: Project) {
    selectProject(project.id)
    // Un proyecto nuevo está activo: si el filtro no lo incluye, se cambia a Activos (eso recarga la lista).
    if (filter === 'completed' || filter === 'archived') setFilter('active')
    else reload()
  }

  function retryLookup() {
    setLookupError(null)
  }

  let detail
  if (selected) {
    detail = (
      <ProjectDetail key={selected.id} project={selected} onChanged={handleChanged}>
        <TaskBoard project={selected} />
      </ProjectDetail>
    )
  } else if (lookupFailed) {
    detail = (
      <div className="lookup-error">
        <p role="alert" className="form-error">
          No se pudo cargar el proyecto: {lookupError.message}
        </p>
        <button type="button" className="secondary" onClick={retryLookup}>
          Reintentar
        </button>
      </div>
    )
  } else {
    detail = (
      <p className="muted">
        {selectedId && !error ? 'Cargando proyecto…' : 'Elegí un proyecto de la lista.'}
      </p>
    )
  }

  return (
    <div className="projects-layout">
      <ProjectSidebar
        projects={projects}
        loading={loading}
        error={error}
        filter={filter}
        selectedId={selectedId}
        onFilterChange={setFilter}
        onSelect={selectProject}
        onRetry={reload}
        onCreated={handleCreated}
        headingRef={sidebarHeadingRef}
      />

      <div className="project-main">{detail}</div>
    </div>
  )
}
