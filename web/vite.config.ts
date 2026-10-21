/// <reference types="vitest/config" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': 'http://127.0.0.1:5001' },
  },
  build: {
    sourcemap: false,
    rollupOptions: {
      output: { manualChunks: { 'react-vendor': ['react', 'react-dom', 'react-router'], motion: ['motion'] } },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test-setup.ts'],
    css: false,
  },
})
