import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' }
})

// Request interceptor — inject token
service.interceptors.request.use(
  (config) => {
    const token = (localStorage.getItem('token') || '').trim()
    if (token) {
      config.headers.Authorization = token
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor — unwrap data, handle errors
service.interceptors.response.use(
  (response) => {
    const res = response.data
    // Java backend wraps in { code, message, data }
    if (res.code !== undefined && res.code !== 200) {
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || '请求失败'))
    }
    return res
  },
  (error) => {
    const status = error.response?.status
    if (status === 401) {
      localStorage.removeItem('token')
      ElMessage.warning('登录已过期，请重新登录')
      router.push('/login')
    } else if (status === 403) {
      ElMessage.error('没有权限执行此操作')
    } else if (status >= 500) {
      ElMessage.error('服务器错误，请稍后重试')
    } else {
      ElMessage.error(error.message || '网络异常')
    }
    return Promise.reject(error)
  }
)

export default service
