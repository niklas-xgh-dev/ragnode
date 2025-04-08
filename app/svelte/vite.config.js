import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
  plugins: [svelte()],
  base: '/',  // This is important
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    assetsDir: 'assets' // Ensure consistency with the FastAPI route
  }
});