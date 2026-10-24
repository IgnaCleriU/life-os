import { useEffect, useRef, useState } from 'react'
import { ApiError } from '../api/client'
import { errorMessage } from '../api/errorMessage'
import type { Project } from '../api/types'
import { useApi } from '../api/useApi'
import ProjectDetail, { type ProjectChange } from './ProjectDetail'
import ProjectSidebar from './ProjectSidebar'
import type { StatusFilter } from './projectStatus'
import { useHashProjectId } from './useHashProjectId'
import { matchesStatusFilter, useProjects } from './useProjects'

const DISCARD_MESSAGE = 'Hay cambios sin guardar. ¿Descartarlos?'

/** Vista de proyectos: lista a la izquierda (arriba en pantallas angostas) y detalle a la derecha. */
export default function ProjectsPage() {
  const api = useApi()
  const [filter, setFilter] = useState<StatusFilter>('active')
  const [selectedId, selectProject] = useHashProjectId()
  const { projects, loading, error, reload, replaceProject } = useProjects(filter)
  const sidebarHeadingRef = useRef<HTMLHeadingElement>(null)
  const [dirty, setDirty] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)

  // Proyecto seleccionado que no está en la lista filtrada (p. ej. un reload con el hash
  // de un proyecto completado, con el filtro en Activos): se pide por id para no perder la selección.
  const [opened, setOpened] = useState<Project | null>(null)
  // Fallo al pedir ese proyecto, con el id al que corresponde.
  const [lookupError, setLookupError] = useState<{ id: string; message: string } | null>(null)
  // Un fallo es de la selección que lo produjo: al cambiar de proyecto se olvida, y volver a
  // elegirlo vuelve a pedirlo.
  useEffect(() => () => setLookupError(null), [selectedId])
  const lookupFailed = lookupError !== null && lookupError.id === selectedId
  const listed = projects.find((project) => project.id === selectedId) ?? null
  const selected = listed ?? (opened?.id === selectedId ? opened : null)
  // Se vuelve a pedir cada vez que la lista termina de cargar sin el proyecto (cambio de filtro,
  // recarga, o lista caída), así nunca se muestra una copia vieja.
  const needsLookup = selectedId !== null && listed === null && !loading && !lookupFailed

  // Estado actual para los callbacks que llegan tarde (una acción en vuelo puede terminar
  // después de que el usuario cambió de proyecto o de filtro).
  const latest = useRef({ selectedId, filter })
  useEffect(() => {
    latest.current = { selectedId, filter }
  })

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
          setNotice('Ese proyecto ya no existe.')
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

  function confirmDiscard(): boolean {
    return !dirty || window.confirm(DISCARD_MESSAGE)
  }

  function choose(projectId: string) {
    if (projectId === selectedId) return
    if (!confirmDiscard()) return
    setNotice(null)
    selectProject(projectId)
  }

  function applyFilter(next: StatusFilter) {
    setFilter(next)
    setOpened(null)
  }

  // Cambiar de filtro desmonta el detalle, así que también pide confirmación por una edición sin guardar.
  function changeFilter(next: StatusFilter) {
    if (!confirmDiscard()) return
    applyFilter(next)
  }

  // Tras una acción sobre el detalle. Solo afecta a la selección si el proyecto cambiado es el
  // seleccionado en ese momento; si el usuario ya eligió otro, se actualiza solo la lista.
  function handleChanged(change: ProjectChange) {
    const current = latest.current
    const id = change.type === 'updated' ? change.project.id : change.id
    const isSelected = id === current.selectedId

    if (change.type === 'updated') {
      replaceProject(change.project)
      if (isSelected) setOpened(change.project)
    }

    if (isSelected) {
      if (change.type === 'missing') {
        setNotice('Ese proyecto ya no existe; se quitó de la lista.')
        selectProject(null)
      } else if (
        change.type === 'deleted' ||
        !matchesStatusFilter(change.project, current.filter)
      ) {
        selectProject(null)
        // El detalle desaparece: el foco va a la lista.
        sidebarHeadingRef.current?.focus()
      }
    }
    reload()
  }

  function handleCreated(project: Project) {
    setNotice(null)
    selectProject(project.id)
    // Un proyecto nuevo está activo: si el filtro no lo incluye, se cambia a Activos (eso recarga la lista).
    if (filter === 'completed' || filter === 'archived') applyFilter('active')
    else reload()
  }

  let detail
  if (selected) {
    detail = (
      <ProjectDetail
        key={selected.id}
        project={selected}
        onChanged={handleChanged}
        onDirtyChange={setDirty}
      />
    )
  } else if (lookupFailed) {
    detail = (
      <div className="lookup-error">
        <p role="alert" className="form-error">
          No se pudo cargar el proyecto: {lookupError.message}
        </p>
        <button type="button" className="secondary" onClick={() => setLookupError(null)}>
          Reintentar
        </button>
      </div>
    )
  } else if (notice) {
    detail = (
      <p role="alert" className="form-error">
        {notice}
      </p>
    )
  } else {
    detail = (
      <p className="muted">
        {selectedId ? 'Cargando proyecto…' : 'Elegí un proyecto de la lista.'}
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
        onFilterChange={changeFilter}
        onSelect={choose}
        onRetry={reload}
        onCreated={handleCreated}
        headingRef={sidebarHeadingRef}
        confirmDiscard={confirmDiscard}
      />

      <div className="project-main">{detail}</div>
    </div>
  )
}
