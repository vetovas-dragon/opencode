<template>
  <div>
    <van-cell-group inset title="我的档案">
      <van-field v-model="profile.name" label="姓名" readonly />
      <van-field v-model="profile.gender" label="性别" readonly />
      <van-field v-model="profile.birth_date" label="出生日期" readonly />
      <van-field v-model="profile.ethnicity" label="民族" readonly />
      <van-field v-model="profile.phone" label="手机号" readonly />
      <van-field v-model="profile.address" label="住址" />
      <van-field v-model="profile.allergy_history" label="过敏史" type="textarea" rows="2" />
      <van-field v-model="profile.language_pref" label="语言偏好" readonly />
    </van-cell-group>
    <div style="padding: 16px">
      <van-button type="primary" block @click="save">保存修改</van-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive } from 'vue'
import { showSuccessToast } from 'vant'
import http from '@/api/http'

const profile = reactive<any>({})

async function load() {
  Object.assign(profile, await http.get('/patient/profile'))
}

async function save() {
  await http.put('/patient/profile', { address: profile.address, allergy_history: profile.allergy_history })
  showSuccessToast('已保存')
}

onMounted(load)
</script>
