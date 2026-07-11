/**
 * Axios 请求封装 - 统一拦截器、错误处理、Token 注入
 */
import axios, { type InternalAxiosRequestConfig, type AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// ===== 请求拦截器: 注入 JWT Token =====
request.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ===== 响应拦截器: 统一处理响应与错误 =====
request.interceptors.response.use(
  async (response: AxiosResponse) => {
    // blob 响应 (文件下载): 直接返回原始数据; 若后端返回的是 JSON 错误则解析提示
    if (response.config.responseType === 'blob') {
      if (response.data instanceof Blob && response.data.type.includes('application/json')) {
        const text = await response.data.text()
        try {
          const err = JSON.parse(text)
          ElMessage.error(err.message || '导出失败')
          return Promise.reject(new Error(err.message || '导出失败'))
        } catch {
          // 非 JSON, 当作正常文件流
        }
      }
      return response.data
    }
    const res = response.data
    // 后端统一响应格式: { code, message, data, trace_id }
    if (res.code !== undefined && res.code !== 0) {
      ElMessage.error(res.message || '请求失败')
      // 1002=未认证, 跳转登录
      if (res.code === 1002) {
        localStorage.removeItem('access_token')
        window.location.href = '/login'
      }
      return Promise.reject(new Error(res.message || 'Error'))
    }
    return res
  },
  (error) => {
    const msg = error.response?.data?.message || error.message || '网络异常'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export default request
