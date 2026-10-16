import { useState, type FormEvent } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Priority, Task } from '../api/types'
import { useApi } from '../api/useApi'
import { PRIORITY_LABELS } from './taskModel'

interface QuickCreateProps {
  projectId: string
  onCreated: (task: Task) => void
}

const PRIORITIES: Priority[] = ['high', 'medium', 'low']

/** Alta rápida al tope de "Por hacer": título, prioridad y vencimiento opcional. */
export default function QuickCreate({ projectId, onCreated }: QuickCreateProps) {
  const api = useApi()
  const [title, setTitle] = useState('')
  const [priority, setPriority] = useState<Priority>('medium')
  const [dueDate, setDueDate] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) {
      setError('Ingresá un título para la tarea.')
      return
    }
    setBusy(true)
    setError(null)
    try {
      const created = await api.createTask(projectId, {
        title: trimmed,
        priority,
        due_date: dueDate || null,
      })
      onCreated(created)
      setTitle('')
      setDueDate('')
    } catch (failure) {
      setError(errorMessage(failure))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="quick-create" aria-label="Nueva tarea" onSubmit={handleSubmit} noValidate>
      <label htmlFor="quick-title" className="visually-hidden">
        Título de la nueva tarea
      </label>
      <input
        id="quick-title"
        type="text"
        placeholder="Nueva tarea…"
        value={title}
        onChange={(event) => setTitle(event.target.value)}
      />
      <div className="row">
        <select
          aria-label="Prioridad"
          value={priority}
          onChange={(event) => setPriority(event.target.value as Priority)}
        >
          {PRIORITIES.map((value) => (
            <option key={value} value={value}>
              {PRIORITY_LABELS[value]}
            </option>
          ))}
        </select>
        <input
          type="date"
          aria-label="Vencimiento"
          value={dueDate}
          onChange={(event) => setDueDate(event.target.value)}
        />
      </div>
      {error && (
        <p role="alert" className="form-error">
          {error}
        </p>
      )}
      <button type="submit" disabled={busy}>
        Agregar tarea
      </button>
    </form>
  )
}
