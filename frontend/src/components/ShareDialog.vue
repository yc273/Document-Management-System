<template>
  <div class="share-dialog">
    <el-dialog
      v-model="visible"
      :title="title"
      width="500px"
      @close="handleClose"
    >
      <el-form
        ref="formRef"
        :model="shareForm"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="分享文件">
          <div class="file-info">
            <el-icon :size="32" :color="getFileIconColor()">
              <component :is="getFileIcon()" />
            </el-icon>
            <span class="file-name">{{ fileInfo?.original_name }}</span>
          </div>
        </el-form-item>

        <el-form-item label="分享方式" prop="share_type">
          <el-radio-group v-model="shareForm.share_type">
            <el-radio value="public">公开分享</el-radio>
            <el-radio value="private">私密分享</el-radio>
          </el-radio-group>
        </el-form-item>

        <el-form-item
          v-if="shareForm.share_type === 'private'"
          label="提取码"
          prop="share_code"
        >
          <el-input
            v-model="shareForm.share_code"
            placeholder="4位提取码（可选，不填则自动生成）"
            maxlength="4"
            show-word-limit
          >
            <template #append>
              <el-button @click="generateCode">生成</el-button>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="有效期" prop="expire_days">
          <el-select v-model="shareForm.expire_days" placeholder="选择有效期">
            <el-option label="永久有效" :value="0" />
            <el-option label="1天" :value="1" />
            <el-option label="7天" :value="7" />
            <el-option label="30天" :value="30" />
          </el-select>
        </el-form-item>

        <el-form-item label="访问限制" prop="max_visits">
          <el-input-number
            v-model="shareForm.max_visits"
            :min="0"
            :max="99999"
            placeholder="不限制"
          />
          <span class="form-tip">0表示不限制访问次数</span>
        </el-form-item>

        <el-form-item label="备注">
          <el-input
            v-model="shareForm.remark"
            type="textarea"
            :rows="3"
            placeholder="添加备注信息（可选）"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <!-- 分享结果 -->
        <el-alert
          v-if="shareLink"
          title="分享成功"
          type="success"
          :closable="false"
          show-icon
        >
          <template #default>
            <div class="share-result">
              <div class="link-item">
                <span class="label">分享链接：</span>
                <div class="link-wrapper">
                  <el-input
                    v-model="shareLink"
                    readonly
                    size="small"
                  >
                    <template #append>
                      <el-button @click="copyLink">复制</el-button>
                    </template>
                  </el-input>
                </div>
              </div>

              <div v-if="shareForm.share_type === 'private'" class="code-item">
                <span class="label">提取码：</span>
                <el-tag type="info" size="large">{{ shareForm.share_code }}</el-tag>
              </div>

              <div class="qr-code">
                <el-button
                  type="primary"
                  link
                  @click="showQRCode = !showQRCode"
                >
                  <el-icon><Files /></el-icon>
                  {{ showQRCode ? '隐藏' : '显示' }}二维码
                </el-button>
              </div>

              <div v-if="showQRCode" class="qr-code-wrapper">
                <div class="qr-code-canvas">
                  <img
                    :src="`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(shareLink)}`"
                    alt="二维码"
                    class="qr-code-image"
                  />
                </div>
              </div>
            </div>
          </template>
        </el-alert>
      </el-form>

      <template #footer>
        <el-button @click="handleClose">取消</el-button>
        <el-button
          v-if="!shareLink"
          type="primary"
          @click="handleCreateShare"
          :loading="submitting"
        >
          创建分享
        </el-button>
        <el-button
          v-else
          type="primary"
          @click="handleClose"
        >
          完成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, nextTick, watch } from 'vue'
import { createShare, getShareList } from '@/api/share'
import { ElMessage } from 'element-plus'
import {
  Document, Picture, Headset, Files
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  fileInfo: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'success'])

const visible = ref(false)
const formRef = ref(null)
const submitting = ref(false)
const shareLink = ref('')
const showQRCode = ref(false)
const qrCodeRef = ref(null)

