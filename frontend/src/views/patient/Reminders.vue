<template>
  <div>
    <van-cell-group inset title="我的提醒">
      <van-cell v-for="r in reminders" :key="r.id" :title="`${typeMap[r.reminder_type]}：${r.content}`" :label="`周期：${cycleMap[r.cycle]} · ${r.schedule_cron} · ${r.status === 'active' ? '生效中' : '已结束'}`" />
    </van-cell-group>
    <van-empty v-if="!reminders.length" description="暂无提醒" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import http from '@/api/http'

const reminders = ref<any[]>([])
const typeMap: Record<string, string> = { medication: '用药', measurement: '测量', follow_up: '复诊', lifestyle: '生活方式' }
const cycleMap: Record<string, string> = { once: '单次', daily: '每日', weekly: '每周', monthly: '每月' }

async function load() {
  reminders.value = await http.get('/patient/reminders')
}

onMounted(load)
</script>
