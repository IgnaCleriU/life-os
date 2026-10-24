import { useEffect, useRef, useState, type FormEvent } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Priority, Project, Task, UpdateTaskBody } from '../api/types'
import { useApi } from '../api/useApi'
import { PRIORITY_LABELS } from './taskModel'

interface TaskDialogProps {
  task: Task
  onClose: () => void
  /** Tarea ya guardada (editar). */
  onUpdated: (task: Task) => void
  /** La tarea dejó este proyecto (mover) o se eliminó. */
  onRemoved: (task: Task) => void
}

const PRIORITIES: Priority[] = ['high', 'medium', 'low']

/** Diálogo modal (`<dialog>`) para editar, mover a otro proyecto o eliminar una tarea. */
export default function TaskDialog({ task, onClose, onUpdated, onRemoved }: TaskDialogProps) {
  const api = useApi()
  const dialogRef = useRef<HTMLDialogElement>(null)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description ?? '')
  const [priority, setPriority] = useState<Priority>(task.priority)
  const [dueDate, setDueDate] = useState(task.due_date ?? '')
  const [projects, setProjects] = useState<Project[]>([])
  const [targetId, setTargetId] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    // Al cerrar, el foco vuelve a quien abrió el diálogo (la tarjeta).
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    if (typeof dialog.showModal === 'function') dialog.showModal()
    else dialog.setAttribute('open', '')
    return () => {
      if (opener?.isConnected) opener.focus()
    }
  }, [])

  useEffect(() => {
    let stale = false
    api.listProjects({ status: 'active' }).then(
      (list) => {
        if (!stale) setProjects(list.filter((project) => project.id !== task.project_id))
      },
      () => {
        // Sin la lista no se ofrece mover; editar y eliminar siguen funcionando.
      },
    )
    return () => {
      stale = true
    }
  }, [api, task.project_id])

  async function run(action: () => Promise<void>) {
    setBusy(true)
    setError(null)
    try {
      await action()
    } catch (failure) {
      setError(errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      setError('Ingresá un título para la tarea.')
      return
    }
    // Solo se envían los campos que cambiaron; vaciar descripción o fecha las limpia (null).
    const body: UpdateTaskBody = {}
    if (trimmedTitle !== task.title) body.title = trimmedTitle
    if (priority !== task.priority) body.priority = priority
    // Se compara el texto crudo (un espacio final guardado no cuenta como cambio) y se recorta al enviar.
    const newDescription = description.trim() || null
    if (description !== (task.description ?? '') && newDescription !== task.description) {
      body.description = newDescription
    }
    const newDueDate = dueDate || null
    if (newDueDate !== task.due_date) body.due_date = newDueDate
    if (Object.keys(body).length === 0) {
      onClose()
      return
    }
    await run(async () => {
      onUpdated(await api.updateTask(task.id, body))
      onClose()
    })
  }

  async function handleMove() {
    if (!targetId) return
    await run(async () => {
      await api.moveTask(task.id, { project_id: targetId })
      onRemoved(task)
      onClose()
    })
  }

  async function handleDelete() {
    if (!window.confirm(`¿Eliminar la tarea "${task.title}"?`)) return
    await run(async () => {
      await api.deleteTask(task.id)
      onRemoved(task)
      onClose()
    })
  }

  return (
    <dialog
      ref={dialogRef}
      className="task-dialog"
      aria-labelledby="task-dialog-title"
      onClose={onClose}
      onCancel={(event) => {
        // Escape durante un guardado en curso no cierra: el error tiene que poder verse.
        if (busy) event.preventDefault()
        else onClose()
      }}
    >
      <form onSubmit={handleSave} noValidate>
        <h3 id="task-dialog-title">Editar tarea</h3>
        <label htmlFor="task-title">Título</label>
        <input
          id="task-title"
          type="text"
          value={title}
          onChange={(event) => setTitle(event.target.value)}
        />
        <label htmlFor="task-description">Descripción</label>
        <textarea
          id="task-description"
          rows={4}
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
        <label htmlFor="task-priority">Prioridad</label>
        <select
          id="task-priority"
          value={priority}
          onChange={(event) => setPriority(event.target.value as Priority)}
        >
          {PRIORITIES.map((value) => (
            <option key={value} value={value}>
              {PRIORITY_LABELS[value]}
            </option>
          ))}
        </select>
        <label htmlFor="task-due">Vencimiento</label>
        <div className="row">
          <input
            id="task-due"
            type="date"
            value={dueDate}
            onChange={(event) => setDueDate(event.target.value)}
          />
          <button
            type="button"
            className="secondary"
            disabled={!dueDate}
            onClick={() => setDueDate('')}
          >
            Quitar fecha
          </button>
        </div>

        {error && (
          <p role="alert" className="form-error">
            {error}
          </p>
        )}

        <div className="actions">
          <button type="submit" disabled={busy}>
            Guardar
          </button>
          <button type="button" className="secondary" onClick={onClose}>
            Cancelar
          </button>
          <button type="button" className="danger" disabled={busy} onClick={handleDelete}>
            Eliminar
          </button>
        </div>

        {projects.length > 0 && (
          <>
            <label htmlFor="task-move">Mover a proyecto</label>
            <div className="row">
              <select
                id="task-move"
                value={targetId}
                onChange={(event) => setTargetId(event.target.value)}
              >
                <option value="">Elegí un proyecto…</option>
                {projects.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
              <button
                type="button"
                className="secondary"
                disabled={busy || !targetId}
                onClick={handleMove}
              >
                Mover
              </button>
            </div>
          </>
        )}
      </form>
    </dialog>
  )
}
