import type { Project } from '../api/types'
import TaskCard from './TaskCard'
import './tasks.css'
import { COLUMNS, tasksOfColumn } from './taskModel'
import { useProjectTasks } from './useProjectTasks'

interface TaskBoardProps {
  project: Project
}

/** Kanban de las tareas de un proyecto: Por hacer / En curso / Hecho. */
export default function TaskBoard({ project }: TaskBoardProps) {
  const { tasks, loading, error, reload } = useProjectTasks(project.id)

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
    <div className="kanban">
      {COLUMNS.map((column) => {
        const items = tasksOfColumn(tasks, column.status)
        const headingId = `column-${column.status}`
        return (
          <section key={column.status} className="kanban-column" aria-labelledby={headingId}>
            <h3 id={headingId}>
              {column.label} <span className="muted">({items.length})</span>
            </h3>
            <ul className="task-list">
              {items.map((task) => (
                <TaskCard key={task.id} task={task} onOpen={() => {}} onMove={() => {}} />
              ))}
            </ul>
          </section>
        )
      })}
    </div>
  )
}
