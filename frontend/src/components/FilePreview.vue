<template>
  <el-dialog
    v-model="visible"
    :title="file?.original_name || '预览'"
    :width="dialogWidth"
    :top="dialogTop"
    :close-on-click-modal="false"
    destroy-on-close
    class="file-preview-dialog"
    @closed="handleClosed"
  >
    <div class="preview-container" v-loading="loading">
      <!-- 图片预览 -->
      <div v-if="fileType === 'image'" class="preview-image-wrapper">
        <img :src="previewUrl" :alt="file?.original_name" class="preview-image" @load="loading = false" @error="handleError" />
      </div>

      <!-- PDF预览 -->
      <div v-else-if="fileType === 'pdf'" class="preview-pdf-wrapper">
        <iframe
          :src="previewUrl"
          class="preview-pdf"
          frameborder="0"
          @load="loading = false"
          @error="handleError"
        ></iframe>
      </div>

      <!-- 视频预览 -->
      <div v-else-if="fileType === 'video'" class="preview-video-wrapper">
        <video
          controls
          autoplay
          class="preview-video"
          @loadeddata="loading = false"
          @error="handleError"
        >
          <source :src="previewUrl" />
          您的浏览器不支持视频预览
        </video>
      </div>

      <!-- 音频预览 -->
      <div v-else-if="fileType === 'audio'" class="preview-audio-wrapper">
        <div class="audio-info">
          <el-icon :size="64" color="#409EFF"><Headset /></el-icon>
          <p class="audio-name">{{ file?.original_name }}</p>
        </div>
        <audio
          controls
          autoplay
          class="preview-audio"
          @loadeddata="loading = false"
          @error="handleError"
        >
          <source :src="previewUrl" />
          您的浏览器不支持音频预览
        </audio>
      </div>

      <!-- 文本预览 -->
      <div v-else-if="fileType === 'text'" class="preview-text-wrapper">
        <pre class="preview-text" v-if="textContent !== null">{{ textContent }}</pre>
        <el-empty v-else-if="!loading" description="无法加载文本内容" />
      </div>

      <!-- 不支持的类型 -->
      <div v-else class="preview-unsupported">
        <el-empty :description="`暂不支持预览 ${file?.file_type || ''} 格式`">
          <el-button type="primary" @click="handleDownload">下载文件</el-button>
        </el-empty>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Headset } from '@element-plus/icons-vue'
import request from '@/utils/request'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  file: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible'])

const visible = ref(false)
const loading = ref(true)
const textContent = ref(null)

// 同步外部的 visible
watch(() => props.visible, (val) => {
  visible.value = val
  if (val && props.file) {
    loadPreview()
  }
})

watch(visible, (val) => {
  if (!val) {
    textContent.value = null
  }
  emit('update:visible', val)
})

// 文件类型
const fileType = computed(() => {
  return props.file?.file_type?.toLowerCase() || ''
})

// 预览 URL
const previewUrl = computed(() => {
  if (!props.file?.id) return ''
  return `/api/file/preview/${props.file.id}`
})

// 对话框宽度
const dialogWidth = computed(() => {
  if (fileType.value === 'image') return 'auto'
  if (fileType.value === 'pdf') return '90%'
  if (fileType.value === 'video') return '80%'
  if (fileType.value === 'text') return '70%'
  return '500px'
})

// 对话框顶部距离
const dialogTop = computed(() => {
  if (fileType.value === 'image') return '5vh'
  return '5vh'
})

// 加载预览
const loadPreview = () => {
  loading.value = true
  textContent.value = null

  // 文本文件需要获取内容
  if (fileType.value === 'text') {
    request({
      url: `/file/preview/${props.file.id}`,
      method: 'get',
      responseType: 'text'
    }).then(res => {
      textContent.value = res
      loading.value = false
    }).catch(() => {
      textContent.value = null
      loading.value = false
    })
  } else if (['image', 'pdf', 'video', 'audio'].includes(fileType.value)) {
    // 这些类型通过标签加载，由标签的 load/loadeddata 事件控制 loading
    // 但如果内容本身加载失败，设置超时防止无限 loading
    setTimeout(() => {
      if (loading.value) {
        loading.value = false
      }
    }, 15000)
  } else {
    loading.value = false
  }
}

// 加载错误
const handleError = () => {
  loading.value = false
  ElMessage.error('预览加载失败')
}

// 对话框关闭
const handleClosed = () => {
  textContent.value = null
  loading.value = true
}

// 下载
const handleDownload = () => {
  if (props.file?.id) {
    window.open(`/api/file/download/${props.file.id}`, '_blank')
  }
}
</script>

<style scoped>
.file-preview-dialog :deep(.el-dialog__body) {
  padding: 0;
  overflow: hidden;
}

.file-preview-dialog :deep(.el-dialog__header) {
  margin-right: 0;
  padding: 15px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.preview-container {
  min-height: 200px;
  max-height: 80vh;
  overflow: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

/* 图片预览 */
.preview-image-wrapper {
  text-align: center;
  max-width: 100%;
}

.preview-image {
  max-width: 100%;
  max-height: 75vh;
  object-fit: contain;
  border-radius: 4px;
}

/* PDF预览 */
.preview-pdf-wrapper {
  width: 100%;
  height: 75vh;
}

.preview-pdf {
  width: 100%;
  height: 100%;
  border: none;
}

/* 视频预览 */
.preview-video-wrapper {
  width: 100%;
  max-width: 800px;
}

.preview-video {
  width: 100%;
  max-height: 70vh;
  border-radius: 4px;
}

/* 音频预览 */
.preview-audio-wrapper {
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.audio-info {
  margin-bottom: 30px;
}

.audio-name {
  margin-top: 12px;
  font-size: 16px;
  color: #333;
}

.preview-audio {
  width: 100%;
}

/* 文本预览 */
.preview-text-wrapper {
  width: 100%;
  max-height: 70vh;
  overflow: auto;
}

.preview-text {
  margin: 0;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-wrap: break-word;
  color: #333;
}

/* 不支持的类型 */
.preview-unsupported {
  padding: 60px 0;
}
</style>
