import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  base: '/history-plan/',
  server: {
    port: 5173,
    proxy: {
      '/history-plan/api': {
        target: 'http://127.0.0.1:8023',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/history-plan/, '')
      }
    }
  },
  build: { outDir: 'dist' }
})
