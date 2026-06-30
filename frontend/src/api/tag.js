/**
 * 标签API
 */
import request from '@/utils/request'

/**
 * 获取标签列表
 */
export function getTagList() {
  return request({
    url: '/tag/list',
    method: 'get'
  })
}

/**
 * 创建标签
 */
export function createTag(data) {
  return request({
    url: '/tag',
    method: 'post',
    data
  })
}

/**
 * 修改标签
 */
export function updateTag(id, data) {
  return request({
    url: `/tag/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除标签
 */
export function deleteTag(id) {
  return request({
    url: `/tag/${id}`,
    method: 'delete'
  })
}

/**
 * 获取文档标签
 */
export function getFileTags(fileId) {
  return request({
    url: `/tag/file/${fileId}/tags`,
    method: 'get'
  })
}

/**
 * 为文档添加标签
 */
export function addFileTag(data) {
  return request({
    url: `/tag/file/${data.file_id}/tag`,
    method: 'post',
    data
  })
}

/**
 * 移除文档标签
 */
export function removeFileTag(fileId, tagId) {
  return request({
    url: `/tag/file/${fileId}/tag/${tagId}`,
    method: 'delete'
  })
}
