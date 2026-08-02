<template>
  <div>
    <h3>工作台</h3>
    <el-card v-for="c in convs" :key="c.id" style="margin-bottom: 12px">
      <div>会话 #{{ c.id }}（患者 #{{ c.patient_id }}）</div>
      <el-tag :type="c.status === 'active' ? 'success' : 'info'">
        {{ c.status === 'active' ? '进行中' : '已结束' }}
      </el-tag>
      <el-button v-if="c.status === 'active'" size="small" type="primary" @click="goChat(c.id)">进入问诊</el-button>
      <el-button v-if="c.status === 'ended' && !c.summary_triggered" size="small" type="warning" @click="goSummaries">
        待填写总结
      </el-button>
    </el-card>
    <el-empty v-if="!convs.length" description="暂无会话" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'

const router = useRouter()
const convs = ref<any[]>([])

async function load() {
  convs.value = await http.get('/student/conversations')
}

function goChat(id: number) {
  router.push({ path: '/student/chat', query: { id } })
}

function goSummaries() {
  router.push('/student/summaries')
}

onMounted(load)
</script>
