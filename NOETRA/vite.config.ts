import react from '@vitejs/plugin-react'
import path from 'node:path'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api/video-notes': { target: 'http://127.0.0.1:8765', changeOrigin: true },
      '/api/videos': { target: 'http://127.0.0.1:8765', changeOrigin: true },
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    // three.js is intentionally large; its scene is code-split via the
    // dynamic import in GlassSculpture, so it never blocks the first paint.
    chunkSizeWarningLimit: 1200,
  },
})
