/**
 * 回收站API
 */
import request from '@/utils/request'

/**
 * 获取回收站列表
 */
export function getTrashList(params) {
  return request({
    url: '/trash/list',
    method: 'get',
    params
  })
}

/**
 * 恢复文档
 */
export function restoreFile(id) {
  return request({
    url: `/trash/restore/${id}`,
    method: 'post'
  })
}

/**
 * 永久删除文档
 */
export function permanentDelete(id) {
  return request({
    url: `/trash/delete/${id}`,
    method: 'delete'
  })
}

/**
 * 清空回收站
 */
export function clearTrash() {
  return request({
    url: '/trash/clear',
    method: 'delete'
  })
}
