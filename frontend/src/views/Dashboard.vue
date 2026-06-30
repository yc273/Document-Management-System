<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon files">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.total_files || 0 }}</div>
              <div class="stat-label">文档数量</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon folders">
              <el-icon><Folder /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.total_folders || 0 }}</div>
              <div class="stat-label">文件夹</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon shares">
              <el-icon><Share /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ dashboard.total_shares || 0 }}</div>
              <div class="stat-label">分享链接</div>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon storage">
              <el-icon><Coin /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ storagePercent }}%</div>
              <div class="stat-label">存储使用</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近上传 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="recent-files">
          <template #header>
            <div class="card-header">
              <span>最近上传</span>
              <el-button type="primary" size="small" @click="$router.push('/files')">
                查看全部
              </el-button>
            </div>
          </template>

          <el-table :data="dashboard.recent_files || []" style="width: 100%">
            <el-table-column prop="original_name" label="文件名" />
            <el-table-column prop="file_type" label="类型" width="100" />
            <el-table-column prop="file_size_readable" label="大小" width="120" />
            <el-table-column prop="created_at" label="上传时间" width="180" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getDashboard } from '@/api/stat'
import { useUserStore } from '@/store/user'
import { Document, Folder, Share, Coin } from '@element-plus/icons-vue'

const userStore = useUserStore()

// 仪表板数据
const dashboard = ref({
  total_files: 0,
  total_folders: 0,
  total_shares: 0,
  storage: {},
  recent_files: []
})

// 存储使用百分比
const storagePercent = computed(() => {
  if (!dashboard.value.storage || !dashboard.value.storage.total) return 0
  return dashboard.value.storage.percent || 0
})

// 加载仪表板数据
const loadDashboard = async () => {
  try {
    const res = await getDashboard()
    if (res.code === 200) {
      dashboard.value = res.data
    }
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
  }
}

onMounted(() => {
  loadDashboard()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  border-radius: 8px;
}

.stat-content {
  display: flex;
  align-items: center;
  padding: 10px 0;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #fff;
}

.stat-icon.files {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.folders {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.shares {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon.storage {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.stat-info {
  margin-left: 20px;
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #999;
  margin-top: 8px;
}

.recent-files {
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
