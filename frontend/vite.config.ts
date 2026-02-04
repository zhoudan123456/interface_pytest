import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    host: '0.0.0.0',  // 监听所有网络接口，允许外部访问
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8001',  // 使用 127.0.0.1 确保指向本地服务器
        changeOrigin: true,
        ws: true,
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // 添加日志用于调试
            console.log('Proxying:', req.method, req.url, '→', options.target + proxyReq.path)
          })
        }
      }
    }
  }
})
