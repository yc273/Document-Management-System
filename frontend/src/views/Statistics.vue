<template>
  <div class="statistics">
    <el-row :gutter="20" class="stats-row">
      <!-- 存储空间统计 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><Coin /></el-icon> 存储空间</span>
            </div>
          </template>
          <div class="chart-wrapper">
            <div ref="storageChartRef" class="chart" style="height: 300px"></div>
          </div>
          <div class="storage-info">
            <div class="info-item">
              <span class="label">已使用：</span>
              <span class="value">{{ storageUsed }}</span>
            </div>
            <div class="info-item">
              <span class="label">可用空间：</span>
              <span class="value">{{ storageAvailable }}</span>
            </div>
            <div class="info-item">
              <span class="label">使用率：</span>
              <span class="value percent">{{ storagePercent }}%</span>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 文档类型分布 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><PieChart /></el-icon> 文档类型分布</span>
            </div>
          </template>
          <div class="chart-wrapper">
            <div ref="typeChartRef" class="chart" style="height: 300px"></div>
          </div>
        </el-card>
      </el-col>

      <!-- 上传趋势 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><TrendCharts /></el-icon> 上传趋势（近7天）</span>
            </div>
          </template>
          <div class="chart-wrapper">
            <div ref="uploadChartRef" class="chart" style="height: 350px"></div>
          </div>
        </el-card>
      </el-col>

      <!-- 操作统计 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><DataAnalysis /></el-icon> 操作统计</span>
            </div>
          </template>
          <div class="chart-wrapper">
            <div ref="actionChartRef" class="chart" style="height: 300px"></div>
          </div>
        </el-card>
      </el-col>

      <!-- 操作日志 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="stat-card">
          <template #header>
            <div class="card-header">
              <span><el-icon><DocumentCopy /></el-icon> 最近操作</span>
            </div>
          </template>
          <div class="log-list">
            <el-empty v-if="logs.length === 0" description="暂无操作日志" />
            <div v-else class="log-items">
              <div
                v-for="log in logs"
                :key="log.id"
                class="log-item"
              >
                <div class="log-icon">
                  <el-icon><Operation /></el-icon>
                </div>
                <div class="log-content">
                  <div class="log-action">{{ log.action }}</div>
                  <div class="log-desc">{{ log.description }}</div>
                  <div class="log-time">{{ formatTime(log.created_at) }}</div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import { getStorageStats, getUploadStats, getLogStats } from '@/api/stat'
import { ElMessage } from 'element-plus'
import {
  Coin,
  PieChart,
  TrendCharts,
  DataAnalysis,
  DocumentCopy,
  Operation
} from '@element-plus/icons-vue'
import dayjs from 'dayjs'

// 图表引用
const storageChartRef = ref(null)
const typeChartRef = ref(null)
const uploadChartRef = ref(null)
const actionChartRef = ref(null)

// 图表实例
let storageChart = null
let typeChart = null
let uploadChart = null
let actionChart = null

// 数据
const storageStats = ref({
  total: 0,
  used: 0,
  available: 0,
  percent: 0
})

const typeStats = ref([])
const uploadStats = ref([])
const actionStats = ref([])
const logs = ref([])

// 计算属性
const storageUsed = computed(() => {
  return formatSize(storageStats.value.used)
})

const storageAvailable = computed(() => {
  return formatSize(storageStats.value.available)
})

const storagePercent = computed(() => {
  return storageStats.value.percent.toFixed(2)
})

// 格式化文件大小
const formatSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
}

// 格式化时间
const formatTime = (time) => {
  return dayjs(time).format('YYYY-MM-DD HH:mm:ss')
}

// 初始化存储空间图表
const initStorageChart = () => {
  if (!storageChartRef.value) return

  storageChart = echarts.init(storageChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center'
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        label: {
          show: false,
          position: 'center'
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: 'bold'
          }
        },
        labelLine: {
          show: false
        },
        data: [
          {
            value: storageStats.value.used,
            name: '已使用',
            itemStyle: { color: '#409EFF' }
          },
          {
            value: storageStats.value.available,
            name: '可用空间',
            itemStyle: { color: '#E6F7FF' }
          }
        ]
      }
    ]
  }

  storageChart.setOption(option)
}

