import { useRef, useState, type DragEvent } from 'react'
import { errorMessage } from '../api/errorMessage'
import type { Project, Task, TaskStatus } from '../api/types'
import { useApi } from '../api/useApi'
import QuickCreate from './QuickCreate'
import TaskCard, { DRAG_TYPE } from './TaskCard'
import TaskDialog from './TaskDialog'
import './tasks.css'
import { COLUMNS, tasksOfColumn } from './taskModel'
import { useProjectTasks } from './useProjectTasks'

interface TaskBoardProps {
  project: Project
}

/** Kanban de las tareas de un proyecto: Por hacer / En curso / Hecho. */
export default function TaskBoard({ project }: TaskBoardProps) {
  const api = useApi()
  const { tasks, loading, error, setTasks, reload } = useProjectTasks(project.id)
  const [actionError, setActionError] = useState<string | null>(null)
  const [editing, setEditing] = useState<Task | null>(null)
  const [dropTarget, setDropTarget] = useState<TaskStatus | null>(null)
  const inflight = useRef(
    new Map<string, { latest: number; pending: number; confirmed: TaskStatus }>(),
  )
  const enters = useRef<Record<TaskStatus, number>>({ todo: 0, doing: 0, done: 0 })

  function replaceTask(id: string, change: (task: Task) => Task) {
    setTasks((current) => current.map((item) => (item.id === id ? change(item) : item)))
  }

  /**
   * Mueve una tarea de columna: cada destino tiene su endpoint (`start`,
   * `complete`, `reopen`). La UI cambia al instante y se revierte si falla.
   */
  async function moveTask(task: Task, to: TaskStatus) {
    if (task.status === to) return
    // Con movimientos superpuestos de una misma tarea solo cuenta el último pedido: las
    // respuestas atrasadas no pisan la UI, y un fallo vuelve al último estado confirmado.
    const entry = inflight.current.get(task.id) ?? {
      latest: 0,
      pending: 0,
      confirmed: task.status,
    }
    inflight.current.set(task.id, entry)
    const mine = ++entry.latest
    entry.pending += 1
    setActionError(null)
    replaceTask(task.id, (item) => ({ ...item, status: to }))
    try {
      const updated =
        to === 'doing'
          ? await api.startTask(task.id)
          : to === 'done'
            ? await api.completeTask(task.id)
            : await api.reopenTask(task.id)
      entry.confirmed = updated.status
      if (mine === entry.latest) replaceTask(task.id, () => updated)
    } catch (failure) {
      if (mine === entry.latest) {
        replaceTask(task.id, (item) => ({ ...item, status: entry.confirmed }))
        setActionError(`No se pudo mover "${task.title}": ${errorMessage(failure)}`)
      }
    } finally {
      entry.pending -= 1
      if (entry.pending === 0) inflight.current.delete(task.id)
    }
  }

  function carriesTask(event: DragEvent<HTMLElement>): boolean {
    return Array.from(event.dataTransfer.types ?? []).includes(DRAG_TYPE)
  }

  function handleDragEnter(event: DragEvent<HTMLElement>, status: TaskStatus) {
    if (!carriesTask(event)) return
    enters.current[status] += 1
  }

  function handleDragLeave(event: DragEvent<HTMLElement>, status: TaskStatus) {
    if (!carriesTask(event)) return
    enters.current[status] = Math.max(0, enters.current[status] - 1)
    if (enters.current[status] === 0)
      setDropTarget((current) => (current === status ? null : current))
  }

  function handleDragOver(event: DragEvent<HTMLElement>, status: TaskStatus) {
    if (!carriesTask(event)) return
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    if (dropTarget !== status) setDropTarget(status)
  }

  function handleDrop(event: DragEvent<HTMLElement>, status: TaskStatus) {
    if (!carriesTask(event)) return
    event.preventDefault()
    enters.current = { todo: 0, doing: 0, done: 0 }
    setDropTarget(null)
    const task = tasks.find((item) => item.id === event.dataTransfer.getData(DRAG_TYPE))
    if (task) void moveTask(task, status)
  }

  if (loading && tasks.length === 0) return <p className="muted">Cargando tareas…</p>
  if (error) {
    return (
      <div className="sidebar-error">
        <p role="alert" className="form-error">
          {error}
        </p>
        <button type="button" className="secondary" onClick={reload}>
          Reintentar
        </button>
      </div>
    )
  }

  return (
    <>
      {actionError && (
        <p role="alert" className="form-error">
          {actionError}
        </p>
      )}
      <div className="kanban">
        {COLUMNS.map((column) => {
          const items = tasksOfColumn(tasks, column.status)
          const headingId = `column-${column.status}`
          return (
            <section
              key={column.status}
              className={
                dropTarget === column.status ? 'kanban-column drop-target' : 'kanban-column'
              }
              aria-labelledby={headingId}
              onDragOver={(event) => handleDragOver(event, column.status)}
              onDragEnter={(event) => handleDragEnter(event, column.status)}
              onDragLeave={(event) => handleDragLeave(event, column.status)}
              onDrop={(event) => handleDrop(event, column.status)}
            >
              <h3 id={headingId}>
                {column.label} <span className="muted">({items.length})</span>
              </h3>
              {column.status === 'todo' && (
                <QuickCreate
                  projectId={project.id}
                  onCreated={(created) => setTasks((current) => [...current, created])}
                />
              )}
              <ul className="task-list">
                {items.map((task) => (
                  <TaskCard key={task.id} task={task} onOpen={setEditing} onMove={moveTask} />
                ))}
              </ul>
            </section>
          )
        })}
      </div>
      {editing && (
        <TaskDialog
          key={editing.id}
          task={editing}
          onClose={() => setEditing(null)}
          onUpdated={(updated) => replaceTask(updated.id, () => updated)}
          onRemoved={(removed) => setTasks((current) => current.filter((t) => t.id !== removed.id))}
        />
      )}
    </>
  )
}
