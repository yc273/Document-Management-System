<template>
  <div class="file-manager">
    <el-row :gutter="20" class="manager-row">
      <!-- 左侧文件夹树 -->
      <el-col :xs="24" :sm="24" :md="6" :lg="5" :xl="4" class="folder-col"
        v-show="!isMobileView || showMobileTree">
        <el-card class="folder-card">
          <FolderTree
            ref="folderTreeRef"
            @select="handleFolderSelect"
            @refresh="handleFolderRefresh"
          />
        </el-card>
      </el-col>

      <!-- 右侧文件列表 -->
      <el-col :xs="24" :sm="24" :md="18" :lg="19" :xl="20" class="file-col">
        <el-card class="file-card">
          <!-- 面包屑导航 -->
          <div class="breadcrumb-bar" v-if="breadcrumbList.length > 0">
            <el-button
              v-if="isMobileView && !showMobileTree"
              class="mobile-back-btn"
              text
              @click="goBackToFolders"
            >
              <el-icon><ArrowLeft /></el-icon>
              <span>文件夹</span>
            </el-button>
            <el-breadcrumb separator="/">
              <el-breadcrumb-item
                v-for="item in breadcrumbList"
                :key="item.id"
                @click="handleBreadcrumbClick(item)"
              >
                <el-icon><Folder /></el-icon>
                {{ item.name }}
              </el-breadcrumb-item>
            </el-breadcrumb>
          </div>

          <!-- 工具栏 -->
          <div class="toolbar">
            <div class="toolbar-left">
              <el-button type="primary" @click="handleUpload">
                <el-icon><Upload /></el-icon>
                上传文档
              </el-button>

              </div>

            <div class="toolbar-right">
              <!-- 视图切换 -->
              <el-button-group class="view-toggle">
                <el-button
                  :type="viewMode === 'list' ? 'primary' : ''"
                  @click="viewMode = 'list'"
                >
                  <el-icon><List /></el-icon>
                </el-button>
                <el-button
                  :type="viewMode === 'grid' ? 'primary' : ''"
                  @click="viewMode = 'grid'"
                >
                  <el-icon><Grid /></el-icon>
                </el-button>
              </el-button-group>

              <div class="search-box">
                <el-input
                  v-model="searchKeyword"
                  placeholder="搜索文档..."
                  clearable
                  @clear="handleSearch"
                  @keyup.enter="handleSearch"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
              </div>
            </div>
          </div>

          <!-- 列表视图 -->
          <div v-if="viewMode === 'list'" class="list-view" v-loading="loading">
            <el-table :data="fileList" style="width: 100%" @selection-change="handleSelectionChange">
              <el-table-column type="selection" width="55" />

              <el-table-column prop="original_name" label="文件名" min-width="200" show-overflow-tooltip>
                <template #default="{ row }">
                  <div class="file-name-cell">
                    <el-icon :size="24" :color="getFileIconColor(row.file_type)">
                      <component :is="getFileIcon(row.file_type)" />
                    </el-icon>
                    <span class="file-name">{{ row.original_name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="file_type" label="类型" width="100" align="center">
                <template #default="{ row }">
                  <el-tag size="small" :type="getFileTypeTagType(row.file_type)">
                    {{ row.file_type.toUpperCase() }}
                  </el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="file_size_readable" label="大小" width="120" align="right" />
              <el-table-column prop="created_at" label="上传时间" width="180" align="center" />
              <el-table-column label="操作" :width="isMobileView ? 300 : 320" :fixed="isMobileView ? false : 'right'" align="center" class-name="operations-col">
                <template #default="{ row }">
                  <el-button-group>
                    <el-button type="primary" size="small" link @click="handlePreview(row)">
                      <el-icon><View /></el-icon>
                      预览
                    </el-button>
                    <el-button type="primary" size="small" link @click="handleDownload(row)">
                      <el-icon><Download /></el-icon>
                      下载
                    </el-button>
                    <el-button type="success" size="small" link @click="handleShare(row)">
                      <el-icon><Share /></el-icon>
                      分享
                    </el-button>
                    <el-button type="info" size="small" link @click="handleRename(row)">
                      <el-icon><Edit /></el-icon>
                      重命名
                    </el-button>
                    <el-button type="danger" size="small" link @click="handleDelete(row)">
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-button>
                  </el-button-group>
                </template>
              </el-table-column>
            </el-table>
          </div>

          <!-- 网格视图 -->
          <div v-else class="grid-view" v-loading="loading">
            <div class="file-grid">
              <div
                v-for="file in fileList"
                :key="file.id"
                class="file-item"
                @click="handleFileClick(file)"
                @contextmenu.prevent="handleContextMenu($event, file)"
              >
                <div class="file-icon-wrapper">
                  <el-icon :size="48" :color="getFileIconColor(file.file_type)">
                    <component :is="getFileIcon(file.file_type)" />
                  </el-icon>
                </div>
                <div class="file-info">
                  <div class="file-name" :title="file.original_name">
                    {{ file.original_name }}
                  </div>
                  <div class="file-meta">
                    {{ file.file_size_readable }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <el-empty v-if="!loading && fileList.length === 0" description="暂无文档" />

          <!-- 批量操作栏 -->
          <div v-if="selectedFiles.length > 0" class="batch-actions">
            <div class="selected-info">
              已选择 <strong>{{ selectedFiles.length }}</strong> 个文件
            </div>
            <div class="batch-buttons">
              <el-button type="success" size="small" @click="handleBatchShare">
                <el-icon><Share /></el-icon>
                批量分享
              </el-button>
              <el-button type="primary" size="small" :loading="batchDownloading" @click="handleBatchDownload">
                <el-icon><Download /></el-icon>
                批量下载
              </el-button>
              <el-button type="info" size="small" @click="handleBatchMove">
                <el-icon><FolderOpened /></el-icon>
                移动
              </el-button>
              <el-button type="danger" size="small" @click="handleBatchDelete">
                <el-icon><Delete /></el-icon>
                批量删除
              </el-button>
            </div>
          </div>

          <!-- 分页 -->
          <div v-if="fileList.length > 0" class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[12, 24, 48, 96]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分享对话框 -->
    <ShareDialog
      v-model="shareDialogVisible"
      :file-info="selectedFile"
      @success="handleShareSuccess"
    />

    <!-- 预览对话框 -->
    <FilePreview
      v-model:visible="previewVisible"
      :file="previewFile"
    />

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadVisible" title="上传文档" width="560px" @close="handleUploadClose">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="uploadFileList"
        drag
        multiple
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持多种文件格式。小于 20MB 走普通上传，大于 20MB 自动分片上传（支持断点续传）
          </div>
        </template>
      </el-upload>

      <!-- 上传进度区 -->
      <div v-if="uploadProgressList.length > 0" class="upload-progress-area">
        <div v-for="(item, idx) in uploadProgressList" :key="idx" class="upload-progress-item">
          <div class="upload-progress-name">
            <span>{{ item.name }}</span>
            <el-tag size="small" :type="item.status === 'done' ? 'success' : (item.status === 'error' ? 'danger' : 'info')">
              {{ item.statusText }}
            </el-tag>
          </div>
          <el-progress :percentage="item.percent" :status="item.status === 'done' ? 'success' : (item.status === 'error' ? 'exception' : '')" />
        </div>
      </div>

      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmUpload" :loading="uploading" :disabled="uploadFileList.length === 0">
          开始上传
        </el-button>
      </template>
    </el-dialog>

    <!-- 重命名对话框 -->
    <el-dialog v-model="renameVisible" title="重命名" width="400px">
      <el-form :model="renameForm" label-width="80px">
        <el-form-item label="文件名">
          <el-input v-model="renameForm.name" placeholder="请输入新文件名" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="renameVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- 移动文件对话框 -->
    <el-dialog v-model="moveVisible" title="移动到文件夹" width="450px">
      <p class="move-tip">将选中的 {{ moveForm.fileCount }} 个文件移动到：</p>
      <el-tree-select
        v-model="moveForm.targetFolderId"
        :data="moveFolderTreeData"
        :props="{ label: 'name', value: 'id', children: 'children' }"
        :render-after-expand="false"
        check-strictly
        node-key="id"
        placeholder="选择目标文件夹"
        style="width: 100%"
      >
        <template #default="{ data }">
          <span>
            <el-icon style="vertical-align: middle;"><Folder /></el-icon>
            {{ data.name }}
          </span>
        </template>
      </el-tree-select>
      <template #footer>
        <el-button @click="moveVisible = false">取消</el-button>
        <el-button type="primary" :loading="moving" @click="handleConfirmMove">确定移动</el-button>
      </template>
    </el-dialog>

    <!-- 右键菜单 -->
    <transition name="fade">
      <div
        v-if="contextMenuVisible"
        class="context-menu"
        :style="{ left: contextMenuPosition.x + 'px', top: contextMenuPosition.y + 'px' }"
      >
        <div class="context-menu-item" @click="handlePreview(contextMenuFile)">
          <el-icon><View /></el-icon>
          预览
        </div>
        <div class="context-menu-item" @click="handleDownload(contextMenuFile)">
          <el-icon><Download /></el-icon>
          下载
        </div>
        <div class="context-menu-item" @click="handleShare(contextMenuFile)">
          <el-icon><Share /></el-icon>
          分享
        </div>
        <div class="context-menu-item" @click="handleRename(contextMenuFile)">
          <el-icon><Edit /></el-icon>
          重命名
        </div>
        <div class="context-menu-item" @click="handleDelete(contextMenuFile)">
          <el-icon><Delete /></el-icon>
          删除
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { getFileList, deleteFile, downloadFile, updateFile, moveFile, batchDeleteFile, batchDownloadFile, uploadChunk, checkUpload, mergeUpload } from '@/api/file'
import { getBreadcrumb, getFolderList } from '@/api/folder'
import request from '@/utils/request'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Upload, FolderAdd, Search, Download, Delete, UploadFilled,
  List, Grid, Edit, Document, Folder, Picture, ArrowLeft,
  Headset, Files, Share, FolderOpened, View
} from '@element-plus/icons-vue'
import { useUserStore } from '@/store/user'
import FolderTree from '@/components/FolderTree.vue'
import ShareDialog from '@/components/ShareDialog.vue'
import FilePreview from '@/components/FilePreview.vue'

const userStore = useUserStore()

// 视图模式
const viewMode = ref('list') // list | grid

const loading = ref(false)
const fileList = ref([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const uploadVisible = ref(false)
const uploadRef = ref(null)
const uploading = ref(false)
const uploadData = ref({
  folder_id: 0
})
// 待上传文件列表（el-upload file-list）
const uploadFileList = ref([])
// 每个文件的上传进度
const uploadProgressList = ref([])

// 分片上传配置
const CHUNK_SIZE = 5 * 1024 * 1024      // 每片 5MB
const CHUNK_THRESHOLD = 20 * 1024 * 1024 // 超过 20MB 走分片上传
const CHUNK_CONCURRENCY = 3              // 分片并发数

// 文件夹相关
const folderTreeRef = ref(null)
const currentFolder = ref(null)
const breadcrumbList = ref([])

// 移动端：是否显示文件夹树（选择文件夹后自动隐藏）
const showMobileTree = ref(true)
const isMobileView = computed(() => window.innerWidth <= 768)

// 重命名
const renameVisible = ref(false)
const renameForm = ref({
  id: null,
  name: ''
})

// 右键菜单
const contextMenuVisible = ref(false)
const contextMenuPosition = ref({ x: 0, y: 0 })
const contextMenuFile = ref(null)

// 分享功能
const shareDialogVisible = ref(false)
const selectedFile = ref(null)
const selectedFiles = ref([])

// 批量下载状态
const batchDownloading = ref(false)

// 移动文件
const moveVisible = ref(false)
const moving = ref(false)
const moveForm = ref({
  fileIds: [],
  fileCount: 0,
  targetFolderId: null
})
const moveFolderTreeData = ref([])

// 预览功能
const previewVisible = ref(false)
const previewFile = ref(null)

// 加载文档列表
const loadFiles = async () => {
  loading.value = true
  try {
    const res = await getFileList({
      page: currentPage.value,
      per_page: pageSize.value,
      folder_id: uploadData.value.folder_id,
      keyword: searchKeyword.value.trim()
    })
    if (res.code === 200) {
      fileList.value = res.data.files || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载文档列表失败:', error)
    ElMessage.error('加载文档列表失败')
  } finally {
    loading.value = false
  }
}

// 加载面包屑
const loadBreadcrumb = async (folderId) => {
  if (!folderId || folderId === 0) {
    breadcrumbList.value = [
      { id: 0, name: '全部文件' }
    ]
    return
  }

  try {
    const res = await getBreadcrumb(folderId)
    if (res.code === 200) {
      breadcrumbList.value = [
        { id: 0, name: '全部文件' },
        ...(res.data.breadcrumb || [])
      ]
    }
  } catch (error) {
    console.error('加载面包屑失败:', error)
  }
}

// 文件夹选择
const handleFolderSelect = (folder) => {
  currentFolder.value = folder
  uploadData.value.folder_id = folder.id || 0
  currentPage.value = 1
  // 切换文件夹时清空搜索，避免残留关键词影响新文件夹列表
  searchKeyword.value = ''
  loadFiles()
  loadBreadcrumb(folder.id || 0)
  // 移动端选择文件夹后自动隐藏文件夹树，让文件列表占满全屏
  if (window.innerWidth <= 768) {
    showMobileTree.value = false
  }
}

// 移动端：返回文件夹树
const goBackToFolders = () => {
  showMobileTree.value = true
}

// 文件夹刷新
const handleFolderRefresh = (resetToRoot) => {
  if (resetToRoot === 0) {
    // 文件夹被删除，重置到根目录
    currentFolder.value = null
    uploadData.value.folder_id = 0
    breadcrumbList.value = [{ id: 0, name: '全部文件' }]
    if (folderTreeRef.value) {
      folderTreeRef.value.setCurrentKey(0)
    }
  }
  loadFiles()
}

// 面包屑点击
const handleBreadcrumbClick = (item) => {
  if (folderTreeRef.value) {
    folderTreeRef.value.setCurrentKey(item.id)
    handleFolderSelect(item)
  }
  // 移动端点击"全部文件"面包屑时返回文件夹树
  if (item.id === 0 && window.innerWidth <= 768) {
    showMobileTree.value = true
  }
}

// 搜索
const handleSearch = async () => {
  if (!searchKeyword.value.trim()) {
    loadFiles()
    return
  }

  loading.value = true
  try {
    const res = await getFileList({
      folder_id: uploadData.value.folder_id,
      keyword: searchKeyword.value,
      page: 1,
      per_page: pageSize.value
    })
    if (res.code === 200) {
      fileList.value = res.data.files || []
      total.value = res.data.total || 0
      currentPage.value = 1
    }
  } catch (error) {
    console.error('搜索失败:', error)
    ElMessage.error('搜索失败')
  } finally {
    loading.value = false
  }
}

// 上传文档
const handleUpload = () => {
  uploadRef.value?.clearFiles()
  uploadVisible.value = true
}

// el-upload 文件选择变化（手动管理模式）
const handleFileChange = (file, fileList) => {
  uploadFileList.value = fileList
}

// el-upload 移除文件
const handleFileRemove = (file, fileList) => {
  uploadFileList.value = fileList
}

// 上传对话框关闭时清理
const handleUploadClose = () => {
  uploadFileList.value = []
  uploadProgressList.value = []
  uploadRef.value?.clearFiles()
}

// 计算文件 MD5（使用 FileReader + spark-md5 不可用时，用简易 hash 替代：文件名+大小+修改时间）
// 注：为避免引入额外依赖，用 size+name+lastModified 生成标识。生产可用 spark-md5 替换。
const calcFileHash = async (file) => {
  const info = `${file.name}_${file.size}_${file.lastModified}`
  // 简单字符串 hash → 作为分片目录标识
  let hash = 0
  for (let i = 0; i < info.length; i++) {
    const ch = info.charCodeAt(i)
    hash = ((hash << 5) - hash) + ch
    hash |= 0
  }
  return 'h' + Math.abs(hash).toString(16) + file.size.toString(16)
}

// 确认上传：逐个文件处理
const handleConfirmUpload = async () => {
  if (uploadFileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  // 初始化进度列表
  uploadProgressList.value = uploadFileList.value.map(f => ({
    name: f.name,
    percent: 0,
    status: 'uploading',
    statusText: '等待中'
  }))

  let successCount = 0
  for (let i = 0; i < uploadFileList.value.length; i++) {
    const rawFile = uploadFileList.value[i].raw
    try {
      if (rawFile.size >= CHUNK_THRESHOLD) {
        await uploadInChunks(rawFile, i)
      } else {
        await uploadSingle(rawFile, i)
      }
      successCount++
    } catch (err) {
      console.error(`上传 ${rawFile.name} 失败:`, err)
      uploadProgressList.value[i].status = 'error'
      uploadProgressList.value[i].statusText = '失败'
    }
  }

  uploading.value = false
  if (successCount > 0) {
    ElMessage.success(`上传完成，成功 ${successCount} 个文件`)
    loadFiles()
    folderTreeRef.value?.refresh()
  }
  // 全部成功则关闭对话框
  if (successCount === uploadFileList.value.length) {
    uploadVisible.value = false
    handleUploadClose()
  }
}

// 普通单次上传（< 20MB）
const uploadSingle = async (file, progressIndex) => {
  uploadProgressList.value[progressIndex].statusText = '上传中...'
  const formData = new FormData()
  formData.append('file', file)
  formData.append('folder_id', uploadData.value.folder_id)

  await request({
    url: '/file/upload',
    method: 'post',
    data: formData,
    headers: { 'Content-Type': 'multipart/form-data' },
    withCredentials: true,
    onUploadProgress: (e) => {
      if (e.total) {
        uploadProgressList.value[progressIndex].percent = Math.floor(e.loaded * 100 / e.total)
      }
    }
  })
  uploadProgressList.value[progressIndex].percent = 100
  uploadProgressList.value[progressIndex].status = 'done'
  uploadProgressList.value[progressIndex].statusText = '完成'
}

// 分片上传（>= 20MB）
const uploadInChunks = async (file, progressIndex) => {
  const fileHash = await calcFileHash(file)
  const totalChunks = Math.ceil(file.size / CHUNK_SIZE)

  // 更新状态文本
  uploadProgressList.value[progressIndex].statusText = '检查中...'

  // 1. check：秒传 / 断点续传 / 全新
  const checkRes = await checkUpload({
    file_hash: fileHash,
    file_size: file.size,
    filename: file.name,
    folder_id: uploadData.value.folder_id
  })

  if (checkRes.data.status === 'skip') {
    // 秒传成功
    uploadProgressList.value[progressIndex].percent = 100
    uploadProgressList.value[progressIndex].status = 'done'
    uploadProgressList.value[progressIndex].statusText = '秒传完成'
    return
  }

  // 确定需要上传的分片序号
  let chunksToUpload = []
  for (let i = 0; i < totalChunks; i++) chunksToUpload.push(i)
  if (checkRes.data.status === 'resume') {
    const uploaded = new Set(checkRes.data.uploaded_chunks || [])
    chunksToUpload = chunksToUpload.filter(i => !uploaded.has(i))
  }

  uploadProgressList.value[progressIndex].statusText = `分片上传 0/${chunksToUpload.length}`

  // 2. 并发上传分片
  let completedCount = 0
  const totalToUpload = chunksToUpload.length
  let cursor = 0

  const uploadOneChunk = async () => {
    while (cursor < chunksToUpload.length) {
      const chunkIndex = chunksToUpload[cursor++]
      const start = chunkIndex * CHUNK_SIZE
      const end = Math.min(start + CHUNK_SIZE, file.size)
      const blob = file.slice(start, end)

      const formData = new FormData()
      formData.append('file', blob)
      formData.append('file_hash', fileHash)
      formData.append('chunk_index', chunkIndex)
      formData.append('total_chunks', totalChunks)

      await uploadChunk(formData)
      completedCount++
      const pct = Math.floor(completedCount * 100 / totalToUpload)
      uploadProgressList.value[progressIndex].percent = pct
      uploadProgressList.value[progressIndex].statusText = `分片上传 ${completedCount}/${totalToUpload}`
    }
  }

  // 启动并发
  const workers = []
  for (let i = 0; i < CHUNK_CONCURRENCY; i++) {
    workers.push(uploadOneChunk())
  }
  await Promise.all(workers)

  // 3. merge
  uploadProgressList.value[progressIndex].statusText = '合并中...'
  await mergeUpload({
    file_hash: fileHash,
    filename: file.name,
    file_size: file.size,
    folder_id: uploadData.value.folder_id
  })
  uploadProgressList.value[progressIndex].percent = 100
  uploadProgressList.value[progressIndex].status = 'done'
  uploadProgressList.value[progressIndex].statusText = '完成'
}

// 文件点击
const handleFileClick = (file) => {
  handlePreview(file)
}

// 预览文档
const handlePreview = (file) => {
  previewFile.value = file
  previewVisible.value = true
}

// 下载文档
const handleDownload = (file) => {
  const url = downloadFile(file.id)
  window.open(url, '_blank')
  closeContextMenu()
}

// 批量下载（打包为ZIP）
const handleBatchDownload = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要下载的文件')
    return
  }

  batchDownloading.value = true
  try {
    const fileIds = selectedFiles.value.map(f => f.id)
    const response = await batchDownloadFile({ file_ids: fileIds })
    // 从响应头获取文件名，没有则用默认名
    const disposition = response.headers['content-disposition'] || ''
    const match = disposition.match(/filename\*?=(?:UTF-8'')?(.*)$/i)
    let fileName = '批量下载.zip'
    if (match && match[1]) {
      fileName = decodeURIComponent(match[1].replace(/['"]/g, ''))
    }
    // 创建下载链接
    const blob = new Blob([response.data], { type: 'application/zip' })
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    ElMessage.success(`已打包下载 ${selectedFiles.value.length} 个文件`)
    selectedFiles.value = []
  } catch (error) {
    console.error('批量下载失败:', error)
    ElMessage.error('批量下载失败')
  } finally {
    batchDownloading.value = false
  }
}

// 重命名
const handleRename = (file) => {
  renameForm.value = {
    id: file.id,
    name: file.original_name
  }
  renameVisible.value = true
  closeContextMenu()
}

// 确认重命名
const handleConfirmRename = async () => {
  if (!renameForm.value.name.trim()) {
    ElMessage.warning('文件名不能为空')
    return
  }

  try {
    const res = await updateFile(renameForm.value.id, {
      original_name: renameForm.value.name
    })
    if (res.code === 200) {
      ElMessage.success('重命名成功')
      renameVisible.value = false
      loadFiles()
    }
  } catch (error) {
    ElMessage.error('重命名失败')
  }
}

// 删除文档
const handleDelete = (file) => {
  ElMessageBox.confirm(`确定要删除文档"${file.original_name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteFile(file.id)
      ElMessage.success('删除成功')
      loadFiles()
      folderTreeRef.value?.refresh()
      closeContextMenu()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {
    closeContextMenu()
  })
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedFiles.value = selection
}

// 分享文档
const handleShare = (file) => {
  selectedFile.value = file
  shareDialogVisible.value = true
  closeContextMenu()
}

// 批量分享
const handleBatchShare = () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要分享的文件')
    return
  }
  // 目前只支持单个文件分享，取第一个文件
  if (selectedFiles.value.length > 1) {
    ElMessage.info('目前只支持单个文件分享')
  }
  selectedFile.value = selectedFiles.value[0]
  shareDialogVisible.value = true
}

// 批量移动
// 移动文件
const handleBatchMove = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要移动的文件')
    return
  }

  // 加载文件夹树（用于选择目标位置）
  try {
    const res = await getFolderList()
    if (res.code === 200) {
      moveFolderTreeData.value = res.data.folders || []
    }
  } catch (e) {
    console.error('加载文件夹失败:', e)
    ElMessage.error('加载文件夹列表失败')
    return
  }

  // 没有任何文件夹时无法移动
  if (moveFolderTreeData.value.length === 0) {
    ElMessage.warning('当前没有可用的文件夹，请先创建文件夹')
    return
  }

  moveForm.value = {
    fileIds: selectedFiles.value.map(f => f.id),
    fileCount: selectedFiles.value.length,
    targetFolderId: null
  }
  moveVisible.value = true
}

// 确认移动
const handleConfirmMove = async () => {
  if (moveForm.value.targetFolderId === null) {
    ElMessage.warning('请选择目标文件夹')
    return
  }
  moving.value = true
  try {
    const res = await moveFile({
      file_ids: moveForm.value.fileIds,
      target_folder_id: moveForm.value.targetFolderId
    })
    if (res.code === 200) {
      ElMessage.success(`成功移动 ${moveForm.value.fileCount} 个文件`)
      moveVisible.value = false
      selectedFiles.value = []
      await loadFiles()
      folderTreeRef.value?.refresh()
    }
  } catch (error) {
    console.error('移动失败:', error)
  } finally {
    moving.value = false
  }
}

// 批量删除
const handleBatchDelete = () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要删除的文件')
    return
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedFiles.value.length} 个文件吗？`,
    '批量删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      const fileIds = selectedFiles.value.map(f => f.id)
      const res = await batchDeleteFile({ file_ids: fileIds })
      if (res.code === 200) {
        ElMessage.success('批量删除成功')
        selectedFiles.value = []
        loadFiles()
        folderTreeRef.value?.refresh()
      }
    } catch (error) {
      ElMessage.error('批量删除失败')
    }
  }).catch(() => {})
}

// 分享成功
const handleShareSuccess = () => {
  ElMessage.success('分享成功')
}

// 右键菜单
const handleContextMenu = (event, file) => {
  contextMenuFile.value = file
  contextMenuPosition.value = {
    x: event.clientX,
    y: event.clientY
  }
  contextMenuVisible.value = true
}

// 关闭右键菜单
const closeContextMenu = () => {
  contextMenuVisible.value = false
}

// 点击其他区域关闭右键菜单
const handleClickOutside = () => {
  closeContextMenu()
}

// 分页
const handleSizeChange = () => {
  currentPage.value = 1
  loadFiles()
}

const handleCurrentChange = () => {
  loadFiles()
}

// 获取文件图标
const getFileIcon = (fileType) => {
  const type = fileType.toLowerCase()
  const iconMap = {
    'pdf': Document,
    'doc': Document,
    'docx': Document,
    'xls': Document,
    'xlsx': Document,
    'ppt': Document,
    'pptx': Document,
    'txt': Document,
    'jpg': Picture,
    'jpeg': Picture,
    'png': Picture,
    'gif': Picture,
    'bmp': Picture,
    'svg': Picture,
    'webp': Picture,
    'mp3': Headset,
    'mp4': Files,  // Video图标不存在，用Files代替
    'avi': Files,
    'mkv': Files,
    'mov': Files,
    'wmv': Files,
    'zip': Files,
    'rar': Files,
    '7z': Files
  }
  return iconMap[type] || Document
}

// 获取文件图标颜色
const getFileIconColor = (fileType) => {
  const type = fileType.toLowerCase()
  const colorMap = {
    'pdf': '#F56C6C',
    'doc': '#409EFF',
    'docx': '#409EFF',
    'xls': '#67C23A',
    'xlsx': '#67C23A',
    'ppt': '#E6A23C',
    'pptx': '#E6A23C',
    'txt': '#909399',
    'jpg': '#409EFF',
    'jpeg': '#409EFF',
    'png': '#409EFF',
    'gif': '#409EFF',
    'bmp': '#409EFF',
    'svg': '#409EFF',
    'webp': '#409EFF',
    'mp3': '#F56C6C',
    'mp4': '#F56C6C',
    'avi': '#F56C6C',
    'mkv': '#F56C6C',
    'mov': '#F56C6C',
    'wmv': '#F56C6C',
    'zip': '#E6A23C',
    'rar': '#E6A23C',
    '7z': '#E6A23C'
  }
  return colorMap[type] || '#909399'
}

// 获取文件类型标签类型
const getFileTypeTagType = (fileType) => {
  const type = fileType.toLowerCase()
  const typeMap = {
    'pdf': 'danger',
    'doc': 'primary',
    'docx': 'primary',
    'xls': 'success',
    'xlsx': 'success',
    'ppt': 'warning',
    'pptx': 'warning',
    'jpg': 'info',
    'jpeg': 'info',
    'png': 'info',
    'gif': 'info'
  }
  return typeMap[type] || 'info'
}

onMounted(() => {
  // 初始化面包屑
  breadcrumbList.value = [{ id: 0, name: '全部文件' }]
  loadFiles()
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.file-manager {
  height: 100%;
  padding: 0;
}

.manager-row {
  height: 100%;
}

/* 文件夹树 */
.folder-col {
  height: 100%;
}

.folder-card {
  height: 100%;
  border-radius: 8px;
}

.folder-card :deep(.el-card__body) {
  height: 100%;
  padding: 0;
  overflow: hidden;
}

/* 文件列表 */
.file-col {
  height: 100%;
}

.file-card {
  height: 100%;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.file-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

/* 面包屑 */
.breadcrumb-bar {
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 15px;
}

.breadcrumb-bar :deep(.el-breadcrumb-item) {
  cursor: pointer;
}

.breadcrumb-bar :deep(.el-breadcrumb-item:hover .el-icon) {
  color: #409eff;
}

/* 工具栏 */
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding: 10px 0;
}

.toolbar-left {
  display: flex;
  gap: 10px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 15px;
}

.view-toggle {
  flex-shrink: 0;
}

.search-box {
  width: 300px;
}

/* 列表视图 */
.list-view {
  flex: 1;
  overflow: auto;
}

.file-name-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 网格视图 */
.grid-view {
  flex: 1;
  overflow: auto;
  padding: 10px 0;
}

.file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 20px;
  padding: 10px;
}

.file-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  background: #f5f7fa;
}

.file-item:hover {
  background: #e6f7ff;
  transform: translateY(-2px);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.file-icon-wrapper {
  margin-bottom: 10px;
}

.file-info {
  width: 100%;
  text-align: center;
}

.file-info .file-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-bottom: 5px;
}

.file-meta {
  font-size: 12px;
  color: #999;
}

/* 右键菜单 */
.context-menu {
  position: fixed;
  z-index: 9999;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  padding: 5px 0;
  min-width: 120px;
}

.context-menu-item {
  padding: 8px 15px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #606266;
  transition: all 0.3s;
}

.context-menu-item:hover {
  background: #f5f7fa;
  color: #409eff;
}

.context-menu-item .el-icon {
  font-size: 16px;
}

/* 分页 */
.pagination {
  margin-top: 20px;
  padding: 10px 0;
  display: flex;
  justify-content: flex-end;
  border-top: 1px solid #f0f0f0;
}

/* 批量操作栏 */
.batch-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 4px;
  margin-top: 15px;
}

.selected-info {
  font-size: 14px;
  color: #666;
}

.selected-info strong {
  color: #409eff;
  font-size: 16px;
}

.batch-buttons {
  display: flex;
  gap: 10px;
}

/* 上传对话框 */
.el-icon--upload {
  font-size: 67px;
  color: #c0c4cc;
  margin: 40px 0 16px;
  line-height: 50px;
}

.el-upload__tip {
  margin-top: 10px;
  color: #999;
  font-size: 12px;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 操作列按钮组 */
.operations-col :deep(.el-button-group) {
  white-space: nowrap;
}

/* 响应式 */
/* 移动端返回按钮 */
.mobile-back-btn {
  margin-bottom: 8px;
  padding: 0;
  font-size: 14px;
  color: #409eff;
}

.mobile-back-btn .el-icon {
  margin-right: 4px;
}

@media (max-width: 768px) {
  .manager-row {
    flex-direction: column;
  }

  .folder-col {
    width: 100% !important;
    height: 300px;
    margin-bottom: 20px;
  }

  .file-col {
    width: 100% !important;
    height: 100%;
  }

  /* 移动端表格横向滚动 */
  .list-view {
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }
  .list-view :deep(.el-table__body-wrapper) {
    overflow-x: auto;
    overflow-y: visible;
  }
  .list-view :deep(.el-table__header-wrapper) {
    overflow-x: auto;
  }
  .list-view :deep(.el-table) {
    width: auto;
    min-width: 100%;
  }
  .list-view :deep(.el-table__body-wrapper table),
  .list-view :deep(.el-table__header-wrapper table) {
    width: auto !important;
  }
  .toolbar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .toolbar-left {
    justify-content: center;
  }

  .toolbar-right {
    flex-direction: column;
    gap: 10px;
  }

  .search-box {
    width: 100%;
  }

  .file-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 15px;
  }
}

@media (max-width: 480px) {
  .file-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .toolbar-left {
    flex-direction: column;
  }
}

/* 移动提示 */
.move-tip {
  margin-bottom: 12px;
  font-size: 14px;
  color: #606266;
}

/* 上传进度区 */
.upload-progress-area {
  margin-top: 15px;
  max-height: 200px;
  overflow-y: auto;
}

.upload-progress-item {
  margin-bottom: 12px;
}

.upload-progress-name {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 13px;
  color: #606266;
}

.upload-progress-name span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 360px;
}
</style>
