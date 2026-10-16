import { useState, type FormEvent, type ReactNode } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Project } from '../api/types'
import { useApi } from '../api/useApi'
import { PROJECT_STATUS_LABELS } from './projectStatus'

const CREATED_FORMAT = new Intl.DateTimeFormat('es-AR', { dateStyle: 'long' })

function formatCreatedAt(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? iso : CREATED_FORMAT.format(date)
}

interface ProjectDetailProps {
  project: Project
  /** Se llama tras una acción con el proyecto actualizado, o con null si se eliminó. */
  onChanged: (project: Project | null) => void
  /** Contenido de la sección "Tablero" (el próximo cambio lo reemplaza por el kanban). */
  children?: ReactNode
}

export default function ProjectDetail({ project, onChanged, children }: ProjectDetailProps) {
  const api = useApi()
  const [editing, setEditing] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [formError, setFormError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)

  function startEditing() {
    setName(project.name)
    setDescription(project.description ?? '')
    setFormError(null)
    setEditing(true)
  }

  async function run(action: () => Promise<Project | null>) {
    setBusy(true)
    setActionError(null)
    try {
      onChanged(await action())
    } catch (error) {
      setActionError(errorMessage(error))
    } finally {
      setBusy(false)
    }
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedName = name.trim()
    if (!trimmedName) {
      setFormError('Ingresá un nombre para el proyecto.')
      return
    }
    setFormError(null)
    await run(async () => {
      // La descripción vacía se envía como null: la limpia en la API.
      const updated = await api.updateProject(project.id, {
        name: trimmedName,
        description: description.trim() || null,
      })
      setEditing(false)
      return updated
    })
  }

  function handleDelete() {
    if (
      !window.confirm(`¿Eliminar el proyecto "${project.name}"? Esta acción no se puede deshacer.`)
    ) {
      return
    }
    void run(async () => {
      await api.deleteProject(project.id)
      return null
    })
  }

  return (
    <article className="project-detail">
      <header className="project-detail-header">
        <h2>{project.name}</h2>
        <span className={`status-badge status-${project.status}`}>
          {PROJECT_STATUS_LABELS[project.status]}
        </span>
      </header>

      {editing ? (
        <form className="inline-form" aria-label="Editar proyecto" onSubmit={handleSave} noValidate>
          <label htmlFor="edit-project-name">Nombre</label>
          <input
            id="edit-project-name"
            type="text"
            required
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <label htmlFor="edit-project-description">Descripción (opcional)</label>
          <textarea
            id="edit-project-description"
            rows={3}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          {formError && (
            <p role="alert" className="form-error">
              {formError}
            </p>
          )}
          <div className="actions">
            <button type="submit" disabled={busy}>
              Guardar
            </button>
            <button type="button" className="secondary" onClick={() => setEditing(false)}>
              Cancelar
            </button>
          </div>
        </form>
      ) : (
        <>
          {project.description ? (
            <p>{project.description}</p>
          ) : (
            <p className="muted">Sin descripción.</p>
          )}
          <p className="muted">Creado el {formatCreatedAt(project.created_at)}</p>
        </>
      )}

      {actionError && (
        <p role="alert" className="form-error">
          {actionError}
        </p>
      )}

      {!editing && (
        <div className="actions">
          {project.status === 'active' ? (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={() => run(() => api.completeProject(project.id))}
              >
                Completar
              </button>
              <button
                type="button"
                className="secondary"
                disabled={busy}
                onClick={() => run(() => api.archiveProject(project.id))}
              >
                Archivar
              </button>
            </>
          ) : (
            <button
              type="button"
              disabled={busy}
              onClick={() => run(() => api.activateProject(project.id))}
            >
              Activar
            </button>
          )}
          <button type="button" className="secondary" disabled={busy} onClick={startEditing}>
            Editar
          </button>
          <button type="button" className="danger" disabled={busy} onClick={handleDelete}>
            Eliminar
          </button>
        </div>
      )}

      <section aria-label="Tablero" className="board">
        {children ?? <p className="muted">El tablero de tareas llega en el próximo cambio.</p>}
      </section>
    </article>
  )
}
