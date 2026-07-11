<template>
  <div class="trash">
    <el-card class="trash-card">
      <!-- 头部工具栏 -->
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Delete /></el-icon>
            <span class="title">回收站</span>
            <el-tag v-if="total > 0" type="info" size="small">
              {{ total }} 项
            </el-tag>
          </div>
          <div class="header-right">
            <el-button
              v-if="fileList.length > 0"
              type="danger"
              size="small"
              @click="handleClearTrash"
            >
              <el-icon><DeleteFilled /></el-icon>
              清空回收站
            </el-button>
          </div>
        </div>
      </template>

      <!-- 文件列表 -->
      <div class="trash-content">
        <!-- 空状态 -->
        <el-empty
          v-if="!loading && fileList.length === 0"
          description="回收站为空"
        >
          <template #image>
            <el-icon :size="100" color="#c0c4cc">
              <Delete />
            </el-icon>
          </template>
        </el-empty>

        <!-- 文件列表 -->
        <div v-else class="file-list">
          <el-table
            :data="fileList"
            v-loading="loading"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="55" />

            <el-table-column label="名称" min-width="200">
              <template #default="{ row }">
                <div class="file-name-cell">
                  <el-icon :size="24" :color="row.item_type === 'folder' ? '#E6A23C' : getFileIconColor(row.file_type)">
                    <Folder v-if="row.item_type === 'folder'" />
                    <component v-else :is="getFileIcon(row.file_type)" />
                  </el-icon>
                  <span class="file-name">{{ row.item_type === 'folder' ? row.name : row.original_name }}</span>
                  <el-tag v-if="row.item_type === 'folder'" size="small" type="warning" style="margin-left: 6px">
                    文件夹
                  </el-tag>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag v-if="row.item_type === 'folder'" size="small" type="warning">文件夹</el-tag>
                <el-tag v-else size="small" type="info">
                  {{ row.file_type ? row.file_type.toUpperCase() : '-' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="大小/内容" width="120" align="right">
              <template #default="{ row }">
                <span v-if="row.item_type === 'folder'">{{ row.inner_file_count || 0 }} 个文件</span>
                <span v-else>{{ row.file_size_readable }}</span>
              </template>
            </el-table-column>

            <el-table-column prop="deleted_at" label="删除时间" width="180" align="center">
              <template #default="{ row }">
                {{ formatDate(row.deleted_at) }}
              </template>
            </el-table-column>

            <el-table-column prop="expire_days" label="保留天数" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="getExpireTagType(row.expire_days)"
                  size="small"
                >
                  {{ row.expire_days }} 天
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="200" fixed="right" align="center">
              <template #default="{ row }">
                <el-button-group>
                  <el-button
                    type="success"
                    size="small"
                    link
                    @click="handleRestore(row)"
                  >
                    <el-icon><RefreshLeft /></el-icon>
                    恢复
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="handlePermanentDelete(row)"
                  >
                    <el-icon><DeleteFilled /></el-icon>
                    永久删除
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <!-- 批量操作栏 -->
          <div v-if="selectedFiles.length > 0" class="batch-actions">
            <div class="selected-info">
              已选择 <strong>{{ selectedFiles.length }}</strong> 项
            </div>
            <div class="batch-buttons">
              <el-button
                type="success"
                size="small"
                @click="handleBatchRestore"
              >
                <el-icon><RefreshLeft /></el-icon>
                批量恢复
              </el-button>
              <el-button
                type="danger"
                size="small"
                @click="handleBatchDelete"
              >
                <el-icon><DeleteFilled /></el-icon>
                批量永久删除
              </el-button>
            </div>
          </div>

          <!-- 分页 -->
          <div class="pagination">
            <el-pagination
              v-model:current-page="currentPage"
              v-model:page-size="pageSize"
              :total="total"
              :page-sizes="[10, 20, 50, 100]"
              layout="total, sizes, prev, pager, next, jumper"
              @size-change="handleSizeChange"
              @current-change="handleCurrentChange"
            />
          </div>
        </div>
      </div>
    </el-card>

    <!-- 恢复位置选择对话框 -->
    <el-dialog
      v-model="restoreDialogVisible"
      title="选择恢复位置"
      width="450px"
    >
      <el-form :model="restoreForm" label-width="80px">
        <el-form-item label="文件名">
          <span class="restore-file-name">{{ restoreForm.fileName }}</span>
        </el-form-item>
        <el-form-item v-if="restoreForm.originalFolderName" label="原位置">
          <el-tag :type="restoreForm.originalFolderExists ? 'info' : 'danger'" size="small">
            {{ restoreForm.originalFolderName }}
            <span v-if="!restoreForm.originalFolderExists">（已删除）</span>
          </el-tag>
        </el-form-item>
        <el-form-item label="恢复到">
          <el-tree-select
            v-model="restoreForm.folder_id"
            :data="folderTreeData"
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
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="restoreDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmRestore">确定恢复</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getTrashList,
  restoreFile,
  restoreFolder,
  permanentDelete,
  permanentDeleteFolder,
  clearTrash
} from '@/api/trash'
import { getFolderList } from '@/api/folder'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete,
  DeleteFilled,
  RefreshLeft,
  Document,
  Picture,
  Headset,
  Files,
  Folder
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

// 数据
const loading = ref(false)
const fileList = ref([])
const selectedFiles = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 恢复对话框
const restoreDialogVisible = ref(false)
const restoreForm = ref({
  id: null,
  folder_id: 0,
  fileName: '',
  originalFolderName: '',
  originalFolderExists: true
})
// 文件夹树（用于恢复时选择目标位置）
const folderTreeData = ref([])
// 文件夹ID -> 名称 的扁平映射，用于查找原文件夹名
const folderNameMap = ref({})

// 将树形数据扁平化成 { id: name } 映射
const buildFolderNameMap = (nodes, map = {}) => {
  for (const node of nodes || []) {
    map[node.id] = node.name
    if (node.children && node.children.length) {
      buildFolderNameMap(node.children, map)
    }
  }
  return map
}

// 深度优先取出文件夹树中的第一个文件夹ID（即"全部文件"下的第一个）
const getFirstFolderId = (nodes) => {
  for (const node of nodes || []) {
    if (node.id) return node.id
    if (node.children && node.children.length) {
      const found = getFirstFolderId(node.children)
      if (found) return found
    }
  }
  return null
}

// 加载文件夹树
const loadFolderTree = async () => {
  try {
    const res = await getFolderList()
    if (res.code === 200) {
      folderTreeData.value = res.data.folders || []
      folderNameMap.value = buildFolderNameMap(folderTreeData.value)
    }
  } catch (e) {
    console.error('加载文件夹列表失败:', e)
  }
}

// 加载回收站列表
const loadTrashList = async () => {
  loading.value = true
  try {
    const res = await getTrashList({
      page: currentPage.value,
      per_page: pageSize.value
    })
    if (res.code === 200) {
      fileList.value = res.data.files || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载回收站列表失败:', error)
    ElMessage.error('加载回收站列表失败')
  } finally {
    loading.value = false
  }
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedFiles.value = selection
}

// 恢复（根据 item_type 路由）
const handleRestore = async (row) => {
  // 文件夹：整体恢复（不需要选目标位置，恢复到原父文件夹，不在则回根目录）
  if (row.item_type === 'folder') {
    try {
      const res = await restoreFolder(row.id)
      if (res.code === 200) {
        ElMessage.success('文件夹已恢复')
        await loadTrashList()
        selectedFiles.value = []
      }
    } catch (error) {
      ElMessage.error('恢复失败')
    }
    return
  }

  // 文件：走原有的选目标文件夹流程
  if (folderTreeData.value.length === 0) {
    await loadFolderTree()
  }

  // 没有任何文件夹时，无法恢复（文件必须放到某个文件夹下）
  const firstFolderId = getFirstFolderId(folderTreeData.value)
  if (!firstFolderId) {
    ElMessage.warning('请先创建文件夹后再恢复文件')
    return
  }

  const originalFolderId = row.original_folder_id || 0
  const originalExists = row.original_folder_exists !== false &&
    folderNameMap.value[originalFolderId] !== undefined

  // 默认恢复到原位置（若原文件夹还在）；否则默认选第一个文件夹
  const defaultFolderId = originalExists ? originalFolderId : firstFolderId

  restoreForm.value = {
    id: row.id,
    fileName: row.original_name,
    folder_id: defaultFolderId,
    originalFolderName: originalFolderId === 0
      ? '根目录'
      : (folderNameMap.value[originalFolderId] || `文件夹#${originalFolderId}`),
    originalFolderExists: row.original_folder_exists !== false
  }
  restoreDialogVisible.value = true
}

// 确认恢复
const handleConfirmRestore = async () => {
  // 必须选择一个真实文件夹
  if (!restoreForm.value.folder_id) {
    ElMessage.warning('请选择要恢复到的文件夹')
    return
  }
  try {
    const res = await restoreFile(restoreForm.value.id, {
      folder_id: restoreForm.value.folder_id
    })
    if (res.code === 200) {
      ElMessage.success('恢复成功')
      restoreDialogVisible.value = false
      await loadTrashList()
      selectedFiles.value = []
    }
  } catch (error) {
    ElMessage.error('恢复失败')
  }
}

// 批量恢复
const handleBatchRestore = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要恢复的文件')
    return
  }

  // 确保文件夹树已加载
  if (folderTreeData.value.length === 0) {
    await loadFolderTree()
  }
  // 没有文件夹则无法恢复（文件必须放到某个文件夹下）
  const firstFolderId = getFirstFolderId(folderTreeData.value)
  if (!firstFolderId) {
    ElMessage.warning('请先创建文件夹后再恢复文件')
    return
  }

  ElMessageBox.confirm(
    `确定要恢复选中的 ${selectedFiles.value.length} 项吗？`,
    '批量恢复',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      for (const item of selectedFiles.value) {
        if (item.item_type === 'folder') {
          // 文件夹整体恢复
          await restoreFolder(item.id)
        } else {
          // 文件：原文件夹还在则回原处，否则放到第一个文件夹
          const originalFolderId = item.original_folder_id || 0
          const originalExists = item.original_folder_exists !== false &&
            folderNameMap.value[originalFolderId] !== undefined
          const targetId = originalExists ? originalFolderId : firstFolderId
          await restoreFile(item.id, { folder_id: targetId })
        }
      }
      ElMessage.success('批量恢复成功')
      await loadTrashList()
      selectedFiles.value = []
    } catch (error) {
      ElMessage.error('批量恢复失败')
    }
  }).catch(() => {})
}

