/**
 * Vue Router 配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/store/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/share/:shareCode',
    name: 'ShareAccess',
    component: () => import('@/views/ShareAccess.vue'),
    meta: { title: '分享访问', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/views/Layout.vue'),
    redirect: '/dashboard',
    meta: { requiresAuth: true },
    children: [
      {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页', icon: 'House' }
      },
      {
        path: '/files',
        name: 'FileManager',
        component: () => import('@/views/FileManager.vue'),
        meta: { title: '文件管理', icon: 'Folder' }
      },
      {
        path: '/share',
        name: 'Share',
        component: () => import('@/views/Share.vue'),
        meta: { title: '我的分享', icon: 'Share' }
      },
      {
        path: '/trash',
        name: 'Trash',
        component: () => import('@/views/Trash.vue'),
        meta: { title: '回收站', icon: 'Delete' }
      },
      {
        path: '/statistics',
        name: 'Statistics',
        component: () => import('@/views/Statistics.vue'),
        meta: { title: '数据统计', icon: 'DataAnalysis' }
      }
    ]
  },
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在' }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()
  const isAuthenticated = userStore.isLogin

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 智能文档管理系统` : '智能文档管理系统'

  // 检查是否需要登录
  if (to.meta.requiresAuth) {
    if (!isAuthenticated) {
      next('/login')
      return
    }
  }

  // 如果已登录，访问登录页时跳转到首页
  if (isAuthenticated && (to.path === '/login' || to.path === '/register')) {
    next('/')
    return
  }

  next()
})

export default router
