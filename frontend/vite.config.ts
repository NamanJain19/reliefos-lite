import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3012,
    strictPort: true,
    host: true
  },
  build: {
    target: 'esnext',
    cssCodeSplit: true,
    chunkSizeWarningLimit: 600,
    rollupOptions: {
      output: {
        manualChunks(id) {
          const normalized = id.replace(/\\/g, '/');
          if (normalized.includes('/node_modules/')) {
            if (
              normalized.includes('/react/') ||
              normalized.includes('/react-dom/') ||
              normalized.includes('/scheduler/') ||
              normalized.includes('/react-router/') ||
              normalized.includes('/react-router-dom/') ||
              normalized.includes('/@remix-run/')
            ) {
              return 'vendor-react';
            }
            if (
              normalized.includes('/leaflet/') ||
              normalized.includes('/react-leaflet/')
            ) {
              return 'vendor-leaflet';
            }
            if (normalized.includes('/lucide-react/')) {
              return 'vendor-icons';
            }
            if (
              normalized.includes('/recharts/') ||
              normalized.includes('/victory-vendor/') ||
              normalized.includes('/d3-')
            ) {
              return 'vendor-charts';
            }
          }
        }
      }
    }
  }
});
