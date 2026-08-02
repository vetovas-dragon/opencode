<template>
  <el-container class="layout">
    <el-aside width="220px">
      <div class="brand">在线问诊教学系统 · 医生端</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/doctor/students">学生管理</el-menu-item>
        <el-menu-item index="/doctor/records">
          <el-badge :value="unread" :hidden="!unread" class="menu-badge">
            <span>问诊记录</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="/doctor/reviews">审核中心</el-menu-item>
        <el-menu-item index="/doctor/stats">数据统计</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ userStore.name }}（医生）</span>
        <el-button link type="danger" @click="logout">退出登录</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
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
    /* 忽略 */
  }
}

onMounted(() => {
  pollUnread()
  timer = setInterval(pollUnread, 30000)
})
onUnmounted(() => timer && clearInterval(timer))

function logout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100vh; }
.brand { padding: 16px; font-weight: bold; }
.header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #eee; }
.menu-badge :deep(.el-badge__content) { right: -14px; top: 8px; }
</style>
