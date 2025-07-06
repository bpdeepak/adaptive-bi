import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    watch: {
      usePolling: true,
    },
  },
  css: {
    postcss: './postcss.config.cjs',
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
  // Fix for Docker permission issues
  optimizeDeps: {
    include: ['react', 'react-dom'],
  },
  esbuild: {
    target: 'es2020',
  },
  // Additional Docker-specific configurations
  cacheDir: '/tmp/.vite',
  resolve: {
    preserveSymlinks: true,
  },
})
