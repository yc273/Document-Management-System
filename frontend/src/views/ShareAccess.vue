<template>
  <div class="share-access">
    <div class="access-container">
      <!-- 密码验证界面 -->
      <div v-if="!verified && !loading" class="password-card">
        <div class="card-header">
          <el-icon :size="48" color="#409eff"><Lock /></el-icon>
          <h2>私密分享</h2>
          <p>请输入提取码访问文件</p>
        </div>

        <el-form :model="passwordForm" @submit.prevent="handleVerifyPassword">
          <el-form-item>
            <el-input
              v-model="passwordForm.password"
              placeholder="请输入4位提取码"
              maxlength="4"
              size="large"
              clearable
              show-word-limit
            >
              <template #prefix>
                <el-icon><Key /></el-icon>
              </template>
            </el-input>
          </el-form-item>

          <el-button
            type="primary"
            size="large"
            :loading="verifying"
            @click="handleVerifyPassword"
            style="width: 100%"
          >
            访问文件
          </el-button>
        </el-form>
      </div>

      <!-- 文件信息界面 -->
      <div v-if="verified && shareInfo" class="file-card">
        <div class="card-header">
          <el-icon :size="48" :color="getFileIconColor(shareInfo.file_type)">
            <component :is="getFileIcon(shareInfo.file_type)" />
          </el-icon>
          <h2>{{ shareInfo.file_name }}</h2>
          <p class="file-meta">
            <span>{{ shareInfo.file_size_readable }}</span>
            <span>•</span>
            <span>分享于 {{ formatDate(shareInfo.created_at) }}</span>
          </p>
        </div>

        <div class="file-info">
          <div class="info-item">
            <span class="label">分享者：</span>
            <span class="value">{{ shareInfo.nickname || '用户' }}</span>
          </div>

          <div v-if="shareInfo.expire_days > 0" class="info-item">
            <span class="label">有效期：</span>
            <span class="value">{{ shareInfo.expire_days }}天</span>
          </div>

          <div v-else class="info-item">
            <span class="label">有效期：</span>
            <span class="value">永久有效</span>
          </div>

          <div class="info-item">
            <span class="label">访问次数：</span>
            <span class="value">{{ shareInfo.view_count || 0 }}次</span>
          </div>

          <div class="info-item">
            <span class="label">下载次数：</span>
            <span class="value">{{ shareInfo.download_count || 0 }}次</span>
          </div>
        </div>

        <div class="actions">
          <el-button
            type="primary"
            size="large"
            @click="handleDownload"
            :loading="downloading"
          >
            <el-icon><Download /></el-icon>
            下载文件
          </el-button>

          <el-button
            v-if="showPreview"
            type="success"
            size="large"
            @click="handlePreview"
          >
            <el-icon><View /></el-icon>
            在线预览
          </el-button>
        </div>

        <div class="tips">
          <el-icon><InfoFilled /></el-icon>
          <span>文件来自智能文档管理系统，安全可靠</span>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="loading-card">
        <el-icon :size="48" class="is-loading"><Loading /></el-icon>
        <p>正在加载分享信息...</p>
      </div>

      <!-- 错误状态 -->
      <div v-if="error" class="error-card">
        <el-icon :size="48" color="#f56c6c"><CircleClose /></el-icon>
        <h2>分享不存在</h2>
        <p>{{ errorMessage }}</p>
        <el-button type="primary" @click="goHome">返回首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getShare, verifyShare } from '@/api/share'
import { ElMessage } from 'element-plus'
import {
  Lock, Key, Download, View, InfoFilled, Loading, CircleClose,
  Document, Picture, Headset, Files
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

const route = useRoute()
const router = useRouter()

// 数据
const loading = ref(true)
const verifying = ref(false)
const verified = ref(false)
const error = ref(false)
const errorMessage = ref('')
const shareInfo = ref(null)
const downloading = ref(false)

// 表单数据
const passwordForm = ref({
  password: ''
})

// 获取分享码
const shareCode = computed(() => route.params.shareCode)

// 是否显示预览按钮
const showPreview = computed(() => {
  if (!shareInfo.value) return false
  const fileType = shareInfo.value.file_type?.toLowerCase()
  return ['pdf', 'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'webp'].includes(fileType)
})

// 加载分享信息
const loadShareInfo = async () => {
  loading.value = true
  try {
    const res = await getShare(shareCode.value)
    if (res.code === 200) {
      shareInfo.value = res.data.share
      // 如果不需要密码，直接验证通过
      if (!shareInfo.value.has_password) {
        verified.value = true
      }
    }
  } catch (err) {
    error.value = true
    errorMessage.value = err.response?.data?.message || '分享不存在或已失效'
  } finally {
    loading.value = false
  }
}

// 验证密码
const handleVerifyPassword = async () => {
  if (!passwordForm.value.password || passwordForm.value.password.length !== 4) {
    ElMessage.warning('请输入4位提取码')
    return
  }

  verifying.value = true
  try {
    const res = await verifyShare(shareCode.value, {
      password: passwordForm.value.password
    })
    if (res.code === 200) {
      verified.value = true
      // 增加访问计数
      shareInfo.value.view_count = (shareInfo.value.view_count || 0) + 1
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '提取码错误')
  } finally {
    verifying.value = false
  }
}

// 下载文件
const handleDownload = async () => {
  downloading.value = true
  try {
    const url = `${import.meta.env.VITE_API_BASE_URL || ''}/api/share/${shareCode.value}/download`
    window.open(url, '_blank')

    // 增加下载计数
    shareInfo.value.download_count = (shareInfo.value.download_count || 0) + 1
  } catch (err) {
    ElMessage.error('下载失败')
  } finally {
    downloading.value = false
  }
}

// 预览文件
const handlePreview = () => {
  const url = `${import.meta.env.VITE_API_BASE_URL || ''}/api/file/preview/${shareInfo.value.file_id}`
  window.open(url, '_blank')
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
    'mp4': Files
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

// 返回首页
const goHome = () => {
  router.push('/')
}

onMounted(() => {
  loadShareInfo()
})
</script>

<style scoped>
.share-access {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.access-container {
  width: 100%;
  max-width: 480px;
}

.password-card,
.file-card,
.loading-card,
.error-card {
  background: white;
  border-radius: 12px;
  padding: 40px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.card-header {
  margin-bottom: 30px;
}

.card-header h2 {
  margin: 16px 0 8px;
  font-size: 24px;
  color: #333;
}

.card-header p {
  color: #666;
  font-size: 14px;
}

.file-meta {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #999;
  font-size: 14px;
}

.file-info {
  padding: 20px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 30px;
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

.actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.tips {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin-top: 20px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  color: #666;
  font-size: 13px;
}

.loading-card p {
  margin-top: 16px;
  color: #666;
}

.error-card h2 {
  margin: 16px 0 8px;
  color: #333;
}

.error-card p {
  color: #666;
  margin-bottom: 20px;
}

/* 响应式 */
@media (max-width: 480px) {
  .share-access {
    padding: 10px;
  }

  .password-card,
  .file-card,
  .loading-card,
  .error-card {
    padding: 30px 20px;
  }

  .actions {
    flex-direction: column;
  }

  .actions .el-button {
    width: 100%;
  }
}
</style>