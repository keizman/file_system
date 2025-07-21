import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:9301',
        changeOrigin: true
      },
      '/health': {
        target: 'http://localhost:9301',
        changeOrigin: true
      }
    }
  }
})