/**
 * Pinia Store
 * 用户状态管理
 */
import { defineStore } from 'pinia'
import { login, logout, getUserInfo } from '@/api/auth'
import { ElMessage } from 'element-plus'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),

  getters: {
    isLogin: (state) => !!state.token,
    username: (state) => state.user?.username || '',
    isAdmin: (state) => state.user?.role === 'admin',
    avatar: (state) => state.user?.avatar || ''
  },

  actions: {
    /**
     * 用户登录
     */
    async login(loginForm) {
      const { username, password } = loginForm

      try {
        const res = await login({ username, password })

        // 保存token
        this.token = 'dummy-token' // 实际应该从后端返回
        localStorage.setItem('token', this.token)

        // 保存用户信息
        this.user = res.data.user
        localStorage.setItem('user', JSON.stringify(this.user))

        ElMessage.success('登录成功')
        return true
      } catch (error) {
        ElMessage.error('登录失败')
        return false
      }
    },

    /**
     * 用户退出
     */
    async logout() {
      try {
        await logout()
      } catch (error) {
        console.error('退出失败:', error)
      } finally {
        this.token = ''
        this.user = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')

        ElMessage.success('已退出登录')
      }
    },

    /**
     * 获取用户信息
     */
    async getUserInfo() {
      if (!this.token) return null

      try {
        const res = await getUserInfo()
        this.user = res.data.user
        localStorage.setItem('user', JSON.stringify(this.user))
        return this.user
      } catch (error) {
        this.logout()
        return null
      }
    },

    /**
     * 更新用户信息
     */
    updateUser(userInfo) {
      this.user = { ...this.user, ...userInfo }
      localStorage.setItem('user', JSON.stringify(this.user))
    }
  }
})
