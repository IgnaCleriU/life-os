import type { DragEvent } from 'react'
import type { Task, TaskStatus } from '../api/types'
import {
  COLUMNS,
  PRIORITY_LABELS,
  STATUS_LABELS,
  allowedMoves,
  formatDueDate,
  isOverdue,
} from './taskModel'

export const DRAG_TYPE = 'text/plain'

interface TaskCardProps {
  task: Task
  onOpen: (task: Task) => void
  onMove: (task: Task, to: TaskStatus) => void
}

const PREVIEW_LENGTH = 100

function preview(text: string): string {
  const clean = text.replace(/\s+/g, ' ').trim()
  return clean.length > PREVIEW_LENGTH ? `${clean.slice(0, PREVIEW_LENGTH).trimEnd()}…` : clean
}

export default function TaskCard({ task, onOpen, onMove }: TaskCardProps) {
  const overdue = isOverdue(task)
  const order = COLUMNS.map((column) => column.status)

  function handleDragStart(event: DragEvent<HTMLElement>) {
    event.dataTransfer.setData(DRAG_TYPE, task.id)
    event.dataTransfer.effectAllowed = 'move'
  }

  return (
    <li className="task-card" draggable onDragStart={handleDragStart}>
      <button type="button" className="task-open" onClick={() => onOpen(task)}>
        {task.title}
      </button>
      <div className="task-meta">
        <span className={`priority-badge priority-${task.priority}`}>
          {PRIORITY_LABELS[task.priority]}
        </span>
        {task.due_date && (
          <span className={overdue ? 'task-due overdue' : 'task-due'}>
            {overdue ? 'Vencida: ' : 'Vence: '}
            {formatDueDate(task.due_date)}
          </span>
        )}
      </div>
      {task.description && <p className="task-description">{preview(task.description)}</p>}
      <div className="task-moves">
        {allowedMoves(task.status).map((to) => {
          const forward = order.indexOf(to) > order.indexOf(task.status)
          return (
            <button
              key={to}
              type="button"
              className="secondary"
              aria-label={`Mover a ${STATUS_LABELS[to]}`}
              onClick={() => onMove(task, to)}
            >
              {forward ? `${STATUS_LABELS[to]} ▶` : `◀ ${STATUS_LABELS[to]}`}
            </button>
          )
        })}
      </div>
    </li>
  )
}
