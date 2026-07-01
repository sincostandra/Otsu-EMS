import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Dev: proxy API calls to Django so the SPA and API share an origin.
// Prod: Django serves the built bundle, so /api is already same-origin.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})
