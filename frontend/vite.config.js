import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: app is served at "/" and /api is proxied to Django (same-origin).
// Build: Django + WhiteNoise serve the bundle under /static/, so the built
// asset URLs must carry that base. Dev keeps "/" so `npm run dev` stays simple.
export default defineConfig(({ command }) => ({
  base: command === 'build' ? '/static/' : '/',
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
}))
