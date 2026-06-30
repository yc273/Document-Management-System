<template>
  <div class="statistics">
    <el-card>
      <template #header>
        <span>数据统计</span>
      </template>

      <el-row :gutter="20">
        <el-col :span="24">
          <div class="placeholder">
            <el-empty description="统计功能开发中，敬请期待..." />
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
// 统计页面（占位）
</script>

<style scoped>
.statistics {
  padding: 0;
}

.placeholder {
  padding: 60px 0;
}
</style>
