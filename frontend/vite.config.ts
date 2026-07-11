import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5174,
    open: true,
    proxy: {
      // 前后端联调: 前端 /api 请求代理到后端 FastAPI
      // 用 127.0.0.1 避免 localhost IPv6 解析导致的连接延迟
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 简历原文件 (PDF/DOC) 由后端 StaticFiles 挂载在 /uploads, 需代理否则 404
      '/uploads': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
