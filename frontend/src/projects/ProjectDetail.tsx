import type { ReactNode } from 'react'
import type { Project } from '../api/types'
import { PROJECT_STATUS_LABELS } from './projectStatus'

const CREATED_FORMAT = new Intl.DateTimeFormat('es-AR', { dateStyle: 'long' })

function formatCreatedAt(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : CREATED_FORMAT.format(date)
}

interface ProjectDetailProps {
  project: Project
  /** Contenido de la sección "Tablero" (el próximo cambio lo reemplaza por el kanban). */
  children?: ReactNode
}

export default function ProjectDetail({ project, children }: ProjectDetailProps) {
  return (
    <article className="project-detail">
      <header className="project-detail-header">
        <h2>{project.name}</h2>
        <span className={`status-badge status-${project.status}`}>
          {PROJECT_STATUS_LABELS[project.status]}
        </span>
      </header>

      {project.description ? (
        <p>{project.description}</p>
      ) : (
        <p className="muted">Sin descripción.</p>
      )}
      <p className="muted">Creado el {formatCreatedAt(project.created_at)}</p>

      <section aria-label="Tablero" className="board">
        {children ?? <p className="muted">El tablero de tareas llega en el próximo cambio.</p>}
      </section>
    </article>
  )
}
