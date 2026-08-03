<template>
  <div>
    <h3>问诊实训全程记录</h3>
    <el-timeline v-if="records.length">
      <el-timeline-item
        v-for="r in records"
        :key="r.conversation_id"
        :type="r.status === 'active' ? 'primary' : r.summary ? (r.summary.status === 'passed' ? 'success' : r.summary.status === 'rejected' ? 'danger' : 'warning') : 'info'"
        :timestamp="`${r.created_at.slice(0, 16).replace('T', ' ')}`"
      >
        <el-card shadow="never">
          <div style="display: flex; justify-content: space-between; align-items: center">
            <b>会话 #{{ r.conversation_id }}</b>
            <el-tag :type="r.status === 'active' ? 'success' : 'info'">{{ r.status === 'active' ? '进行中' : '已结束' }}</el-tag>
          </div>
          <el-descriptions v-if="r.summary" :column="1" border size="small" style="margin-top: 8px">
            <el-descriptions-item label="总结状态">
              <el-tag :type="r.summary.status === 'passed' ? 'success' : r.summary.status === 'pending' ? 'warning' : 'danger'" size="small">
                {{ summaryMap[r.summary.status] }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item v-if="r.summary.review_comment" label="审核意见">{{ r.summary.review_comment }}</el-descriptions-item>
            <template v-if="r.score">
              <el-descriptions-item label="实训评分">{{ r.score.total }} 分（{{ r.score.grade }}）</el-descriptions-item>
              <el-descriptions-item label="评分评语">{{ r.score.comment }}</el-descriptions-item>
            </template>
          </el-descriptions>
          <el-empty v-else description="尚未提交问诊总结" :image-size="50" />
        </el-card>
      </el-timeline-item>
    </el-timeline>
    <el-empty v-else description="暂无实训记录" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import http from '@/api/http'

const records = ref<any[]>([])
const summaryMap: Record<string, string> = { draft: '草稿', pending: '待审核', passed: '已通过', rejected: '已驳回' }

async function load() {
  records.value = await http.get('/student/records')
}

onMounted(load)
</script>
