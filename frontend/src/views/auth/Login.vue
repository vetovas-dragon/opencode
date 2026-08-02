<template>
  <div class="login-page">
    <el-card class="login-card">
      <h2>在线问诊教学系统</h2>
      <el-form :model="form" label-width="80px" @submit.prevent>
        <el-form-item label="账号">
          <el-input v-model="form.contact" placeholder="手机号或邮箱" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password placeholder="登录密码" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" style="width: 100%" @click="doLogin">登 录</el-button>
        </el-form-item>
      </el-form>
      <div class="footer">
        <el-button link type="primary" @click="$router.push('/register')">没有账号？立即注册</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ contact: '', password: '' })

async function doLogin() {
  if (!form.contact || !form.password) {
    ElMessage.warning('请输入账号与密码')
    return
  }
  loading.value = true
  try {
    const role = await userStore.login(form.contact, form.password)
    router.push(`/${role}`)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page { height: 100vh; display: flex; align-items: center; justify-content: center; background: #f0f2f5; }
.login-card { width: 420px; }
.footer { text-align: center; }
</style>
