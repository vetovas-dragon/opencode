<template>
  <div class="register-page">
    <el-card class="register-card">
      <h2>注册账号</h2>
      <el-steps :active="step" finish-status="success" simple>
        <el-step title="选择角色" />
        <el-step title="填写信息" />
      </el-steps>

      <template v-if="step === 0">
        <el-radio-group v-model="form.role" class="role-group">
          <el-radio-button value="doctor">医生</el-radio-button>
          <el-radio-button value="student">医学生</el-radio-button>
          <el-radio-button value="patient">患者</el-radio-button>
        </el-radio-group>
        <div class="tips">医生/医学生注册后需管理员人工审核；患者注册即时生效。</div>
        <el-button type="primary" style="width: 100%" @click="step = 1">下一步</el-button>
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
            <el-button type="primary" style="width: 100%" :loading="loading" @click="submit">提交注册</el-button>
          </el-form-item>
        </el-form>
        <el-button link type="primary" @click="step = 0">返回上一步</el-button>
      </template>
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
const step = ref(0)
const sending = ref(false)
const loading = ref(false)
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
    ElMessage.success('验证码已发送')
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
      ElMessage.success(res.need_review ? '注册成功，请等待管理员审核' : '注册成功')
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
.register-page { min-height: 100vh; display: flex; align-items: center; justify-content: center; background: #f0f2f5; padding: 24px; }
.register-card { width: 560px; }
.role-group { margin: 16px 0; }
.tips { color: #909399; font-size: 12px; margin-bottom: 16px; }
</style>
