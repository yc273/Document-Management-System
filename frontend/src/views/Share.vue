<template>
  <div class="share">
    <el-card class="share-card">
      <!-- 头部工具栏 -->
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <el-icon><Share /></el-icon>
            <span class="title">我的分享</span>
            <el-tag v-if="total > 0" type="info" size="small">
              {{ total }} 项
            </el-tag>
          </div>
          <div class="header-right">
            <el-button
              type="primary"
              size="small"
              @click="handleCreateShare"
            >
              <el-icon><Plus /></el-icon>
              创建分享
            </el-button>
          </div>
        </div>
      </template>

      <!-- 分享列表 -->
      <div class="share-content">
        <!-- 空状态 -->
        <el-empty
          v-if="!loading && shareList.length === 0"
          description="暂无分享"
        >
          <template #image>
            <el-icon :size="100" color="#c0c4cc">
              <Share />
            </el-icon>
          </template>
          <el-button type="primary" @click="handleCreateShare">
            创建第一个分享
          </el-button>
        </el-empty>

        <!-- 分享列表 -->
        <div v-else class="share-list">
          <el-table
            :data="shareList"
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
                  <div class="file-info">
                    <span class="file-name">{{ row.file_name }}</span>
                    <span class="share-link">{{ getShareLink(row.share_code) }}</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <el-table-column label="类型" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="!row.has_password ? 'success' : 'warning'" size="small">
                  {{ !row.has_password ? '公开' : '私密' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="访问次数" width="100" align="center">
              <template #default="{ row }">
                <div class="visit-count">
                  <el-icon><View /></el-icon>
                  {{ row.view_count || 0 }}
                </div>
              </template>
            </el-table-column>

            <el-table-column label="下载次数" width="100" align="center">
              <template #default="{ row }">
                <div class="download-count">
                  <el-icon><Download /></el-icon>
                  {{ row.download_count || 0 }}
                </div>
              </template>
            </el-table-column>

            <el-table-column label="创建时间" width="180" align="center">
              <template #default="{ row }">
                {{ formatDate(row.created_at) }}
              </template>
            </el-table-column>

            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="isExpired(row) ? 'danger' : 'success'"
                  size="small"
                >
                  {{ isExpired(row) ? '已过期' : '有效' }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column label="操作" width="250" fixed="right" align="center">
              <template #default="{ row }">
                <el-button-group>
                  <el-button
                    type="primary"
                    size="small"
                    link
                    @click="handleCopyLink(row)"
                  >
                    <el-icon><DocumentCopy /></el-icon>
                    复制链接
                  </el-button>
                  <el-button
                    type="info"
                    size="small"
                    link
                    @click="handleViewStats(row)"
                  >
                    <el-icon><DataAnalysis /></el-icon>
                    统计
                  </el-button>
                  <el-button
                    type="danger"
                    size="small"
                    link
                    @click="handleCancelShare(row)"
                  >
                    <el-icon><Delete /></el-icon>
                    取消
                  </el-button>
                </el-button-group>
              </template>
            </el-table-column>
          </el-table>

          <!-- 批量操作栏 -->
          <div v-if="selectedShares.length > 0" class="batch-actions">
            <div class="selected-info">
              已选择 <strong>{{ selectedShares.length }}</strong> 项
            </div>
            <div class="batch-buttons">
              <el-button
                type="danger"
                size="small"
                @click="handleBatchCancel"
              >
                <el-icon><Delete /></el-icon>
                批量取消
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

    <!-- 创建分享对话框 -->
    <ShareDialog
      v-model="shareDialogVisible"
      :file-info="selectedFile"
      @success="handleShareSuccess"
    />

    <!-- 分享统计对话框 -->
    <el-dialog
      v-model="statsDialogVisible"
      title="分享统计"
      width="500px"
    >
      <div v-if="currentShare" class="share-stats">
        <div class="stats-item">
          <span class="label">分享链接：</span>
          <el-input
            :model-value="getShareLink(currentShare.share_code)"
            readonly
            size="small"
          >
            <template #append>
              <el-button @click="handleCopyLink(currentShare)">
                <el-icon><DocumentCopy /></el-icon>
                复制
              </el-button>
            </template>
          </el-input>
        </div>

        <div class="stats-grid">
          <div class="stat-box">
            <div class="stat-value">{{ currentShare.view_count || 0 }}</div>
            <div class="stat-label">访问次数</div>
          </div>
          <div class="stat-box">
            <div class="stat-value">{{ currentShare.download_count || 0 }}</div>
            <div class="stat-label">下载次数</div>
          </div>
        </div>

        <div class="stats-info">
          <div class="info-item">
            <span class="label">创建时间：</span>
            <span class="value">{{ formatDate(currentShare.created_at) }}</span>
          </div>
          <div class="info-item">
            <span class="label">有效期：</span>
            <span class="value">
              {{ currentShare.expire_days === 0 ? '永久有效' : `${currentShare.expire_days}天` }}
            </span>
          </div>
          <div class="info-item">
            <span class="label">类型：</span>
            <span class="value">
              <el-tag :type="!currentShare.has_password ? 'success' : 'warning'" size="small">
                {{ !currentShare.has_password ? '公开' : '私密' }}
              </el-tag>
            </span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { getShareList, cancelShare } from '@/api/share'
import { getFileList } from '@/api/file'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Share,
  Plus,
  View,
  Download,
  Delete,
  DocumentCopy,
  DataAnalysis,
  Document,
  Picture,
  Headset,
  Files
} from '@element-plus/icons-vue'
import ShareDialog from '@/components/ShareDialog.vue'
import dayjs from 'dayjs'

// 数据
const loading = ref(false)
const shareList = ref([])
const selectedShares = ref([])
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 对话框
const shareDialogVisible = ref(false)
const statsDialogVisible = ref(false)
const selectedFile = ref(null)
const currentShare = ref(null)

// 加载分享列表
const loadShareList = async () => {
  loading.value = true
  try {
    const res = await getShareList({
      page: currentPage.value,
      per_page: pageSize.value
    })
    if (res.code === 200) {
      shareList.value = res.data.shares || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载分享列表失败:', error)
    ElMessage.error('加载分享列表失败')
  } finally {
    loading.value = false
  }
}

// 选择变化
const handleSelectionChange = (selection) => {
  selectedShares.value = selection
}

// 创建分享
const handleCreateShare = () => {
  ElMessage.info('请先在文件管理页面选择文件进行分享')
}

// 复制链接
const handleCopyLink = (share) => {
  const link = getShareLink(share.share_code)

  const textarea = document.createElement('textarea')
  textarea.value = link
  document.body.appendChild(textarea)
  textarea.select()

  try {
    document.execCommand('copy')
    ElMessage.success('链接已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制失败')
  }

  document.body.removeChild(textarea)
}

// 获取分享链接
const getShareLink = (shareCode) => {
  const baseUrl = window.location.origin
  return `${baseUrl}/share/${shareCode}`
}

// 查看统计
const handleViewStats = (share) => {
  currentShare.value = share
  statsDialogVisible.value = true
}

// 取消分享
const handleCancelShare = (share) => {
  ElMessageBox.confirm(
    `确定要取消"${share.file_name}"的分享吗？`,
    '取消分享',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await cancelShare(share.id)
      ElMessage.success('已取消分享')
      await loadShareList()
      selectedShares.value = []
    } catch (error) {
      ElMessage.error('取消分享失败')
    }
  }).catch(() => {})
}

// 批量取消
const handleBatchCancel = async () => {
  if (selectedShares.value.length === 0) {
    ElMessage.warning('请先选择要取消的分享')
    return
  }

  ElMessageBox.confirm(
    `确定要取消选中的 ${selectedShares.value.length} 个分享吗？`,
    '批量取消',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      for (const share of selectedShares.value) {
        await cancelShare(share.id)
      }
      ElMessage.success('批量取消成功')
      await loadShareList()
      selectedShares.value = []
    } catch (error) {
      ElMessage.error('批量取消失败')
    }
  }).catch(() => {})
}

