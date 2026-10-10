import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000
})

// 请求拦截：带上token
service.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 响应拦截，处理401鉴权失效
service.interceptors.response.use(
  res => res.data,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      location.href = '/login'
      ElMessage.warning('登录已过期，请重新登录')
    } else {
      ElMessage.error(err.response?.data?.detail || '请求失败')
    }
    return Promise.reject(err)
  }
)
export default service
