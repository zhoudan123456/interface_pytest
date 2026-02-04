/**
 * Axios配置
 */
import axios from 'axios'
import type { ApiResponse } from '@/types'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 600000, // 10分钟超时（LLM匹配可能需要较长时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 如果是FormData，删除Content-Type让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default apiClient
