<template>
  <el-container class="layout">
    <el-aside width="220px">
      <div class="brand">在线问诊教学系统 · 管理后台</div>
      <el-menu :default-active="$route.path" router>
        <el-menu-item index="/admin/review">身份审核</el-menu-item>
        <el-menu-item index="/admin/overview">全局概览</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <span>{{ userStore.name }}（管理员）</span>
        <el-button link type="danger" @click="logout">退出登录</el-button>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

function logout() {
  userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout { height: 100vh; }
.brand { padding: 16px; font-weight: bold; }
.header { display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #eee; }
</style>
