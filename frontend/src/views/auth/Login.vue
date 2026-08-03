<template>
  <div class="auth-page login">
    <div class="auth-side">
      <div class="brand">
        <div class="logo">问诊</div>
        <h1>在线问诊教学系统</h1>
        <p>民族语言医患沟通实训平台<br />支持彝语语音互转 · 医学生实训 · 带教审核</p>
      </div>
    </div>
    <div class="auth-main">
      <el-card class="auth-card" shadow="never">
        <h2>欢迎回来</h2>
        <p class="sub">登录你的账号</p>
        <el-form :model="form" label-position="top" @submit.prevent>
          <el-form-item label="账号">
            <el-input v-model="form.contact" size="large" placeholder="手机号或邮箱" :prefix-icon="User" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="form.password" size="large" type="password" show-password placeholder="登录密码" :prefix-icon="Lock" />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" size="large" :loading="loading" style="width: 100%" @click="doLogin">登 录</el-button>
          </el-form-item>
        </el-form>
        <div class="footer">
          <el-button link type="primary" @click="$router.push('/register')">没有账号？立即注册</el-button>
        </div>
        <el-divider><span class="divider-text">演示账号（直接点击登录）</span></el-divider>
        <div class="demo-list">
          <el-tag v-for="d in demoAccounts" :key="d.contact" class="demo-tag" effect="plain" @click="fill(d)">
            {{ d.role }} · {{ d.contact }}
          </el-tag>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const form = reactive({ contact: '', password: '' })

const demoAccounts = [
  { role: '患者', contact: '13800000001' },
  { role: '医学生', contact: '13800000011' },
  { role: '医生', contact: '13800000021' },
]

function fill(d: { contact: string }) {
  form.contact = d.contact
  form.password = 'Test1234'
  doLogin()
}

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
.auth-page {
  min-height: 100vh;
  display: flex;
  background: #eef3fb;
}
.auth-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f1c35 0%, #16325e 55%, #1677ff 130%);
  color: #fff;
}
.auth-side .brand { text-align: center; padding: 24px; }
.auth-side .logo {
  width: 64px;
  height: 64px;
  margin: 0 auto 20px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.25);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 2px;
}
.auth-side h1 { font-size: 30px; margin: 0 0 14px; font-weight: 600; }
.auth-side p { color: rgba(255, 255, 255, 0.72); font-size: 14px; line-height: 1.9; margin: 0; }
.auth-main { width: 460px; display: flex; align-items: center; justify-content: center; padding: 24px; }
.auth-card { width: 100%; border-radius: 16px; box-shadow: var(--otc-card-shadow); padding: 8px 12px; }
.auth-card h2 { margin: 4px 0 4px; font-size: 24px; }
.auth-card .sub { color: #8a94a6; margin: 0 0 22px; }
.footer { text-align: center; }
.divider-text { color: #a0a9b8; font-size: 12px; }
.demo-list { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; }
.demo-tag { cursor: pointer; transition: transform 0.15s; }
.demo-tag:hover { transform: translateY(-1px); }
@media (max-width: 900px) {
  .auth-side { display: none; }
}
</style>
