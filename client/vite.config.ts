import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'
  
  return {
    plugins: [react()],
    resolve: {
      alias: {
        '@': resolve(__dirname, './src'),
      },
    },
    server: {
      host: '0.0.0.0', // Allow access from outside container
      port: 3000,
      watch: {
        usePolling: true, // Required for Docker on Windows/Mac
        interval: 1000, // Poll every 1 second
      },
      proxy: {
        '/api': {
          target: process.env.VITE_API_BASE_URL || 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
    build: {
      outDir: 'dist',
      sourcemap: !isProduction,
      minify: isProduction ? 'esbuild' : false,
      rollupOptions: {
        output: {
          manualChunks: {
            vendor: ['react', 'react-dom'],
            zustand: ['zustand'],
          },
        },
      },
    },
    define: {
      __APP_ENV__: JSON.stringify(process.env.VITE_ENVIRONMENT || mode),
    },
  }
})
