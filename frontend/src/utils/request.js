/**
 * Axios请求封装
 * 统一处理请求和响应
 */
import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const request = axios.create({
  baseURL: '/api',
  timeout: 30000,
  withCredentials: true,  // 支持跨域携带cookie
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // Session-based authentication: 后端Flask-Login通过cookie管理session
    // 不需要手动添加Authorization header
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    // 二进制流响应（如文件下载）直接返回，不做JSON解析
    if (response.config.responseType === 'blob') {
      return response
    }

    const res = response.data

    // 如果响应码不是200，显示错误信息
    if (res.code !== 200) {
      ElMessage.error(res.message || '请求失败')

      // 401: 未授权，跳转登录页
      if (res.code === 401) {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }

      return Promise.reject(new Error(res.message || '请求失败'))
    }

    return res
  },
  error => {
    console.error('响应错误:', error)

    if (error.response) {
      const { status } = error.response

      switch (status) {
        case 401:
          ElMessage.error('未授权，请先登录')
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          window.location.href = '/login'
          break
        case 403:
          ElMessage.error('权限不足')
          break
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器错误')
          break
        default:
          ElMessage.error(error.response.data?.message || '请求失败')
      }
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

export default request
