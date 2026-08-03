<template>
  <div>
    <div class="welcome-card">
      <div class="welcome-title">您好，{{ userStore.name }}</div>
      <div class="welcome-sub">今天也要关注健康哦</div>
      <div class="quick-row">
        <van-button type="primary" size="small" round icon="chat-o" @click="startVisible = true">发起问诊</van-button>
        <van-button type="warning" size="small" round icon="audio" @click="$router.push('/patient/voice')">语音互转</van-button>
      </div>
    </div>

    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">我的会话</div>
        <div class="value">{{ stats.total }}</div>
        <div class="extra">进行中 {{ stats.active }}</div>
      </div>
      <div class="stat-card alt1">
        <div class="label">健康数据记录</div>
        <div class="value">{{ healthCount }}</div>
        <div class="extra">血压 · 血糖 · 心率</div>
      </div>
      <div class="stat-card alt2">
        <div class="label">用药提醒</div>
        <div class="value">{{ reminderCount }}</div>
        <div class="extra">按时服药，守护健康</div>
      </div>
    </div>

    <van-cell-group inset title="在线问诊">
      <van-cell v-for="c in convs" :key="c.id" :title="`会话 #${c.id}`" :label="`${c.status === 'active' ? '进行中' : '已结束'} · ${c.created_at}`" is-link @click="openConv(c)" />
    </van-cell-group>
    <van-cell-group inset title="语音服务" style="margin-top: 12px">
      <van-cell title="汉语 ⇄ 彝语 语音互转" label="按住说话，实时转写互译" icon="audio" is-link @click="$router.push('/patient/voice')" />
    </van-cell-group>

    <van-action-sheet v-model:show="startVisible" title="发起问诊" :actions="startActions" @select="onStartSelect" />
    <van-popup v-model:show="doctorVisible" position="bottom" round style="padding: 16px" safe-area-inset-bottom>
      <div style="font-weight: 600; margin-bottom: 8px">选择直连医生</div>
      <van-radio-group v-model="selectedDoctor">
        <van-cell v-for="d in doctors" :key="d.id" :title="`${d.name}（${d.title || '医师'}）`" :label="`${d.practice_scope || ''} · ${d.organization || ''}`" clickable @click="selectedDoctor = d.id">
          <template #right-icon><van-radio :name="d.id" /></template>
        </van-cell>
      </van-radio-group>
      <van-empty v-if="!doctors.length" description="暂无可直连医生" />
      <van-button type="primary" block style="margin-top: 12px" :disabled="!selectedDoctor" @click="startDirect">确认发起</van-button>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast } from 'vant'
import { useUserStore } from '@/stores/user'
import http from '@/api/http'

const router = useRouter()
const userStore = useUserStore()
const convs = ref<any[]>([])
const stats = ref({ total: 0, active: 0 })
const healthCount = ref(0)
const reminderCount = ref(0)
const startVisible = ref(false)
const doctorVisible = ref(false)
const doctors = ref<any[]>([])
const selectedDoctor = ref<number | null>(null)

const startActions = [
  { name: '自动分配医学生接诊', value: 'auto' },
  { name: '直连医生问诊', value: 'direct' },
]

async function onStartSelect(action: any) {
  startVisible.value = false
  if (action.value === 'auto') {
    await http.post('/conversations', { doctor_direct: false })
    showSuccessToast('会话已创建')
    load()
  } else {
    doctors.value = await http.get('/conversations/doctors')
    doctorVisible.value = true
  }
}

async function startDirect() {
  if (!selectedDoctor.value) return
  await http.post('/conversations', { doctor_direct: true, doctor_id: selectedDoctor.value })
  doctorVisible.value = false
  showSuccessToast('已直连医生问诊')
  load()
}

async function load() {
  const rows: any[] = await http.get('/conversations/mine')
  convs.value = rows
  stats.value = {
    total: rows.length,
    active: rows.filter((r) => r.status === 'active').length,
  }
  try {
    const health: any = await http.get('/patients/health-records')
    healthCount.value = health?.items?.length ?? 0
  } catch {
    healthCount.value = 0
  }
  try {
    const reminders: any = await http.get('/patients/reminders')
    reminderCount.value = reminders?.items?.length ?? 0
  } catch {
    reminderCount.value = 0
  }
}

function openConv(c: any) {
  router.push({ path: '/patient/chat', query: { id: c.id } })
}

onMounted(load)
</script>

<style scoped>
.welcome-card {
  background: linear-gradient(135deg, #0f1c35 0%, #1677ff 120%);
  border-radius: 14px;
  padding: 20px;
  color: #fff;
  margin-bottom: 14px;
}
.welcome-title { font-size: 20px; font-weight: 700; }
.welcome-sub { color: rgba(255, 255, 255, 0.75); font-size: 13px; margin-top: 4px; }
.quick-row { margin-top: 14px; display: flex; gap: 10px; }
.quick-row :deep(.van-button--primary) { border-color: rgba(255, 255, 255, 0.4); }
</style>
