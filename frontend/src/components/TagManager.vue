<template>
  <div class="tag-manager">
    <!-- 标签选择器 -->
    <div v-if="mode === 'select'" class="tag-selector">
      <el-select
        v-model="selectedTags"
        multiple
        placeholder="选择标签"
        collapse-tags
        collapse-tags-tooltip
        @change="handleTagChange"
      >
        <el-option
          v-for="tag in tagList"
          :key="tag.id"
          :label="tag.name"
          :value="tag.id"
        >
          <div class="tag-option">
            <el-tag
              :color="tag.color"
              size="small"
              effect="plain"
            >
              {{ tag.name }}
            </el-tag>
            <span class="use-count">({{ tag.use_count || 0 }})</span>
          </div>
        </el-option>
      </el-select>

      <el-button
        type="primary"
        size="small"
        link
        @click="showCreateDialog"
      >
        <el-icon><Plus /></el-icon>
        新建标签
      </el-button>
    </div>

    <!-- 标签列表 -->
    <div v-else-if="mode === 'list'" class="tag-list">
      <div class="tag-list-header">
        <div class="header-title">
          <el-icon><PriceTag /></el-icon>
          <span>标签列表</span>
        </div>
        <el-button
          type="primary"
          size="small"
          @click="showCreateDialog"
        >
          <el-icon><Plus /></el-icon>
          新建标签
        </el-button>
      </div>

      <div class="tag-list-content">
        <el-empty v-if="tagList.length === 0" description="暂无标签" />

        <div v-else class="tag-grid">
          <div
            v-for="tag in tagList"
            :key="tag.id"
            class="tag-item"
          >
            <el-tag
              :color="tag.color"
              size="large"
              closable
              @close="handleDeleteTag(tag)"
            >
              {{ tag.name }}
            </el-tag>
            <div class="tag-actions">
              <el-button
                type="primary"
                size="small"
                link
                @click="handleEditTag(tag)"
              >
                <el-icon><Edit /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 新建/编辑标签对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEditMode ? '编辑标签' : '新建标签'"
      width="400px"
    >
      <el-form :model="tagForm" label-width="80px">
        <el-form-item label="标签名称">
          <el-input
            v-model="tagForm.name"
            placeholder="请输入标签名称"
            maxlength="20"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="标签颜色">
          <div class="color-picker-wrapper">
            <el-color-picker v-model="tagForm.color" />
            <el-tag :color="tagForm.color" style="margin-left: 10px">
              {{ tagForm.name || '预览' }}
            </el-tag>
          </div>
        </el-form-item>

        <!-- 预设颜色 -->
        <el-form-item label="快速选择">
          <div class="preset-colors">
            <div
              v-for="color in presetColors"
              :key="color"
              class="color-item"
              :style="{ backgroundColor: color }"
              @click="tagForm.color = color"
            >
              <el-icon v-if="tagForm.color === color"><Check /></el-icon>
            </div>
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getTagList, createTag, updateTag, deleteTag } from '@/api/tag'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, PriceTag, Check } from '@element-plus/icons-vue'

const props = defineProps({
  mode: {
    type: String,
    default: 'select', // select | list
    validator: (value) => ['select', 'list'].includes(value)
  },
  modelValue: {
    type: Array,
    default: () => []
  },
  fileId: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'change', 'refresh'])

// 标签列表
const tagList = ref([])

// 选中的标签
const selectedTags = ref([])

// 对话框
const dialogVisible = ref(false)
const isEditMode = ref(false)
const submitting = ref(false)

// 标签表单
const tagForm = ref({
  id: null,
  name: '',
  color: '#409EFF'
})

// 预设颜色
const presetColors = ref([
  '#409EFF', // 蓝色
  '#67C23A', // 绿色
  '#E6A23C', // 橙色
  '#F56C6C', // 红色
  '#909399', // 灰色
  '#C0392B', // 深红
  '#8E44AD', // 紫色
  '#2980B9', // 深蓝
  '#27AE60', // 深绿
  '#D35400', // 深橙
  '#16A085', // 青色
  '#2C3E50'  // 深灰
])

// 加载标签列表
const loadTags = async () => {
  try {
    const res = await getTagList()
    if (res.code === 200) {
      tagList.value = res.data || []
    }
  } catch (error) {
    console.error('加载标签列表失败:', error)
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  isEditMode.value = false
  tagForm.value = {
    id: null,
    name: '',
    color: '#409EFF'
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = () => {
  isEditMode.value = true
  dialogVisible.value = true
}

// 编辑标签
const handleEditTag = (tag) => {
  tagForm.value = {
    id: tag.id,
    name: tag.name,
    color: tag.color
  }
  showEditDialog()
}

// 删除标签
const handleDeleteTag = (tag) => {
  ElMessageBox.confirm(
    `确定要删除标签"${tag.name}"吗？删除后将无法恢复。`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteTag(tag.id)
      ElMessage.success('删除成功')
      await loadTags()
      emit('refresh')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 确认新建/编辑
const handleConfirm = async () => {
  if (!tagForm.value.name.trim()) {
    ElMessage.warning('标签名称不能为空')
    return
  }

  submitting.value = true
  try {
    if (isEditMode.value) {
      // 编辑
      await updateTag(tagForm.value.id, {
        name: tagForm.value.name,
        color: tagForm.value.color
      })
      ElMessage.success('修改成功')
    } else {
      // 新建
      await createTag({
        name: tagForm.value.name,
        color: tagForm.value.color
      })
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    await loadTags()
    emit('refresh')
  } catch (error) {
    ElMessage.error(isEditMode.value ? '修改失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 标签选择变化
const handleTagChange = (value) => {
  emit('update:modelValue', value)
  emit('change', value)
}

// 刷新
const refresh = () => {
  loadTags()
}

// 暴露方法给父组件
defineExpose({
  refresh
})

onMounted(() => {
  loadTags()
  // 初始化选中的标签
  selectedTags.value = [...props.modelValue]
})
</script>

<style scoped>
.tag-manager {
  width: 100%;
}

/* 标签选择器 */
.tag-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.tag-selector .el-select {
  flex: 1;
}

.tag-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.use-count {
  font-size: 12px;
  color: #999;
  margin-left: 8px;
}

/* 标签列表 */
.tag-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.tag-list-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 15px;
  border-bottom: 1px solid #f0f0f0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.tag-list-content {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.tag-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 15px;
}

.tag-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
  background: #f5f7fa;
  border-radius: 6px;
  transition: all 0.3s;
}

.tag-item:hover {
  background: #e6f7ff;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tag-actions {
  opacity: 0;
  transition: opacity 0.3s;
}

.tag-item:hover .tag-actions {
  opacity: 1;
}

/* 颜色选择器 */
.color-picker-wrapper {
  display: flex;
  align-items: center;
}

.preset-colors {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.color-item {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.color-item:hover {
  transform: scale(1.1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.color-item .el-icon {
  font-size: 18px;
}

/* 滚动条样式 */
.tag-list-content::-webkit-scrollbar {
  width: 6px;
}

.tag-list-content::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.tag-list-content::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>
