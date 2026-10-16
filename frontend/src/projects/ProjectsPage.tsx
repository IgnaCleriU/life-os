import { useEffect, useState } from 'react'
import { useApi } from '../api/useApi'
import type { Project } from '../api/types'
import ProjectDetail from './ProjectDetail'
import ProjectSidebar from './ProjectSidebar'
import type { StatusFilter } from './projectStatus'
import { useHashProjectId } from './useHashProjectId'
import { useProjects } from './useProjects'

/** Vista de proyectos: lista a la izquierda (arriba en pantallas angostas) y detalle a la derecha. */
export default function ProjectsPage() {
  const api = useApi()
  const [filter, setFilter] = useState<StatusFilter>('active')
  const [selectedId, selectProject] = useHashProjectId()
  const { projects, loading, error, reload } = useProjects(filter)

  // Proyecto seleccionado que no está en la lista filtrada (p. ej. un reload con el hash
  // de un proyecto completado, con el filtro en Activos): se pide por id para no perder la selección.
  const [opened, setOpened] = useState<Project | null>(null)
  const selected =
    projects.find((project) => project.id === selectedId) ??
    (opened?.id === selectedId ? opened : null)
  const needsLookup = selectedId !== null && selected === null && !loading && !error

  useEffect(() => {
    if (selectedId === null || !needsLookup) return
    let stale = false
    api.getProject(selectedId).then(
      (project) => {
        if (!stale) setOpened(project)
      },
      () => {
        // El proyecto ya no existe (o no se pudo leer): se quita la selección.
        if (!stale) selectProject(null)
      },
    )
    return () => {
      stale = true
    }
  }, [api, selectedId, needsLookup, selectProject])

  function handleCreated(project: Project) {
    selectProject(project.id)
    // Un proyecto nuevo está activo: si el filtro no lo incluye, se cambia a Activos (eso recarga la lista).
    if (filter === 'completed' || filter === 'archived') setFilter('active')
    else reload()
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
      />

      <div className="project-main">
        {selected ? (
          <ProjectDetail key={selected.id} project={selected} />
        ) : (
          <p className="muted">
            {selectedId && !error ? 'Cargando proyecto…' : 'Elegí un proyecto de la lista.'}
          </p>
        )}
      </div>
    </div>
  )
}