// 永久删除（根据 item_type 路由）
const handlePermanentDelete = (row) => {
  const isFolder = row.item_type === 'folder'
  const displayName = isFolder ? row.name : row.original_name
  const tip = isFolder
    ? `确定要永久删除文件夹"${displayName}"吗？文件夹内的所有文件也将被永久删除，无法恢复！`
    : `确定要永久删除"${displayName}"吗？永久删除后将无法恢复！`

  ElMessageBox.confirm(tip, '永久删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'error'
  }).then(async () => {
    try {
      if (isFolder) {
        await permanentDeleteFolder(row.id)
      } else {
        await permanentDelete(row.id)
      }
      ElMessage.success('永久删除成功')
      await loadTrashList()
      selectedFiles.value = []
    } catch (error) {
      ElMessage.error('永久删除失败')
    }
  }).catch(() => {})
}

// 批量永久删除
const handleBatchDelete = async () => {
  if (selectedFiles.value.length === 0) {
    ElMessage.warning('请先选择要删除的文件')
    return
  }

  ElMessageBox.confirm(
    `确定要永久删除选中的 ${selectedFiles.value.length} 项吗？永久删除后将无法恢复！`,
    '批量永久删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    }
  ).then(async () => {
    try {
      // 逐个删除：根据类型调用对应接口
      for (const item of selectedFiles.value) {
        if (item.item_type === 'folder') {
          await permanentDeleteFolder(item.id)
        } else {
          await permanentDelete(item.id)
        }
      }
      ElMessage.success('批量永久删除成功')
      await loadTrashList()
      selectedFiles.value = []
    } catch (error) {
      ElMessage.error('批量永久删除失败')
    }
  }).catch(() => {})
}