// 标题
const title = computed(() => {
  return shareLink.value ? '分享成功' : '创建分享'
})

// 表单数据
const shareForm = ref({
  share_type: 'public', // public | private
  share_code: '',
  expire_days: 7,
  max_visits: 0,
  remark: ''
})

// 表单验证规则
const formRules = {
  share_type: [
    { required: true, message: '请选择分享方式', trigger: 'change' }
  ],
  share_code: [
    { min: 4, max: 4, message: '提取码为4位', trigger: 'blur' }
  ],
  expire_days: [
    { required: true, message: '请选择有效期', trigger: 'change' }
  ]
}

// 获取文件图标
const getFileIcon = () => {
  if (!props.fileInfo) return Document
  const fileType = props.fileInfo.file_type?.toLowerCase() || ''
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
  return iconMap[fileType] || Document
}

// 获取文件图标颜色
const getFileIconColor = () => {
  if (!props.fileInfo) return '#909399'
  const fileType = props.fileInfo.file_type?.toLowerCase() || ''
  const colorMap = {
    'pdf': '#F56C6C',
    'doc': '#409EFF',
    'docx': '#409EFF',
    'jpg': '#409EFF',
    'png': '#409EFF'
  }
  return colorMap[fileType] || '#909399'
}

// 生成提取码
const generateCode = () => {
  const chars = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
  let code = ''
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  shareForm.value.share_code = code
}

// 创建分享
const handleCreateShare = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
  } catch (error) {
    return
  }

  submitting.value = true
  try {
    const data = {
      file_id: props.fileInfo.id,
      expire_days: shareForm.value.expire_days,
      password: shareForm.value.share_type === 'private' ? shareForm.value.share_code : null
    }

    const res = await createShare(data)
    if (res.code === 200) {
      // 生成分享链接
      const baseUrl = window.location.origin
      shareLink.value = `${baseUrl}/share/${res.data.share.share_code}`

      ElMessage.success('创建分享成功')
      emit('success')
    }
  } catch (error) {
    ElMessage.error('创建分享失败')
  } finally {
    submitting.value = false
  }
}

// 复制链接
const copyLink = () => {
  const textarea = document.createElement('textarea')
  textarea.value = shareLink.value
  document.body.appendChild(textarea)
  textarea.select()

  try {
    document.execCommand('copy')
    ElMessage.success('复制成功')
  } catch (error) {
    ElMessage.error('复制失败')
  }

  document.body.removeChild(textarea)
}

// 关闭对话框
const handleClose = () => {
  visible.value = false
  // 重置表单
  shareForm.value = {
    share_type: 'public',
    share_code: '',
    expire_days: 7,
    max_visits: 0,
    remark: ''
  }
  shareLink.value = ''
  showQRCode.value = false
}

// 监听modelValue变化
watch(
  () => props.modelValue,
  (val) => {
    visible.value = val
  },
  { immediate: true }
)

watch(visible, (val) => {
  emit('update:modelValue', val)
})
</script>

<style scoped>
.share-dialog :deep(.el-dialog__body) {
  padding-top: 20px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 4px;
}

.file-name {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.form-tip {
  margin-left: 10px;
  font-size: 12px;
  color: #999;
}

/* 分享结果 */
.share-result {
  padding: 10px 0;
}

.link-item,
.code-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.label {
  width: 80px;
  font-size: 14px;
  color: #666;
  flex-shrink: 0;
}

.link-wrapper {
  flex: 1;
}

.qr-code {
  margin-top: 10px;
}

.qr-code-wrapper {
  display: flex;
  justify-content: center;
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  margin-top: 10px;
}

.qr-code-canvas {
  width: 200px;
  height: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.qr-code-image {
  width: 200px;
  height: 200px;
  object-fit: contain;
}

/* 响应式 */
@media (max-width: 768px) {
  .link-item,
  .code-item {
    flex-direction: column;
    align-items: stretch;
  }

  .label {
    margin-bottom: 5px;
  }
}
</style>
