import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { ApiClient } from '../api/client'
import { ApiError } from '../api/client'
import type { Project } from '../api/types'
import { ApiContext } from '../api/useApi'
import ProjectDetail from './ProjectDetail'

const CASA: Project = {
  id: 'p1',
  name: 'Casa',
  description: 'Reformas',
  status: 'active',
  created_at: '2026-01-10T12:00:00Z',
}

function createMockApi() {
  return {
    updateProject: vi.fn(),
    deleteProject: vi.fn(),
    completeProject: vi.fn(),
    archiveProject: vi.fn(),
    activateProject: vi.fn(),
  }
}

function renderDetail(project: Project, api = createMockApi()) {
  const onChanged = vi.fn()
  render(
    <ApiContext.Provider value={api as unknown as ApiClient}>
      <ProjectDetail project={project} onChanged={onChanged} />
    </ApiContext.Provider>,
  )
  return { api, onChanged }
}

afterEach(() => {
  vi.restoreAllMocks()
})

describe('ProjectDetail actions', () => {
  it('offers complete and archive for an active project', () => {
    renderDetail(CASA)

    expect(screen.getByRole('button', { name: 'Completar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Archivar' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Activar' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Editar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Eliminar' })).toBeInTheDocument()
  })

  it('offers archive and activate for a completed project', () => {
    renderDetail({ ...CASA, status: 'completed' })

    expect(screen.queryByRole('button', { name: 'Completar' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Archivar' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Activar' })).toBeInTheDocument()
  })

  it('offers complete and activate for an archived project', () => {
    renderDetail({ ...CASA, status: 'archived' })

    expect(screen.getByRole('button', { name: 'Completar' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Archivar' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Activar' })).toBeInTheDocument()
  })

  it('completes the project and reports the updated one', async () => {
    const { api, onChanged } = renderDetail(CASA)
    const updated = { ...CASA, status: 'completed' as const }
    api.completeProject.mockResolvedValue(updated)

    fireEvent.click(screen.getByRole('button', { name: 'Completar' }))

    await waitFor(() => expect(onChanged).toHaveBeenCalledWith(updated))
    expect(api.completeProject).toHaveBeenCalledWith('p1')
  })

  it('edits the name and description with PATCH and clears an empty description', async () => {
    const { api, onChanged } = renderDetail(CASA)
    const updated = { ...CASA, name: 'Casa nueva', description: null }
    api.updateProject.mockResolvedValue(updated)

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    expect(screen.getByLabelText('Nombre')).toHaveValue('Casa')
    expect(screen.getByLabelText('Descripción (opcional)')).toHaveValue('Reformas')

    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: '  Casa nueva ' } })
    fireEvent.change(screen.getByLabelText('Descripción (opcional)'), { target: { value: '' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    await waitFor(() => expect(onChanged).toHaveBeenCalledWith(updated))
    expect(api.updateProject).toHaveBeenCalledWith('p1', { name: 'Casa nueva', description: null })
  })

  it('does not send an edit with an empty name', () => {
    const { api } = renderDetail(CASA)

    fireEvent.click(screen.getByRole('button', { name: 'Editar' }))
    fireEvent.change(screen.getByLabelText('Nombre'), { target: { value: '  ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Guardar' }))

    expect(screen.getByRole('alert')).toHaveTextContent('Ingresá un nombre')
    expect(api.updateProject).not.toHaveBeenCalled()
  })

  it('deletes the project after confirmation', async () => {
    const confirm = vi.spyOn(window, 'confirm').mockReturnValue(true)
    const { api, onChanged } = renderDetail(CASA)
    api.deleteProject.mockResolvedValue(undefined)

    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }))

    expect(confirm).toHaveBeenCalledWith(expect.stringContaining('"Casa"'))
    await waitFor(() => expect(onChanged).toHaveBeenCalledWith(null))
    expect(api.deleteProject).toHaveBeenCalledWith('p1')
  })

  it('does not delete when the confirmation is cancelled', () => {
    vi.spyOn(window, 'confirm').mockReturnValue(false)
    const { api, onChanged } = renderDetail(CASA)

    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }))

    expect(api.deleteProject).not.toHaveBeenCalled()
    expect(onChanged).not.toHaveBeenCalled()
  })

  it('shows the API message when the project cannot be deleted (409)', async () => {
    vi.spyOn(window, 'confirm').mockReturnValue(true)
    const { api, onChanged } = renderDetail(CASA)
    api.deleteProject.mockRejectedValue(
      new ApiError(
        409,
        'project_not_empty',
        'El proyecto tiene tareas: movelas o eliminalas antes.',
      ),
    )

    fireEvent.click(screen.getByRole('button', { name: 'Eliminar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'El proyecto tiene tareas: movelas o eliminalas antes.',
    )
    expect(onChanged).not.toHaveBeenCalled()
  })
})
