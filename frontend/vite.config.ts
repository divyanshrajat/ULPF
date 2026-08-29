import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // Proxy API calls to the FastAPI backend during Vite dev mode.
  // In production, FastAPI serves both the SPA and the API on :8000.
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    // Ensure assets use relative paths so FastAPI can serve them
    assetsDir: 'assets',
  },
})
