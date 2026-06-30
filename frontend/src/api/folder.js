/**
 * 文件夹API
 */
import request from '@/utils/request'

/**
 * 获取文件夹列表
 */
export function getFolderList() {
  return request({
    url: '/folder/list',
    method: 'get'
  })
}

/**
 * 创建文件夹
 */
export function createFolder(data) {
  return request({
    url: '/folder',
    method: 'post',
    data
  })
}

/**
 * 获取文件夹详情
 */
export function getFolder(id) {
  return request({
    url: `/folder/${id}`,
    method: 'get'
  })
}

/**
 * 修改文件夹
 */
export function updateFolder(id, data) {
  return request({
    url: `/folder/${id}`,
    method: 'put',
    data
  })
}

/**
 * 删除文件夹
 */
export function deleteFolder(id) {
  return request({
    url: `/folder/${id}`,
    method: 'delete'
  })
}

/**
 * 移动文件夹
 */
export function moveFolder(data) {
  return request({
    url: '/folder/move',
    method: 'post',
    data
  })
}

/**
 * 获取文件夹文档列表
 */
export function getFolderFiles(id) {
  return request({
    url: `/folder/${id}/files`,
    method: 'get'
  })
}

/**
 * 获取面包屑
 */
export function getBreadcrumb(id) {
  return request({
    url: `/folder/breadcrumb/${id}`,
    method: 'get'
  })
}