// 初始化文档类型图表
const initTypeChart = () => {
  if (!typeChartRef.value) return

  typeChart = echarts.init(typeChartRef.value)

  const option = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '10%',
      top: 'center'
    },
    series: [
      {
        type: 'pie',
        radius: '65%',
        center: ['35%', '50%'],
        data: typeStats.value.map(item => ({
          value: item.count,
          name: item.type.toUpperCase()
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  typeChart.setOption(option)
}

// 初始化上传趋势图表
const initUploadChart = () => {
  if (!uploadChartRef.value) return

  uploadChart = echarts.init(uploadChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['上传数量', '上传大小']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: uploadStats.value.map(item => item.date)
    },
    yAxis: [
      {
        type: 'value',
        name: '数量',
        position: 'left'
      },
      {
        type: 'value',
        name: '大小(MB)',
        position: 'right'
      }
    ],
    series: [
      {
        name: '上传数量',
        type: 'line',
        smooth: true,
        data: uploadStats.value.map(item => item.count),
        itemStyle: { color: '#409EFF' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.3)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.05)' }
          ])
        }
      },
      {
        name: '上传大小',
        type: 'line',
        smooth: true,
        yAxisIndex: 1,
        data: uploadStats.value.map(item => (item.size / 1024 / 1024).toFixed(2)),
        itemStyle: { color: '#67C23A' }
      }
    ]
  }

  uploadChart.setOption(option)
}

// 初始化操作统计图表
const initActionChart = () => {
  if (!actionChartRef.value) return

  actionChart = echarts.init(actionChartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: actionStats.value.map(item => item.action)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        type: 'bar',
        data: actionStats.value.map(item => item.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#409EFF' },
            { offset: 1, color: '#66B1FF' }
          ])
        },
        barWidth: '60%'
      }
    ]
  }

  actionChart.setOption(option)
}

// 加载统计数据
const loadStats = async () => {
  try {
    // 存储统计
    const storageRes = await getStorageStats()
    if (storageRes.code === 200) {
      storageStats.value = storageRes.data.storage || {}

      // 文档类型统计
      const fileTypes = storageRes.data.file_types || []
      typeStats.value = fileTypes.map(item => ({
        type: item.type,
        count: item.count,
        totalSize: item.total_size_mb
      }))
    }

    // 上传统计
    const uploadRes = await getUploadStats()
    if (uploadRes.code === 200) {
      uploadStats.value = uploadRes.data.daily || []
    }

    // 日志统计
    const logRes = await getLogStats()
    if (logRes.code === 200) {
      logs.value = logRes.data.logs || []
      // 从日志中统计操作类型
      const actionMap = {}
      logs.value.forEach(log => {
        const action = log.action || 'unknown'
        actionMap[action] = (actionMap[action] || 0) + 1
      })
      actionStats.value = Object.keys(actionMap).map(key => ({
        action: key,
        count: actionMap[key]
      }))
    }

    // 初始化图表
    initStorageChart()
    initTypeChart()
    initUploadChart()
    initActionChart()
  } catch (error) {
    console.error('加载统计数据失败:', error)
    ElMessage.error('加载统计数据失败')
  }
}

// 窗口大小变化时重绘图表
const handleResize = () => {
  storageChart?.resize()
  typeChart?.resize()
  uploadChart?.resize()
  actionChart?.resize()
}

onMounted(() => {
  loadStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  storageChart?.dispose()
  typeChart?.dispose()
  uploadChart?.dispose()
  actionChart?.dispose()
})
</script>

<style scoped>
.statistics {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
  border-radius: 8px;
}

.stat-card:last-child {
  margin-bottom: 0;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #333;
}

.chart-wrapper {
  padding: 10px 0;
}

.chart {
  width: 100%;
}

/* 存储信息 */
.storage-info {
  display: flex;
  justify-content: space-around;
  padding: 20px 0;
  border-top: 1px solid #f0f0f0;
}

.info-item {
  text-align: center;
}

.info-item .label {
  font-size: 14px;
  color: #999;
  display: block;
  margin-bottom: 5px;
}

.info-item .value {
  font-size: 18px;
  font-weight: 600;
  color: #333;
}

.info-item .value.percent {
  color: #409eff;
}

/* 日志列表 */
.log-list {
  max-height: 300px;
  overflow-y: auto;
}

.log-items {
  padding: 10px 0;
}

.log-item {
  display: flex;
  gap: 15px;
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.3s;
}

.log-item:last-child {
  border-bottom: none;
}

.log-item:hover {
  background: #f5f7fa;
}

.log-icon {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #e6f7ff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
}

.log-content {
  flex: 1;
}

.log-action {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
}

.log-desc {
  font-size: 13px;
  color: #666;
  margin-bottom: 5px;
}

.log-time {
  font-size: 12px;
  color: #999;
}

/* 滚动条样式 */
.log-list::-webkit-scrollbar {
  width: 6px;
}

.log-list::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.log-list::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}

/* 响应式 */
@media (max-width: 768px) {
  .storage-info {
    flex-direction: column;
    gap: 15px;
  }

  .info-item {
    display: flex;
    justify-content: space-between;
    padding: 0 20px;
  }

  .log-item {
    flex-direction: column;
    gap: 10px;
  }

  .log-icon {
    width: 100%;
    height: 30px;
    border-radius: 4px;
  }
}
</style>
