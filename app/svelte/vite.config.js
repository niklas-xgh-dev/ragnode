import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: '/dist/',  // Match the FastAPI static file mounting
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
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000'
    }
  }
});