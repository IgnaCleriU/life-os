import { useCallback, useEffect, useState } from 'react'

const PREFIX = '#/projects/'

function readProjectId(): string | null {
  const { hash } = window.location
  if (!hash.startsWith(PREFIX)) return null
  const raw = hash.slice(PREFIX.length)
  if (!raw) return null
  try {
    return decodeURIComponent(raw)
  } catch {
    return null
  }
}

/**
 * Id del proyecto seleccionado, guardado en el hash (`#/projects/<id>`) para que
 * un reload lo conserve. No usa un router: solo lee y reemplaza el hash.
 */
export function useHashProjectId(): [string | null, (projectId: string | null) => void] {
  const [projectId, setProjectId] = useState<string | null>(readProjectId)

  useEffect(() => {
    const onHashChange = () => setProjectId(readProjectId())
    window.addEventListener('hashchange', onHashChange)
    return () => window.removeEventListener('hashchange', onHashChange)
  }, [])

  const select = useCallback((next: string | null) => {
    setProjectId(next)
    const hash = next === null ? '' : `${PREFIX}${encodeURIComponent(next)}`
    // replaceState no dispara hashchange: el estado ya quedó actualizado arriba.
    window.history.replaceState(
      window.history.state,
      '',
      `${window.location.pathname}${window.location.search}${hash}`,
    )
  }, [])

  return [projectId, select]
}
