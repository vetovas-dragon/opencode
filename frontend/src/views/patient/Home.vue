<template>
  <div>
    <van-cell-group inset title="在线问诊">
      <van-cell title="发起问诊" is-link @click="start" />
      <van-cell v-for="c in convs" :key="c.id" :title="`会话 #${c.id}`" :label="`${c.status === 'active' ? '进行中' : '已结束'} · ${c.created_at}`" is-link @click="openConv(c)" />
    </van-cell-group>
    <van-cell-group inset title="服务说明" style="margin-top: 12px">
      <van-cell title="支持汉语/彝语语音交流" icon="audio" />
      <van-cell title="紧急情况请及时线下就医" icon="warning-o" />
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { showSuccessToast } from 'vant'
import http from '@/api/http'

const router = useRouter()
const convs = ref<any[]>([])

async function start() {
  await http.post('/conversations', { doctor_direct: false })
  showSuccessToast('会话已创建')
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
