/**
 * 统计API
 */
import request from '@/utils/request'

/**
 * 获取仪表板数据
 */
export function getDashboard() {
  return request({
    url: '/stat/dashboard',
    method: 'get'
  })
}

/**
 * 获取存储统计
 */
export function getStorageStats() {
  return request({
    url: '/stat/storage',
    method: 'get'
  })
}

/**
 * 获取上传统计
 */
export function getUploadStats(days = 7) {
  return request({
    url: '/stat/upload',
    method: 'get',
    params: { days }
  })
}

/**
 * 获取操作日志
 */
export function getLogs(params) {
  return request({
    url: '/stat/log',
    method: 'get',
    params
  })
}

/**
 * 获取日志统计
 */
export function getLogStats(days = 7) {
  return request({
    url: '/stat/log',
    method: 'get',
    params: { days }
  })
}
