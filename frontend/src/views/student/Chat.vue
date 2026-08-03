<template>
  <div>
    <h3>在线问诊</h3>
    <el-select v-model="conversationId" placeholder="选择会话" style="width: 240px" @change="conversationId ? (conversationId = conversationId) : null">
      <el-option v-for="c in convs" :key="c.id" :value="c.id" :label="`会话 #${c.id}（${c.status}）`" />
    </el-select>
    <el-button v-if="conversationId && isActive" type="danger" plain @click="endConv">结束问诊</el-button>

    <el-card v-if="conversationId" class="chat-card">
      <el-button type="primary" plain size="small" @click="loadCard">查看患者档案悬浮信息</el-button>
      <el-popover v-if="card" :visible="cardVisible" trigger="click" placement="right">
        <template #reference>
          <el-button size="small" plain style="margin-left: 8px" @click="cardVisible = !cardVisible">档案卡片</el-button>
        </template>
        <div style="max-width: 260px">
          <div><b>{{ card.name }}</b>（{{ card.gender || '-' }} · {{ card.ethnicity || '-' }}）</div>
          <div>手机号：{{ card.phone }}</div>
          <div v-if="card.birth_date">出生日期：{{ card.birth_date }}</div>
          <div v-if="card.address">住址：{{ card.address }}</div>
          <div v-if="card.allergy_history">过敏史：{{ card.allergy_history }}</div>
          <div>最近活跃：{{ card.last_activity || '-' }}</div>
          <div v-if="card.recent_health?.length" style="margin-top: 6px; border-top: 1px solid #eee; padding-top: 6px">
            <div style="font-weight: 600; margin-bottom: 4px">最近健康数据</div>
            <div v-for="h in card.recent_health" :key="h.id" :class="{ abnormal: h.is_abnormal }">
              {{ h.metric_type }}: {{ h.value_primary }}{{ h.value_secondary ? '/' + h.value_secondary : '' }}{{ h.unit }}（{{ h.measured_at.slice(5, 16).replace('T', ' ') }}）{{ h.is_abnormal ? '· 异常' : '' }}
            </div>
          </div>
        </div>
      </el-popover>
      <el-button size="small" plain style="margin-left: 8px" @click="translateDraft">汉→彝互转</el-button>

      <ChatPanel v-if="conversationId" :conversation-id="conversationId" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRoute } from 'vue-router'
import http from '@/api/http'
import ChatPanel from '@/components/ChatPanel.vue'

const route = useRoute()
const convs = ref<any[]>([])
const conversationId = ref<number | null>(route.query.id ? Number(route.query.id) : null)
const card = ref<any>(null)
const cardVisible = ref(false)

const isActive = computed(() => {
  const c = convs.value.find((x) => x.id === conversationId.value)
  return c?.status === 'active'
})

async function load() {
  convs.value = await http.get('/student/conversations')
}

async function loadCard() {
  if (!conversationId.value) return
  card.value = await http.get(`/student/conversations/${conversationId.value}/patient-card`)
}

async function translateDraft() {
  const res: any = await http.post('/voice/translate', { source_text: '您好，医生为您解答健康问题。', source_lang: 'zh', target_lang: 'yi' })
  ElMessage.success(`彝语译文：${res.target_text}`)
}

async function endConv() {
  if (!conversationId.value) return
  const res: any = await http.post(`/conversations/${conversationId.value}/end`, { conversation_id: conversationId.value })
  ElMessage.info(res.message)
  load()
}

onMounted(load)
</script>

<style scoped>
.chat-card { margin-top: 16px; }
.abnormal { color: #f56c6c; }
</style>
