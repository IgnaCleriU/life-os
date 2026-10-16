import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// Vitest no expone los globals: RTL no limpia el DOM entre tests por sí solo.
afterEach(() => {
  cleanup()
})
