import { defineStore } from 'pinia'
import request from '@/utils/request'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: (localStorage.getItem('token') || '').trim(),
    username: (localStorage.getItem('username') || '').trim(),
    userId: null
  }),

  getters: {
    isLoggedIn: (state) => !!state.token
  },

  actions: {
    async login(username, password) {
      const res = await request({
        url: '/v1/user/login',
        method: 'post',
        data: { username, password }
      })
      const token = (res.data?.token || res.token || '').trim()
      this.token = token
      this.username = username
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
      return res
    },

    async register(username, password) {
      return await request({
        url: '/v1/user/register',
        method: 'post',
        data: { username, password }
      })
    },

    async fetchUserInfo() {
      const res = await request({
        url: '/v1/user/info',
        method: 'get'
      })
      const data = res.data || res
      this.username = data.username || this.username
      this.userId = data.id || data.userId || null
      localStorage.setItem('username', this.username)
      return data
    },

    logout() {
      this.token = ''
      this.username = ''
      this.userId = null
      localStorage.removeItem('token')
      localStorage.removeItem('username')
    }
  }
})
