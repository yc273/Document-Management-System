<template>
  <div class="folder-tree">
    <div class="tree-header">
      <div class="header-title">
        <el-icon><Folder /></el-icon>
        <span>文件夹</span>
      </div>
      <el-button
        type="primary"
        size="small"
        link
        @click="handleCreateFolder(0)"
        v-if="canCreateFolder"
      >
        <el-icon><FolderAdd /></el-icon>
      </el-button>
    </div>

    <div class="tree-content" v-loading="loading">
      <el-tree
        ref="treeRef"
        :data="treeData"
        :props="treeProps"
        :highlight-current="true"
        :default-expand-all="false"
        :expand-on-click-node="false"
        node-key="id"
        @node-click="handleNodeClick"
        @node-contextmenu="handleNodeContextMenu"
      >
        <template #default="{ node, data }">
          <div class="custom-node">
            <div class="node-content">
              <el-icon class="node-icon">
                <component :is="data.children && data.children.length > 0 ? 'FolderOpened' : 'Folder'" />
              </el-icon>
              <span class="node-label" :title="node.label">{{ node.label }}</span>
              <span v-if="data.file_count !== undefined" class="file-count">
                ({{ data.file_count }})
              </span>
            </div>

            <div class="node-actions" v-if="!data.isRoot">
              <el-dropdown @command="handleCommand($event, data)" trigger="click">
                <el-icon class="more-icon"><MoreFilled /></el-icon>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="create">
                      <el-icon><FolderAdd /></el-icon>
                      新建子文件夹
                    </el-dropdown-item>
                    <el-dropdown-item command="rename">
                      <el-icon><Edit /></el-icon>
                      重命名
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" divided>
                      <el-icon><Delete /></el-icon>
                      删除
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>
      </el-tree>
    </div>

    <!-- 新建/编辑文件夹对话框 -->
    <el-dialog
      v-model="folderDialogVisible"
      :title="isEditMode ? '编辑文件夹' : '新建文件夹'"
      width="400px"
    >
      <el-form :model="folderForm" label-width="80px">
        <el-form-item label="文件夹名称">
          <el-input
            v-model="folderForm.name"
            placeholder="请输入文件夹名称"
            maxlength="50"
            show-word-limit
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="folderDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmFolder" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getFolderList, createFolder, updateFolder, deleteFolder } from '@/api/folder'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Folder, FolderAdd, FolderOpened, Edit, Delete, MoreFilled
} from '@element-plus/icons-vue'

