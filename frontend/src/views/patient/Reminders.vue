<template>
  <div>
    <van-cell-group v-for="r in reminders" :key="r.id" inset title="我的提醒" style="margin-top: 8px">
      <van-cell :title="`${typeMap[r.reminder_type]}：${r.content}`" :label="`周期：${cycleMap[r.cycle]} · ${r.schedule_cron} · ${r.status === 'active' ? '生效中' : '已结束'}`" />
      <template v-if="r.logs.length">
        <van-cell title="最近发送记录" :label="r.logs.map((l: any) => `${l.sent_at.slice(5, 16).replace('T', ' ')} · ${feedbackMap[l.feedback || ''] || '待反馈'}`).join('；')" />
        <van-cell v-if="!r.logs[0].feedback" center title="本次是否完成？">
          <template #right-icon>
            <van-button size="mini" type="primary" @click="feedback(r, 'done')">已完成</van-button>
            <van-button size="mini" style="margin-left: 8px" plain @click="feedback(r, 'later')">稍后处理</van-button>
          </template>
        </van-cell>
      </template>
    </van-cell-group>
    <van-empty v-if="!reminders.length" description="暂无提醒" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { showSuccessToast } from 'vant'
import http from '@/api/http'

const reminders = ref<any[]>([])
const typeMap: Record<string, string> = { medication: '用药', measurement: '测量', follow_up: '复诊', lifestyle: '生活方式' }
const cycleMap: Record<string, string> = { once: '单次', daily: '每日', weekly: '每周', monthly: '每月' }
const feedbackMap: Record<string, string> = { done: '已完成', later: '稍后处理' }

async function load() {
  const list: any[] = await http.get('/patient/reminders')
  reminders.value = await Promise.all(
    list.map(async (r) => ({ ...r, logs: (await http.get(`/patient/reminders/${r.id}/logs`)) as any[] })),
  )
}

async function feedback(r: any, value: string) {
  await http.post(`/patient/reminders/${r.id}/feedback`, { feedback: value })
  showSuccessToast('已反馈')
  load()
}

onMounted(load)
</script>
