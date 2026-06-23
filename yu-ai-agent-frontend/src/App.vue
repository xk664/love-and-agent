<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()

// 刷新后自动恢复用户信息（token 已在 store 初始化时从 localStorage 读取）
onMounted(async () => {
  if (userStore.isLoggedIn) {
    try {
      await userStore.fetchUserInfo()
    } catch {
      // token 已过期或无效，拦截器会处理 401 跳转
    }
  }
})
</script>