const props = defineProps({
  canCreateFolder: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['select', 'refresh'])

// 树形数据
const loading = ref(false)
const treeData = ref([])
const treeRef = ref(null)

// 树形配置
const treeProps = {
  children: 'children',
  label: 'name'
}

// 对话框
const folderDialogVisible = ref(false)
const isEditMode = ref(false)
const submitting = ref(false)
const folderForm = ref({
  id: null,
  name: '',
  parent_id: 0
})

// 加载文件夹树
const loadFolderTree = async () => {
  loading.value = true
  try {
    const res = await getFolderList()
    if (res.code === 200) {
      // 添加根节点
      const rootFolder = {
        id: 0,
        name: '全部文件',
        isRoot: true,
        children: res.data.folders || [],
        file_count: 0
      }
      // 确保所有节点都有children数组
      const ensureChildrenArray = (nodes) => {
        if (!Array.isArray(nodes)) return []
        return nodes.map(node => ({
          ...node,
          children: ensureChildrenArray(node.children)
        }))
      }
      rootFolder.children = ensureChildrenArray(rootFolder.children)
      treeData.value = [rootFolder]
    }
  } catch (error) {
    console.error('加载文件夹树失败:', error)
    ElMessage.error('加载文件夹树失败')
  } finally {
    loading.value = false
  }
}

// 节点点击
const handleNodeClick = (data) => {
  emit('select', data)
}

// 节点右键菜单
const handleNodeContextMenu = (event, data) => {
  // 阻止默认右键菜单
  event.preventDefault()
  event.stopPropagation()

  if (!data.isRoot) {
    // TODO: 可以添加自定义右键菜单
  }
}

// 新建文件夹
const handleCreateFolder = (parentId = 0) => {
  // 确保parentId是数字，防止事件对象被传入
  const folderId = (typeof parentId === 'number') ? parentId : 0

  isEditMode.value = false
  folderForm.value = {
    id: null,
    name: '',
    parent_id: folderId
  }
  folderDialogVisible.value = true
}

// 编辑文件夹
const handleRename = (folder) => {
  isEditMode.value = true
  folderForm.value = {
    id: folder.id,
    name: folder.name,
    parent_id: folder.parent_id
  }
  folderDialogVisible.value = true
}

// 删除文件夹
const handleDeleteFolder = (folder) => {
  ElMessageBox.confirm(
    `确定要删除文件夹"${folder.name}"吗？删除后文件夹内的所有文档将被移至根目录。`,
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    }
  ).then(async () => {
    try {
      await deleteFolder(folder.id)
      ElMessage.success('删除成功')
      await loadFolderTree()
      emit('refresh')
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 下拉菜单命令
const handleCommand = (command, data) => {
  switch (command) {
    case 'create':
      handleCreateFolder(data.id)
      break
    case 'rename':
      handleRename(data)
      break
    case 'delete':
      handleDeleteFolder(data)
      break
  }
}

// 确认新建/编辑
const handleConfirmFolder = async () => {
  if (!folderForm.value.name.trim()) {
    ElMessage.warning('文件夹名称不能为空')
    return
  }

  submitting.value = true
  try {
    if (isEditMode.value) {
      // 编辑
      await updateFolder(folderForm.value.id, {
        name: folderForm.value.name
      })
      ElMessage.success('修改成功')
    } else {
      // 新建 - 确保parent_id是数字类型
      const parentId = parseInt(folderForm.value.parent_id) || 0
      await createFolder({
        name: folderForm.value.name,
        parent_id: parentId
      })
      ElMessage.success('创建成功')
    }

    folderDialogVisible.value = false
    await loadFolderTree()
    emit('refresh')
  } catch (error) {
    ElMessage.error(isEditMode.value ? '修改失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

// 设置当前选中的节点
const setCurrentKey = (key) => {
  treeRef.value?.setCurrentKey(key)
}

// 刷新
const refresh = () => {
  loadFolderTree()
}

// 暴露方法给父组件
defineExpose({
  refresh,
  setCurrentKey
})

onMounted(() => {
  loadFolderTree()
})
</script>

<style scoped>
.folder-tree {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
}

.tree-header {
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

.tree-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

/* 自定义节点样式 */
.custom-node {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-right: 10px;
}

.node-content {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 6px;
  overflow: hidden;
}

.node-icon {
  font-size: 18px;
  color: #409eff;
  flex-shrink: 0;
}

.node-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 14px;
}

.file-count {
  font-size: 12px;
  color: #999;
  margin-left: 4px;
}

.node-actions {
  opacity: 0;
  transition: opacity 0.3s;
  flex-shrink: 0;
}

.custom-node:hover .node-actions {
  opacity: 1;
}

.more-icon {
  font-size: 16px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s;
}

.more-icon:hover {
  color: #409eff;
}

/* Element Plus Tree 样式覆盖 */
:deep(.el-tree) {
  background: transparent;
}

:deep(.el-tree-node__content) {
  height: 36px;
  border-radius: 4px;
  transition: background 0.3s;
}

:deep(.el-tree-node__content:hover) {
  background: #f5f7fa;
}

:deep(.el-tree-node.is-current > .el-tree-node__content) {
  background: #e6f7ff;
  color: #409eff;
}

:deep(.el-tree-node__expand-icon) {
  color: #999;
}

/* 滚动条样式 */
.tree-content::-webkit-scrollbar {
  width: 6px;
}

.tree-content::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.tree-content::-webkit-scrollbar-thumb:hover {
  background: #c0c4cc;
}
</style>
