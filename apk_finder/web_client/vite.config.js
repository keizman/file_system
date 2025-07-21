import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  
  return {
    plugins: [vue()],
    server: {
      port: 3000,
      proxy: {
        '/api': {
          target: env.VITE_SERVER_URL || 'http://localhost:9301',
          changeOrigin: true
        },
        '/health': {
          target: env.VITE_SERVER_URL || 'http://localhost:9301',
          changeOrigin: true
        }
      }
    }
  }
})