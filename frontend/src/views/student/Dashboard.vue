<template>
  <div>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">我的问诊会话</div>
        <div class="value">{{ stats.total }}</div>
        <div class="extra">进行中 {{ stats.active }} · 已结束 {{ stats.ended }}</div>
      </div>
      <div class="stat-card alt1">
        <div class="label">待填写总结</div>
        <div class="value">{{ pendingSummaries }}</div>
        <div class="extra">已结束且未提交总结</div>
      </div>
      <div class="stat-card alt2">
        <div class="label">我的实训计划</div>
        <div class="value">{{ planCount }}</div>
        <div class="extra">持续练习，提升问诊能力</div>
      </div>
    </div>

    <div class="page-card">
      <div class="page-title">我的问诊会话</div>
      <el-table v-if="convs.length" :data="convs" stripe>
        <el-table-column prop="id" label="会话编号" width="110" />
        <el-table-column label="患者" width="120">
          <template #default="{ row }">患者 #{{ row.patient_id }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'" effect="light">
              {{ row.status === 'active' ? '进行中' : '已结束' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" min-width="200">
          <template #default="{ row }">
            <el-button v-if="row.status === 'active'" size="small" type="primary" @click="goChat(row.id)">进入问诊</el-button>
            <el-button v-if="row.status === 'ended' && !row.summary_triggered" size="small" type="warning" @click="goSummaries">待填写总结</el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无会话，去「在线问诊」接诊吧" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import http from '@/api/http'

const router = useRouter()
const convs = ref<any[]>([])
const stats = ref({ total: 0, active: 0, ended: 0 })
const pendingSummaries = ref(0)
const planCount = ref(0)

function summarize(rows: any[]) {
  const s = { total: rows.length, active: rows.filter((r) => r.status === 'active').length, ended: rows.filter((r) => r.status === 'ended').length }
  stats.value = s
  pendingSummaries.value = rows.filter((r) => r.status === 'ended' && !r.summary_triggered).length
}

async function load() {
  const rows: any[] = await http.get('/student/conversations')
  convs.value = rows
  summarize(rows)
  try {
    const plans: any[] = await http.get('/student/plans')
    planCount.value = plans.length
  } catch {
    planCount.value = 0
  }
}

function goChat(id: number) {
  router.push({ path: '/student/chat', query: { id } })
}

function goSummaries() {
  router.push('/student/summaries')
}

onMounted(load)
</script>