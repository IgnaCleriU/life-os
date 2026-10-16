import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

// La app se sirve bajo /app/ desde el backend Spring Boot. En `npm run dev`
// las rutas de la API se reenvían al backend Java local. El proxy reenvía el
// header Authorization del navegador tal cual: si la API tiene auth activa,
// responde 401 hasta que la app envíe el bearer token (lo agrega un PR
// posterior). changeOrigin hace que el backend vea Host 127.0.0.1 aunque el
// dev server escuche en otra interfaz (`npm run dev -- --host`).
const API_TARGET = 'http://127.0.0.1:8000'

export default defineConfig({
  base: '/app/',
  plugins: [react()],
  server: {
    proxy: {
      '/projects': { target: API_TARGET, changeOrigin: true },
      '/tasks': { target: API_TARGET, changeOrigin: true },
      '/health': { target: API_TARGET, changeOrigin: true },
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test-setup.ts'],
  },
})
