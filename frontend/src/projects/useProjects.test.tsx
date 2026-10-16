import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it, vi } from 'vitest'
import type { ApiClient } from '../api/client'
import type { Project } from '../api/types'
import { ApiContext } from '../api/useApi'
import type { StatusFilter } from './projectStatus'
import { useProjects } from './useProjects'

const CASA: Project = {
  id: 'p1',
  name: 'Casa',
  description: null,
  status: 'active',
  created_at: '2026-01-10T12:00:00Z',
}
const HUERTA: Project = { ...CASA, id: 'p2', name: 'Huerta' }

function deferred<T>() {
  let resolve!: (value: T) => void
  const promise = new Promise<T>((done) => {
    resolve = done
  })
  return { promise, resolve }
}

describe('useProjects', () => {
  it('ignores a response to a request that was superseded by a reload', async () => {
    const first = deferred<Project[]>()
    const second = deferred<Project[]>()
    const listProjects = vi
      .fn()
      .mockReturnValueOnce(first.promise)
      .mockReturnValueOnce(second.promise)
    const api = { listProjects } as unknown as ApiClient
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ApiContext.Provider value={api}>{children}</ApiContext.Provider>
    )
    const { result } = renderHook(() => useProjects('active'), { wrapper })

    act(() => result.current.reload())
    expect(listProjects).toHaveBeenCalledTimes(2)

    // La respuesta de la segunda petición llega primero; la vieja, después, no debe pisarla.
    await act(async () => second.resolve([CASA, HUERTA]))
    await waitFor(() => expect(result.current.projects).toEqual([CASA, HUERTA]))

    await act(async () => first.resolve([CASA]))

    expect(result.current.projects).toEqual([CASA, HUERTA])
    expect(result.current.loading).toBe(false)
  })
})

describe('useProjects filter changes', () => {
  it('treats returning to a filter as a new request, not the old result', async () => {
    const back = deferred<Project[]>()
    const listProjects = vi
      .fn()
      .mockResolvedValueOnce([CASA])
      .mockReturnValueOnce(new Promise<Project[]>(() => undefined))
      .mockReturnValueOnce(back.promise)
    const api = { listProjects } as unknown as ApiClient
    const wrapper = ({ children }: { children: ReactNode }) => (
      <ApiContext.Provider value={api}>{children}</ApiContext.Provider>
    )
    const { result, rerender } = renderHook(
      ({ filter }: { filter: StatusFilter }) => useProjects(filter),
      { wrapper, initialProps: { filter: 'active' as StatusFilter } },
    )
    await waitFor(() => expect(result.current.projects).toEqual([CASA]))

    rerender({ filter: 'completed' })
    rerender({ filter: 'active' })

    expect(listProjects).toHaveBeenCalledTimes(3)
    expect(result.current.loading).toBe(true)

    await act(async () => back.resolve([CASA, HUERTA]))

    await waitFor(() => expect(result.current.projects).toEqual([CASA, HUERTA]))
    expect(result.current.loading).toBe(false)
  })
})