// 清空回收站
const handleClearTrash = () => {
  ElMessageBox.confirm(
    '确定要清空回收站吗？清空后所有文件和文件夹将被永久删除，无法恢复！',
    '清空回收站',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error',
      distinguishCancelAndClose: true
    }
  ).then(async () => {
    try {
      await clearTrash()
      ElMessage.success('回收站已清空')
      await loadTrashList()
    } catch (error) {
      ElMessage.error('清空回收站失败')
    }
  }).catch(() => {})
}

// 分页
const handleSizeChange = () => {
  currentPage.value = 1
  loadTrashList()
}

const handleCurrentChange = () => {
  loadTrashList()
}

// 获取文件图标
const getFileIcon = (fileType) => {
  const type = fileType?.toLowerCase() || ''
  const iconMap = {
    'pdf': Document,
    'doc': Document,
    'docx': Document,
    'jpg': Picture,
    'jpeg': Picture,
    'png': Picture,
    'gif': Picture,
    'mp3': Headset,
    'mp4': Files,  // Video图标不存在，用Files代替
    'zip': Files
  }
  return iconMap[type] || Document
}

// 获取文件图标颜色
const getFileIconColor = (fileType) => {
  const type = fileType?.toLowerCase() || ''
  const colorMap = {
    'pdf': '#F56C6C',
    'doc': '#409EFF',
    'docx': '#409EFF',
    'jpg': '#409EFF',
    'png': '#409EFF'
  }
  return colorMap[type] || '#909399'
}

// 获取过期标签类型
const getExpireTagType = (days) => {
  if (days <= 3) return 'danger'
  if (days <= 7) return 'warning'
  return 'success'
}

// 格式化日期
const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  loadTrashList()
})
</script>

<style scoped>
.trash {
  height: 100%;
  padding: 0;
}

.restore-file-name {
  font-weight: 600;
  color: #303133;
  word-break: break-all;
}

.trash-card {
  height: 100%;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.trash-card :deep(.el-card__header) {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.trash-card :deep(.el-card__body) {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  padding: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.header-left .title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.header-right {
  display: flex;
  gap: 10px;
}

.trash-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.file-list {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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

/* 分页 */
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

/* 响应式 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .batch-actions {
    flex-direction: column;
    gap: 10px;
  }

  .batch-buttons {
    width: 100%;
    flex-direction: column;
  }

  .batch-buttons .el-button {
    width: 100%;
  }
}
</style>
