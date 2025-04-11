import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: '/',  // Use root path for development
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    assetsDir: 'assets', // Ensure consistency with the FastAPI route
    rollupOptions: {
      output: {
        manualChunks: undefined
      }
    }
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    proxy: {
      '/api': {
        target: 'http://ragnode-backend:8000',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path
      },
      '/static': {
        target: 'http://ragnode-backend:8000',
        changeOrigin: true,
        secure: false
      }
    }
  }
});