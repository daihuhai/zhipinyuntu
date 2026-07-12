/**
 * Axios 请求封装 - 统一拦截器、错误处理、Token 注入
 * 增强: 请求去重、GET 请求重试
 * 注: 全屏 loading 已移除, 避免耗时操作 (简历解析/匹配) 时遮罩整个页面
 *      各页面自行使用 v-loading 或局部 loading 控制加载状态
 */
import axios, { type InternalAxiosRequestConfig, type AxiosResponse, type AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 600000,  // 简历解析等耗时操作需 10 分钟
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
  (error) => {
    return Promise.reject(error)
  }
)

// ===== 响应拦截器: 统一处理响应与错误 + GET 重试 =====
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
  async (error: AxiosError & { __reused?: boolean; promise?: Promise<any> }) => {
    // 请求去重: 复用已有请求结果
    if (error.__reused && error.promise) {
      return error.promise
    }
    // GET 请求网络错误自动重试 1 次
    const config = error.config as InternalAxiosRequestConfig & { __retried?: boolean }
    if (
      config &&
      config.method === 'get' &&
      !config.__retried &&
      (error.code === 'NETWORK_ERROR' || error.code === 'ECONNABORTED' || error.response?.status === 502)
    ) {
      config.__retried = true
      return request(config)
    }
    const msg = (error.response?.data as any)?.message || error.message || '网络异常'
    if (error.response?.status !== 429) {
      ElMessage.error(msg)
    } else {
      ElMessage.warning('请求过于频繁, 请稍后再试')
    }
    return Promise.reject(error)
  }
)

export default request
