import { useState, type FormEvent } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Project } from '../api/types'
import { useApi } from '../api/useApi'
import { STATUS_FILTER_OPTIONS, type StatusFilter } from './projectStatus'

interface ProjectSidebarProps {
  projects: Project[]
  loading: boolean
  error: string | null
  filter: StatusFilter
  selectedId: string | null
  onFilterChange: (filter: StatusFilter) => void
  onSelect: (projectId: string) => void
  onRetry: () => void
  /** Se llama con el proyecto recién creado. */
  onCreated: (project: Project) => void
}

export default function ProjectSidebar({
  projects,
  loading,
  error,
  filter,
  selectedId,
  onFilterChange,
  onSelect,
  onRetry,
  onCreated,
}: ProjectSidebarProps) {
  return (
    <aside className="project-sidebar" aria-label="Proyectos">
      <h2>Proyectos</h2>

      <div className="sidebar-section">
        <label htmlFor="project-status-filter">Estado</label>
        <select
          id="project-status-filter"
          value={filter}
          onChange={(event) => {
            const option = STATUS_FILTER_OPTIONS.find((item) => item.value === event.target.value)
            if (option) onFilterChange(option.value)
          }}
        >
          {STATUS_FILTER_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        {error ? (
          <div className="sidebar-error">
            <p role="alert" className="form-error">
              {error}
            </p>
            <button type="button" className="secondary" onClick={onRetry}>
              Reintentar
            </button>
          </div>
        ) : loading && projects.length === 0 ? (
          <p className="muted" role="status">
            Cargando proyectos…
          </p>
        ) : projects.length === 0 ? (
          <p className="muted">No hay proyectos en este estado.</p>
        ) : (
          <ul className="project-list">
            {projects.map((project) => (
              <li key={project.id}>
                <button
                  type="button"
                  className="list-item"
                  aria-current={project.id === selectedId ? 'true' : undefined}
                  onClick={() => onSelect(project.id)}
                >
                  {project.name}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      <NewProjectForm onCreated={onCreated} />
    </aside>
  )
}

function NewProjectForm({ onCreated }: { onCreated: (project: Project) => void }) {
  const api = useApi()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedName = name.trim()
    if (!trimmedName) {
      setFormError('Ingresá un nombre para el proyecto.')
      return
    }
    setSaving(true)
    setFormError(null)
    try {
      const created = await api.createProject({
        name: trimmedName,
        description: description.trim() || null,
      })
      setName('')
      setDescription('')
      onCreated(created)
    } catch (error) {
      setFormError(errorMessage(error))
    } finally {
      setSaving(false)
    }
  }

  return (
    <form
      className="new-project"
      aria-labelledby="new-project-title"
      onSubmit={handleSubmit}
      noValidate
    >
      <h2 id="new-project-title">Nuevo proyecto</h2>
      <label htmlFor="new-project-name">Nombre</label>
      <input
        id="new-project-name"
        type="text"
        required
        value={name}
        onChange={(event) => setName(event.target.value)}
      />
      <label htmlFor="new-project-description">Descripción (opcional)</label>
      <textarea
        id="new-project-description"
        rows={2}
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />
      {formError && (
        <p role="alert" className="form-error">
          {formError}
        </p>
      )}
      <button type="submit" disabled={saving}>
        {saving ? 'Creando…' : 'Crear proyecto'}
      </button>
    </form>
  )
}
