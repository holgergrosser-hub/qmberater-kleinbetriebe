import { defineConfig } from 'vite';
export default defineConfig({
  build: {
    minify: 'esbuild',
    outDir: 'dist',
    rollupOptions: { input: { main: 'index.html' } }
  },
  publicDir: 'public'
});
