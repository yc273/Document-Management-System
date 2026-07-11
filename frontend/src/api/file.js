/**
 * 文档API
 */
import request from '@/utils/request'

/**
 * 上传文档
 */
export function uploadFile(file, folderId = 0) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('folder_id', folderId)

  return request({
    url: '/file/upload',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    },
    onUploadProgress: progressEvent => {
      const percentCompleted = Math.floor((progressEvent.loaded * 100) / progressEvent.total)
      return percentCompleted
    }
  })
}

/**
 * 分片上传 - 检查（秒传/断点续传）
 */
export function checkUpload(data) {
  return request({
    url: '/file/upload/check',
    method: 'post',
    data
  })
}

/**
 * 分片上传 - 上传单个分片
 */
export function uploadChunk(formData, onProgress) {
  return request({
    url: '/file/upload/chunk',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: onProgress
  })
}

/**
 * 分片上传 - 合并分片
 */
export function mergeUpload(data) {
  return request({
    url: '/file/upload/merge',
    method: 'post',
    data
  })
}

/**
 * 获取文档列表
 */
export function getFileList(params) {
  return request({
    url: '/file/list',
    method: 'get',
    params
  })
}

/**
 * 获取文档详情
 */
export function getFile(id) {
  return request({
    url: `/file/${id}`,
    method: 'get'
  })
}

/**
 * 修改文档信息
 */
export function updateFile(id, data) {
  return request({
    url: `/file/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除文档（移入回收站）
 */
export function deleteFile(id) {
  return request({
    url: `/file/${id}`,
    method: 'delete'
  })
}

/**
 * 移动文档
 */
export function moveFile(data) {
  return request({
    url: '/file/move',
    method: 'post',
    data
  })
}

/**
 * 下载文档
 */
export function downloadFile(id) {
  return `/api/file/download/${id}`
}

/**
 * 预览文档
 */
export function previewFile(id) {
  return `/api/file/preview/${id}`
}

/**
 * 搜索文档
 */
export function searchFiles(data) {
  return request({
    url: '/file/search',
    method: 'post',
    data
  })
}

/**
 * 批量删除文档
 */
export function batchDeleteFile(data) {
  return request({
    url: '/file/batch-delete',
    method: 'post',
    data
  })
}

/**
 * 批量下载文档（打包为ZIP）
 * 注意：返回的是二进制流，不走统一的JSON响应拦截器
 */
export function batchDownloadFile(data) {
  return request({
    url: '/file/batch-download',
    method: 'post',
    data,
    responseType: 'blob'
  })
}
