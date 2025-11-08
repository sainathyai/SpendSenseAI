import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve as pathResolve, join } from 'path'
import { copyFileSync, existsSync } from 'fs'

// Vite config for User Dashboard (separate port)
export default defineConfig({
  plugins: [
    react(),
    {
      name: 'copy-user-index-html',
      closeBundle() {
        const outDir = pathResolve(__dirname, 'dist-user')
        const source = join(outDir, 'index-user.html')
        const target = join(outDir, 'index.html')

        if (existsSync(source)) {
          copyFileSync(source, target)
        }
      },
    },
  ],
  root: '.',
  server: {
    port: 5174,
    open: false,
  },
  build: {
    outDir: 'dist-user',
    rollupOptions: {
      input: {
        index: pathResolve(__dirname, 'index-user.html'),
      },
    },
  },
})

