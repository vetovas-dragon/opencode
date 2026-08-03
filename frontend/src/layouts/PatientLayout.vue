<template>
  <div class="patient-layout">
    <van-nav-bar class="nav" title="在线问诊教学系统" />
    <main class="content"><router-view /></main>
    <van-tabbar route>
      <van-tabbar-item replace to="/patient/home" icon="home-o">首页</van-tabbar-item>
      <van-tabbar-item replace to="/patient/chat" icon="chat-o" :badge="unread || undefined">问诊</van-tabbar-item>
      <van-tabbar-item replace to="/patient/health" icon="bar-chart-o">健康数据</van-tabbar-item>
      <van-tabbar-item replace to="/patient/reminders" icon="bell-o">提醒</van-tabbar-item>
      <van-tabbar-item replace to="/patient/profile" icon="user-o">我的</van-tabbar-item>
    </van-tabbar>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import http from '@/api/http'

const router = useRouter()
const userStore = useUserStore()
const unread = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

async function pollUnread() {
  try {
    const res: any = await http.get('/conversations/unread-total')
    unread.value = res.unread_total
  } catch {
    /* 未登录时忽略 */
  }
}

onMounted(() => {
  if (!userStore.token) router.push('/login')
  else {
    pollUnread()
    timer = setInterval(pollUnread, 30000)
  }
})
onUnmounted(() => timer && clearInterval(timer))
</script>

<style scoped>
.nav :deep(.van-nav-bar__title) { color: #fff; }
.nav :deep(.van-nav-bar__content) { justify-content: center; }
.nav { background: linear-gradient(90deg, #0f1c35, #1677ff); }
.content { padding: 12px 12px 64px; }
.patient-layout :deep(.van-tabbar) { border-top: 1px solid #f0f2f5; }
</style>
