import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { fileURLToPath, URL } from 'node:url';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    port: 3000,
    host: fontHost(),
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    globals: true,
    environment: 'node',
    include: ['src/**/*.test.ts'],
    exclude: ['e2e/**', 'node_modules/**'],
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    chunkSizeWarningLimit: 800,
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('recharts') || id.includes('d3')) {
              return 'charts';
            }
            if (id.includes('framer-motion') || id.includes('lucide-react')) {
              return 'ui-libs';
            }
            return 'vendor';
          }
          if (
            id.includes('src/features/interview') ||
            id.includes('src/features/resume') ||
            id.includes('src/features/jd') ||
            id.includes('src/features/matching') ||
            id.includes('src/features/supervisor')
          ) {
            return 'interview-pipeline';
          }
          if (id.includes('src/components/charts') || id.includes('reports')) {
            return 'analytics';
          }
        },
      },
    },
  },
});

function fontHost() {
  return true;
}