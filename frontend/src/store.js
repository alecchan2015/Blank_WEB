import { defineStore } from 'pinia'
import { authAPI } from './api'

export const useUserStore = defineStore('user', {
  state: () => ({
    user: null,
    token: localStorage.getItem('token') || null,
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin',
  },
  actions: {
    async login(username, password) {
      const res = await authAPI.login({ username, password })
      this.token = res.access_token
      this.user = res.user
      localStorage.setItem('token', res.access_token)
    },
    async fetchMe() {
      if (!this.token) return
      try {
        this.user = await authAPI.me()
      } catch {
        this.logout()
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('token')
    },
  },
})
