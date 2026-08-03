<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="brand">
        <div class="brand-logo">问诊</div>
        <div class="brand-text">
          <div class="brand-name">在线问诊教学系统</div>
          <div class="brand-role">医生端</div>
        </div>
      </div>
      <el-menu :default-active="$route.path" router class="side-menu">
        <el-menu-item index="/doctor/students">
          <el-icon><User /></el-icon><span>学生管理</span>
        </el-menu-item>
        <el-menu-item index="/doctor/intervene">
          <el-icon><FirstAidKit /></el-icon><span>接诊工作台</span>
        </el-menu-item>
        <el-menu-item index="/doctor/records">
          <el-badge :value="unread" :hidden="!unread" class="menu-badge">
            <el-icon><ChatDotRound /></el-icon><span>问诊记录</span>
          </el-badge>
        </el-menu-item>
        <el-menu-item index="/doctor/reviews">
          <el-icon><Checked /></el-icon><span>审核中心</span>
        </el-menu-item>
        <el-menu-item index="/doctor/stats">
          <el-icon><TrendCharts /></el-icon><span>数据统计</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="page-name">{{ pageName }}</div>
        <div class="user-box">
          <el-avatar :size="32" class="avatar">{{ avatarChar }}</el-avatar>
          <span class="user-name">{{ userStore.name }}</span>
          <el-tag size="small" type="primary" effect="plain">医生</el-tag>
          <el-button link type="danger" @click="logout">退出登录</el-button>
        </div>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { User, FirstAidKit, ChatDotRound, Checked, TrendCharts } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import http from '@/api/http'

const router = useRouter()
const userStore = useUserStore()
const unread = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const avatarChar = computed(() => (userStore.name || '医').slice(0, 1))

const pageName = computed(() => {
  const map: Record<string, string> = {
    '/doctor/students': '学生管理',
    '/doctor/intervene': '接诊工作台',
    '/doctor/records': '问诊记录',
    '/doctor/reviews': '审核中心',
    '/doctor/stats': '数据统计',
  }
  return map[router.currentRoute.value.path] || '医生端'
})

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
.aside {
  background: var(--otc-sidebar-bg);
  display: flex;
  flex-direction: column;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 18px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.brand-logo {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--otc-primary), #3aa0ff);
  color: #fff;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 1px;
  flex-shrink: 0;
}
.brand-name { color: #fff; font-size: 14px; font-weight: 600; white-space: nowrap; }
.brand-role { color: var(--otc-sidebar-text); font-size: 12px; margin-top: 2px; }
.side-menu {
  border-right: none;
  background: transparent;
  flex: 1;
  padding-top: 8px;
}
.side-menu :deep(.el-menu-item) {
  color: var(--otc-sidebar-text);
  height: 46px;
  line-height: 46px;
  margin: 2px 10px;
  border-radius: 8px;
}
.side-menu :deep(.el-menu-item:hover) { background: rgba(255, 255, 255, 0.08); color: #fff; }
.side-menu :deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, var(--otc-primary), #3aa0ff);
  color: #fff;
  font-weight: 600;
}
.side-menu :deep(.el-menu-item .el-icon) { margin-right: 8px; }
.menu-badge :deep(.el-badge__content) { right: 6px; top: 8px; border: none; }
.header {
  background: #fff;
  border-bottom: 1px solid #eef1f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 1px 4px rgba(31, 45, 80, 0.04);
}
.page-name { font-size: 16px; font-weight: 600; }
.user-box { display: flex; align-items: center; gap: 10px; }
.avatar { background: linear-gradient(135deg, var(--otc-primary), #3aa0ff); color: #fff; font-weight: 600; }
.user-name { font-weight: 500; }
.main { background: var(--otc-bg); padding: 20px; }
</style>
