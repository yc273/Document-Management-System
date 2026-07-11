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
 * @param id 文档ID
 * @param data 可选，{ folder_id: 目标文件夹ID }
 */
export function restoreFile(id, data) {
  return request({
    url: `/trash/restore/${id}`,
    method: 'post',
    data
  })
}

/**
 * 恢复文件夹（整体级联恢复）
 */
export function restoreFolder(id) {
  return request({
    url: `/trash/restore-folder/${id}`,
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
 * 永久删除文件夹（级联删除）
 */
export function permanentDeleteFolder(id) {
  return request({
    url: `/trash/delete-folder/${id}`,
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
