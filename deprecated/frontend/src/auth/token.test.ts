import { afterEach, describe, expect, it, vi } from 'vitest'
import { clearToken, clearTokenIfCurrent, readToken, subscribeToTokenChanges, writeToken } from './token'

afterEach(() => {
  vi.restoreAllMocks()
  clearToken()
  window.localStorage.clear()
})

describe('token storage', () => {
  it('stores the token in localStorage under lifeos.token', () => {
    writeToken('abc')

    expect(window.localStorage.getItem('lifeos.token')).toBe('abc')
    expect(readToken()).toBe('abc')
  })

  it('clears the token from localStorage', () => {
    writeToken('abc')
    clearToken()

    expect(window.localStorage.getItem('lifeos.token')).toBeNull()
    expect(readToken()).toBeNull()
  })

  it('falls back to memory when localStorage throws on write', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota', 'QuotaExceededError')
    })

    expect(() => writeToken('mem')).not.toThrow()
    expect(readToken()).toBe('mem')
  })

  it('returns null without throwing when localStorage throws on read', () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })

    expect(() => readToken()).not.toThrow()
    expect(readToken()).toBeNull()
  })

  it('removes an older stored token when the new write fails', () => {
    window.localStorage.setItem('lifeos.token', 'old')
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('quota', 'QuotaExceededError')
    })

    writeToken('new')

    expect(window.localStorage.getItem('lifeos.token')).toBeNull()
    expect(readToken()).toBe('new')
  })

  it('does not throw when both write and remove fail', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })

    expect(() => writeToken('new')).not.toThrow()
    expect(readToken()).toBe('new')
  })

  it('clearTokenIfCurrent ignores a stale token and clears the current one', () => {
    writeToken('token-b')

    expect(clearTokenIfCurrent('token-a')).toBe(false)
    expect(readToken()).toBe('token-b')

    expect(clearTokenIfCurrent('token-b')).toBe(true)
    expect(readToken()).toBeNull()
  })

  it('notifies token changes from other tabs through the storage event', () => {
    const onChange = vi.fn()
    const unsubscribe = subscribeToTokenChanges(onChange)

    window.dispatchEvent(new StorageEvent('storage', { key: 'lifeos.token', newValue: 'from-other-tab' }))
    window.dispatchEvent(new StorageEvent('storage', { key: 'lifeos.token', newValue: null }))
    window.dispatchEvent(new StorageEvent('storage', { key: null, newValue: null }))
    window.dispatchEvent(new StorageEvent('storage', { key: 'other.key', newValue: 'x' }))

    expect(onChange.mock.calls).toEqual([['from-other-tab'], [null], [null]])
    unsubscribe()
    window.dispatchEvent(new StorageEvent('storage', { key: 'lifeos.token', newValue: 'late' }))
    expect(onChange).toHaveBeenCalledTimes(3)
  })

  it('keeps the in-memory token when localStorage is blocked', () => {
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })
    vi.spyOn(Storage.prototype, 'removeItem').mockImplementation(() => {
      throw new DOMException('blocked', 'SecurityError')
    })

    writeToken('mem')
    expect(readToken()).toBe('mem')
    expect(() => clearToken()).not.toThrow()
    expect(readToken()).toBeNull()
  })
})
