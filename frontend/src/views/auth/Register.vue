<template>
  <div class="register-page">
    <el-card class="register-card" shadow="never">
      <div class="head">
        <h2>注册账号</h2>
        <el-button link type="primary" @click="$router.push('/login')">已有账号？去登录</el-button>
      </div>
      <el-steps :active="step" finish-status="success" simple>
        <el-step title="选择角色" />
        <el-step title="填写信息" />
      </el-steps>

      <template v-if="step === 0">
        <div class="role-grid">
          <div
            v-for="r in roles"
            :key="r.value"
            class="role-item"
            :class="{ active: form.role === r.value }"
            @click="form.role = r.value"
          >
            <div class="role-icon">{{ r.icon }}</div>
            <div class="role-name">{{ r.label }}</div>
            <div class="role-desc">{{ r.desc }}</div>
          </div>
        </div>
        <div class="tips">{{ roleTip }}</div>
        <el-button type="primary" style="width: 100%" size="large" @click="step = 1">下一步</el-button>
      </template>

      <template v-else>
        <el-form :model="form" label-width="90px">
          <el-form-item label="手机号/邮箱">
            <el-input v-model="form.contact" placeholder="手机号或邮箱" />
            <el-button style="margin-left: 8px" :disabled="sending" @click="sendCode">{{ sending ? '已发送' : '获取验证码' }}</el-button>
          </el-form-item>
          <el-form-item label="验证码"><el-input v-model="form.code" placeholder="验证码" /></el-form-item>
          <el-form-item label="姓名"><el-input v-model="form.name" /></el-form-item>
          <el-form-item label="密码"><el-input v-model="form.password" type="password" show-password /></el-form-item>

          <!-- 医生执业信息 -->
          <template v-if="form.role === 'doctor'">
            <el-form-item label="执业证书编号"><el-input v-model="form.doctor.license_no" /></el-form-item>
            <el-form-item label="执业范围"><el-input v-model="form.doctor.practice_scope" /></el-form-item>
            <el-form-item label="执业机构"><el-input v-model="form.doctor.organization" /></el-form-item>
            <el-form-item label="职称"><el-input v-model="form.doctor.title" /></el-form-item>
          </template>

          <!-- 学生学籍信息 -->
          <template v-else-if="form.role === 'student'">
            <el-form-item label="院校"><el-input v-model="form.student.school" /></el-form-item>
            <el-form-item label="专业"><el-input v-model="form.student.major" /></el-form-item>
            <el-form-item label="年级"><el-input v-model="form.student.grade" /></el-form-item>
            <el-form-item label="学号"><el-input v-model="form.student.student_no" /></el-form-item>
          </template>

          <!-- 患者健康基础信息 -->
          <template v-else>
            <el-form-item label="性别">
              <el-radio-group v-model="form.patient.gender">
                <el-radio value="男">男</el-radio><el-radio value="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="出生日期"><el-input v-model="form.patient.birth_date" placeholder="如 1990-01-01" /></el-form-item>
            <el-form-item label="民族"><el-input v-model="form.patient.ethnicity" placeholder="如：彝族" /></el-form-item>
            <el-form-item label="语言偏好">
              <el-radio-group v-model="form.patient.language_pref">
                <el-radio value="zh">汉语</el-radio><el-radio value="yi">彝语</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="过敏史"><el-input v-model="form.patient.allergy_history" /></el-form-item>
          </template>

          <el-form-item>
            <el-button type="primary" style="width: 100%" size="large" :loading="loading" @click="submit">提交注册</el-button>
          </el-form-item>
        </el-form>
        <el-button link type="primary" @click="step = 0">返回上一步</el-button>
      </template>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const step = ref(0)
const sending = ref(false)
const loading = ref(false)

const roles = [
  { value: 'patient', label: '患者', icon: '🧑‍⚕️', desc: '即时生效，可立即问诊' },
  { value: 'student', label: '医学生', icon: '🎓', desc: '参与问诊实训、撰写总结' },
  { value: 'doctor', label: '医生', icon: '🩺', desc: '带教审核、接诊介入' },
]
const roleTip = computed(
  () => (form.role === 'patient' ? '患者注册后即时生效。' : '医生/医学生注册后需管理员人工审核，请耐心等待。'),
)

const form = reactive({
  contact: '',
  code: '',
  name: '',
  password: '',
  role: 'patient',
  doctor: { license_no: '', practice_scope: '', organization: '', title: '' },
  student: { school: '', major: '', grade: '', student_no: '' },
  patient: { gender: '男', birth_date: '', ethnicity: '', allergy_history: '', language_pref: 'zh' },
})

async function sendCode() {
  if (!form.contact) {
    ElMessage.warning('请先填写手机号或邮箱')
    return
  }
  sending.value = true
  try {
    await userStore.sendCode(form.contact)
    ElMessage.success('验证码已发送（演示环境可查看后端日志）')
  } finally {
    sending.value = false
  }
}

async function submit() {
  if (form.contact && form.code && form.name && form.password) {
    loading.value = true
    try {
      const res: any = await userStore.register({
        contact: form.contact,
        code: form.code,
        name: form.name,
        password: form.password,
        role: form.role,
        doctor: form.role === 'doctor' ? form.doctor : undefined,
        student: form.role === 'student' ? form.student : undefined,
        patient: form.role === 'patient' ? form.patient : undefined,
      })
      ElMessage.success(res.need_review ? '注册成功，请等待管理员审核' : '注册成功，请登录')
      router.push('/login')
    } finally {
      loading.value = false
    }
  } else {
    ElMessage.warning('请完整填写注册信息')
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0f1c35 0%, #16325e 55%, #1677ff 130%);
  padding: 32px 16px;
}
.register-card { width: 620px; border-radius: 16px; }
.head { display: flex; align-items: center; justify-content: space-between; }
.head h2 { margin: 4px 0 14px; font-size: 24px; }
.role-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 20px 0 12px; }
.role-item {
  border: 1.5px solid #e4e9f2;
  border-radius: 12px;
  padding: 16px 12px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfe;
}
.role-item:hover { border-color: var(--otc-primary); transform: translateY(-2px); }
.role-item.active { border-color: var(--otc-primary); background: var(--el-color-primary-light-9); }
.role-icon { font-size: 30px; }
.role-name { font-weight: 600; margin-top: 8px; }
.role-desc { color: #8a94a6; font-size: 12px; margin-top: 4px; line-height: 1.5; }
.tips { color: #909399; font-size: 12px; margin-bottom: 14px; }
</style>
