<template>
  <el-container class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '200px'" class="layout-aside">
      <div class="logo">
        <el-icon v-if="!isCollapse" class="logo-icon"><Document /></el-icon>
        <span v-if="!isCollapse" class="logo-text">文档管理</span>
        <el-icon v-else class="logo-icon-mini"><Document /></el-icon>
      </div>

      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        :unique-opened="true"
        router
        class="layout-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-menu-item index="/files">
          <el-icon><Folder /></el-icon>
          <template #title>文件管理</template>
        </el-menu-item>

        <el-menu-item index="/share">
          <el-icon><Share /></el-icon>
          <template #title>我的分享</template>
        </el-menu-item>

        <el-menu-item index="/trash">
          <el-icon><Delete /></el-icon>
          <template #title>回收站</template>
        </el-menu-item>

        <el-menu-item index="/statistics">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据统计</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 移动端抽屉菜单 -->
    <el-drawer
      v-model="mobileDrawer"
      :with-header="false"
      size="200px"
      direction="ltr"
      class="mobile-drawer"
    >
      <div class="logo">
        <el-icon class="logo-icon"><Document /></el-icon>
        <span class="logo-text">文档管理</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :unique-opened="true"
        router
        class="layout-menu"
        @select="mobileDrawer = false"
      >
        <el-menu-item index="/dashboard">
          <el-icon><House /></el-icon>
          <template #title>首页</template>
        </el-menu-item>
        <el-menu-item index="/files">
          <el-icon><Folder /></el-icon>
          <template #title>文件管理</template>
        </el-menu-item>
        <el-menu-item index="/share">
          <el-icon><Share /></el-icon>
          <template #title>我的分享</template>
        </el-menu-item>
        <el-menu-item index="/trash">
          <el-icon><Delete /></el-icon>
          <template #title>回收站</template>
        </el-menu-item>
        <el-menu-item index="/statistics">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据统计</template>
        </el-menu-item>
      </el-menu>
    </el-drawer>

    <!-- 主内容区 -->
    <el-container class="layout-main">
      <!-- 顶部栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <!-- 桌面端折叠按钮 -->
          <el-icon class="collapse-icon desktop-only" @click="toggleCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>
          <!-- 移动端菜单按钮 -->
          <el-icon class="collapse-icon mobile-only" @click="mobileDrawer = true">
            <Fold />
          </el-icon>

          <el-breadcrumb separator="/">
            <el-breadcrumb-item>{{ currentPageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>

        <div class="header-right">
          <!-- 用户信息 -->
          <el-dropdown class="user-dropdown" @command="handleCommand">
            <div class="user-info">
              <el-avatar :size="32" :src="user.avatar">
                <el-icon><UserFilled /></el-icon>
              </el-avatar>
              <span class="username">{{ user.username }}</span>
              <el-icon class="dropdown-icon"><ArrowDown /></el-icon>
            </div>

            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人信息
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/store/user'
import { ElMessageBox } from 'element-plus'
import {
  Document, House, Folder, Share, Delete, DataAnalysis,
  Fold, Expand, UserFilled, ArrowDown, User, SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 侧边栏折叠状态
const isCollapse = ref(false)

// 移动端抽屉
const mobileDrawer = ref(false)

// 用户信息
const user = computed(() => userStore.user || {})

// 当前激活的菜单
const activeMenu = computed(() => route.path)

// 当前页面标题
const currentPageTitle = computed(() => {
  return route.meta.title || '首页'
})

// 切换侧边栏
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 处理下拉菜单命令
const handleCommand = (command) => {
  switch (command) {
    case 'profile':
      // 跳转到个人信息页
      ElMessage.info('个人信息功能开发中...')
      break
    case 'logout':
      // 退出登录
      ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        userStore.logout()
        router.push('/login')
      }).catch(() => {})
      break
  }
}
</script>

<style scoped>
.layout-container {
  width: 100%;
  height: 100%;
}

/* 侧边栏样式 */
.layout-aside {
  background: #304156;
  transition: width 0.3s;
  overflow: hidden;
}

.logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b3a4d;
  color: #fff;
}

.logo-icon {
  font-size: 24px;
  margin-right: 8px;
}

.logo-text {
  font-size: 18px;
  font-weight: bold;
}

.logo-icon-mini {
  font-size: 24px;
}

.layout-menu {
  border-right: none;
  background: #304156;
}

/* 顶部栏样式 */
.layout-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-icon {
  font-size: 20px;
  cursor: pointer;
  margin-right: 20px;
  transition: color 0.3s;
}

.collapse-icon:hover {
  color: #409eff;
}

.header-right {
  display: flex;
  align-items: center;
}

.user-dropdown {
  cursor: pointer;
}

.user-info {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background 0.3s;
}

.user-info:hover {
  background: #f5f5f5;
}

.username {
  margin: 0 8px 0 12px;
  font-size: 14px;
  color: #333;
}

.dropdown-icon {
  font-size: 12px;
  color: #999;
}

/* 内容区样式 */
.layout-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 桌面端隐藏/显示 */
@media (min-width: 769px) {
  .mobile-only {
    display: none !important;
  }
}

/* 移动端样式 */
@media (max-width: 768px) {
  .desktop-only {
    display: none !important;
  }

  .layout-aside {
    display: none !important;
  }

  .layout-header {
    padding: 0 12px !important;
  }

  .layout-content {
    padding: 12px !important;
  }

  .header-left {
    min-width: 0 !important;
  }
}

/* 移动端抽屉菜单背景色 */
:deep(.mobile-drawer) {
  background: #304156;
}

:deep(.mobile-drawer .el-drawer__body) {
  padding: 0;
  background: #304156;
}

:deep(.mobile-drawer .logo) {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #2b3a4d;
  color: #fff;
}

:deep(.mobile-drawer .logo-icon) {
  font-size: 24px;
  margin-right: 8px;
}

:deep(.mobile-drawer .logo-text) {
  font-size: 18px;
  font-weight: bold;
}

:deep(.mobile-drawer .el-menu) {
  border-right: none;
  background: #304156;
}
</style>
