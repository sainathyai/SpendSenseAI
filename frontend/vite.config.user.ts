import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// Vite config for User Dashboard (separate port)
export default defineConfig({
  plugins: [react()],
  root: '.',
  server: {
    port: 5174,
    open: false,
  },
  build: {
    outDir: 'dist-user',
    rollupOptions: {
      input: resolve(__dirname, 'index-user.html'),
    },
  },
})

