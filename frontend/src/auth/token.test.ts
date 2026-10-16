import { afterEach, describe, expect, it, vi } from 'vitest'
import { clearToken, readToken, writeToken } from './token'

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