// 分享成功
const handleShareSuccess = () => {
  loadShareList()
}

// 分页
const handleSizeChange = () => {
  currentPage.value = 1
  loadShareList()
}

const handleCurrentChange = () => {
  loadShareList()
}

// 判断是否过期
const isExpired = (share) => {
  if (share.expire_days === 0) return false
  const expireDate = dayjs(share.created_at).add(share.expire_days, 'day')
  return dayjs().isAfter(expireDate)
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

// 格式化日期
const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

onMounted(() => {
  loadShareList()
})
</script>

<style scoped>
.share {
  height: 100%;
  padding: 0;
}

.share-card {
  height: 100%;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.share-card :deep(.el-card__header) {
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.share-card :deep(.el-card__body) {
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

.share-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.share-list {
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

.file-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.file-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.share-link {
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 300px;
}

.visit-count,
.download-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: #666;
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

/* 分享统计 */
.share-stats {
  padding: 10px 0;
}

.stats-item {
  margin-bottom: 20px;
}

.stats-item .label {
  font-size: 14px;
  color: #666;
  display: block;
  margin-bottom: 8px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.stat-box {
  text-align: center;
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #666;
}

.stats-info {
  border-top: 1px solid #f0f0f0;
  padding-top: 15px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 10px 0;
  font-size: 14px;
}

.info-item .label {
  color: #666;
}

.info-item .value {
  color: #333;
  font-weight: 500;
}

/* 响应式 */
@media (max-width: 768px) {
  .card-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }

  .share-link {
    max-width: 150px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .batch-actions {
    flex-direction: column;
    gap: 10px;
  }

  .batch-buttons {
    width: 100%;
  }

  .batch-buttons .el-button {
    width: 100%;
  }
}
</style>
