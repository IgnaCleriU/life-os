import { useState, type DragEvent } from 'react'
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

  function replaceTask(id: string, change: (task: Task) => Task) {
    setTasks((current) => current.map((item) => (item.id === id ? change(item) : item)))
  }

  /**
   * Mueve una tarea de columna: cada destino tiene su endpoint (`start`,
   * `complete`, `reopen`). La UI cambia al instante y se revierte si falla.
   */
  async function moveTask(task: Task, to: TaskStatus) {
    const from = task.status
    if (from === to) return
    setActionError(null)
    replaceTask(task.id, (item) => ({ ...item, status: to }))
    try {
      const updated =
        to === 'doing'
          ? await api.startTask(task.id)
          : to === 'done'
            ? await api.completeTask(task.id)
            : await api.reopenTask(task.id)
      replaceTask(task.id, () => updated)
    } catch (failure) {
      replaceTask(task.id, (item) => ({ ...item, status: from }))
      setActionError(`No se pudo mover "${task.title}": ${errorMessage(failure)}`)
    }
  }

  function handleDragOver(event: DragEvent<HTMLElement>, status: TaskStatus) {
    event.preventDefault()
    event.dataTransfer.dropEffect = 'move'
    if (dropTarget !== status) setDropTarget(status)
  }

  function handleDrop(event: DragEvent<HTMLElement>, status: TaskStatus) {
    event.preventDefault()
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
              onDragLeave={(event) => {
                if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
                  setDropTarget(null)
                }
              }}
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
