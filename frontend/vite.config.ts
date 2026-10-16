import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// La app se sirve bajo /app/ desde el backend Spring Boot. En `npm run dev`
// las rutas de la API se reenvían al backend Java local.
const API_TARGET = 'http://127.0.0.1:8000'

export default defineConfig({
  base: '/app/',
  plugins: [react()],
  server: {
    proxy: {
      '/projects': API_TARGET,
      '/tasks': API_TARGET,
      '/health': API_TARGET,
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
})
