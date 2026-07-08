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

            <el-table-column label="文件名" min-width="200">
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
                <el-tag size="small" type="info">
                  {{ row.file_type.toUpperCase() }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="file_size_readable" label="大小" width="120" align="right" />

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
      width="400px"
    >
      <el-form :model="restoreForm" label-width="80px">
        <el-form-item label="恢复到">
          <el-select v-model="restoreForm.folder_id" placeholder="选择目标文件夹">
            <el-option label="根目录" :value="0" />
            <!-- TODO: 添加文件夹树选择 -->
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="restoreDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmRestore">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import {
  getTrashList,
  restoreFile,
  permanentDelete,
  clearTrash
} from '@/api/trash'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Delete,
  DeleteFilled,
  RefreshLeft,
  Document,
  Picture,
  Headset,
  Files
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
  folder_id: 0
})

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

// 恢复文件
const handleRestore = (file) => {
  restoreForm.value = {
    id: file.id,
    folder_id: file.original_folder_id || 0
  }
  restoreDialogVisible.value = true
}

// 确认恢复
const handleConfirmRestore = async () => {
  try {
    const res = await restoreFile(restoreForm.value.id)
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

  ElMessageBox.confirm(
    `确定要恢复选中的 ${selectedFiles.value.length} 个文件吗？`,
    '批量恢复',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      // 逐个恢复
      for (const file of selectedFiles.value) {
        await restoreFile(file.id)
      }
      ElMessage.success('批量恢复成功')
      await loadTrashList()
      selectedFiles.value = []
    } catch (error) {
      ElMessage.error('批量恢复失败')
    }
  }).catch(() => {})
}

// 永久删除
const handlePermanentDelete = (file) => {
  ElMessageBox.confirm(
    `确定要永久删除"${file.original_name}"吗？永久删除后将无法恢复！`,
    '永久删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    }
  ).then(async () => {
    try {
      await permanentDelete(file.id)
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
    `确定要永久删除选中的 ${selectedFiles.value.length} 个文件吗？永久删除后将无法恢复！`,
    '批量永久删除',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'error'
    }
  ).then(async () => {
    try {
      // 逐个删除
      for (const file of selectedFiles.value) {
        await permanentDelete(file.id)
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
    '确定要清空回收站吗？清空后所有文件将被永久删除，无法恢复！',
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
