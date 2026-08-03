<template>
  <div>
    <van-cell-group inset title="在线问诊">
      <van-cell title="发起问诊" is-link @click="startVisible = true" />
      <van-cell v-for="c in convs" :key="c.id" :title="`会话 #${c.id}`" :label="`${c.status === 'active' ? '进行中' : '已结束'} · ${c.created_at}`" is-link @click="openConv(c)" />
    </van-cell-group>
    <van-cell-group inset title="语音服务" style="margin-top: 12px">
      <van-cell title="汉语 ⇄ 彝语 语音互转" label="按住说话，实时转写互译" icon="audio" is-link @click="$router.push('/patient/voice')" />
    </van-cell-group>
    <van-cell-group inset title="服务说明" style="margin-top: 12px">
      <van-cell title="支持汉语/彝语语音交流" icon="audio" />
      <van-cell title="紧急情况请及时线下就医" icon="warning-o" />
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
import http from '@/api/http'

const router = useRouter()
const convs = ref<any[]>([])
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
  convs.value = await http.get('/conversations/mine')
}

function openConv(c: any) {
  router.push({ path: '/patient/chat', query: { id: c.id } })
}

onMounted(load)
</script>
