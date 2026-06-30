<template>
  <div class="file-manager">
    <el-card class="file-card">
      <!-- 工具栏 -->
      <div class="toolbar">
        <el-button type="primary" @click="handleUpload">
          <el-icon><Upload /></el-icon>
          上传文档
        </el-button>

        <el-button @click="handleNewFolder">
          <el-icon><FolderAdd /></el-icon>
          新建文件夹
        </el-button>

        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            placeholder="搜索文档..."
            clearable
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>

      <!-- 文档列表 -->
      <el-table
        :data="fileList"
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="original_name" label="文件名" />
        <el-table-column prop="file_type" label="类型" width="100" />
        <el-table-column prop="file_size_readable" label="大小" width="120" />
        <el-table-column prop="created_at" label="上传时间" width="180" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" link @click="handleDownload(row)">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
            <el-button type="danger" size="small" link @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

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
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog v-model="uploadVisible" title="上传文档" width="500px">
      <el-upload
        ref="uploadRef"
        :action="uploadAction"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :auto-upload="false"
        drag
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
      </el-upload>

      <template #footer>
        <el-button @click="uploadVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmUpload">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getFileList, deleteFile, downloadFile } from '@/api/file'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, FolderAdd, Search, Download, Delete, UploadFilled } from '@element-plus/icons-vue'

const loading = ref(false)
const fileList = ref([])
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)
const uploadVisible = ref(false)
const uploadRef = ref(null)
const uploadAction = '/api/file/upload'

// 加载文档列表
const loadFiles = async () => {
  loading.value = true
  try {
    const res = await getFileList({
      page: currentPage.value,
      per_page: pageSize.value
    })
    if (res.code === 200) {
      fileList.value = res.data.files
      total.value = res.data.total
    }
  } catch (error) {
    console.error('加载文档列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  loadFiles()
}

// 上传文档
const handleUpload = () => {
  uploadVisible.value = true
}

// 确认上传
const handleConfirmUpload = () => {
  uploadRef.value?.submit()
}

// 上传成功
const handleUploadSuccess = (response) => {
  if (response.code === 200) {
    ElMessage.success('上传成功')
    uploadVisible.value = false
    loadFiles()
  }
}

// 上传失败
const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 新建文件夹
const handleNewFolder = () => {
  ElMessage.info('功能开发中...')
}

// 下载文档
const handleDownload = (row) => {
  const url = downloadFile(row.id)
  window.open(url, '_blank')
}

// 删除文档
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除文档"${row.original_name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await deleteFile(row.id)
      ElMessage.success('删除成功')
      loadFiles()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

// 分页
const handleSizeChange = () => {
  loadFiles()
}

const handleCurrentChange = () => {
  loadFiles()
}

onMounted(() => {
  loadFiles()
})
</script>

<style scoped>
.file-manager {
  height: 100%;
}

.file-card {
  height: 100%;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
}

.search-box {
  margin-left: auto;
  width: 300px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.el-icon--upload {
  font-size: 67px;
  color: #c0c4cc;
  margin: 40px 0 16px;
  line-height: 50px;
}
</style>
