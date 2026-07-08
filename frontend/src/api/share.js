/**
 * 分享API
 */
import request from '@/utils/request'

/**
 * 创建分享
 */
export function createShare(data) {
  return request({
    url: '/share/create',
    method: 'post',
    data
  })
}

/**
 * 获取分享列表
 */
export function getShareList(params) {
  return request({
    url: '/share/list',
    method: 'get',
    params
  })
}

/**
 * 获取分享详情
 */
export function getShare(shareCode) {
  return request({
    url: `/share/${shareCode}`,
    method: 'get'
  })
}

/**
 * 验证分享密码
 */
export function verifyShare(shareCode, data) {
  return request({
    url: `/share/${shareCode}/verify`,
    method: 'post',
    data
  })
}

/**
 * 取消分享
 */
export function cancelShare(id) {
  return request({
    url: `/share/${id}`,
    method: 'delete'
  })
}

/**
 * 获取分享访问统计
 */
export function getShareStats(id) {
  return request({
    url: `/share/stats/${id}`,
    method: 'get'
  })
}
