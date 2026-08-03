<template>
  <div>
    <div class="page-title">审核中心（问诊总结 / 实训计划）</div>
    <el-tabs v-model="tab">
      <el-tab-pane label="问诊总结" name="summary">
        <el-table :data="pending.summaries" border stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="student_id" label="学生ID" width="90" />
          <el-table-column prop="chief_complaint" label="主诉" width="160" />
          <el-table-column prop="present_illness" label="现病史" show-overflow-tooltip />
          <el-table-column prop="initial_diagnosis" label="初步判断" width="140" />
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="review('summary', row, 'pass')">通过</el-button>
              <el-button size="small" type="danger" plain @click="reject('summary', row)">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="实训计划" name="plan">
        <el-table :data="pending.plans" border stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="student_id" label="学生ID" width="90" />
          <el-table-column prop="title" label="计划名称" />
          <el-table-column prop="goal" label="目标" show-overflow-tooltip />
          <el-table-column label="操作" width="220">
            <template #default="{ row }">
              <el-button size="small" type="success" @click="review('plan', row, 'pass')">通过</el-button>
              <el-button size="small" type="danger" plain @click="reject('plan', row)">驳回</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      <el-tab-pane label="评分管理" name="score">
        <el-table :data="passed" border stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="student_id" label="学生ID" width="90" />
          <el-table-column prop="conversation_id" label="会话ID" width="90" />
          <el-table-column prop="chief_complaint" label="主诉" show-overflow-tooltip />
          <el-table-column prop="created_at" label="提交时间" width="200" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="openScore(row)">评分</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="scoreVisible" title="实训评分（0-100 分制）" width="480">
      <el-form label-width="90px">
        <el-form-item label="问诊方法"><el-slider v-model="score.q_consultation" :max="100" /></el-form-item>
        <el-form-item label="病史采集"><el-slider v-model="score.q_history" :max="100" /></el-form-item>
        <el-form-item label="沟通表达"><el-slider v-model="score.q_communication" :max="100" /></el-form-item>
        <el-form-item label="总结撰写"><el-slider v-model="score.q_summary" :max="100" /></el-form-item>
        <el-form-item label="评语">
          <el-input v-model="score.comment" type="textarea" :rows="2" placeholder="必填" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="scoreVisible = false">取消</el-button>
        <el-button type="primary" @click="submitScore">提交评分</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const tab = ref('summary')
const pending = ref<{ summaries: any[]; plans: any[] }>({ summaries: [], plans: [] })
const passed = ref<any[]>([])
const scoreVisible = ref(false)
const score = reactive({ student_id: 0, summary_id: null as number | null, q_consultation: 0, q_history: 0, q_communication: 0, q_summary: 0, comment: '' })

async function load() {
  pending.value = await http.get('/reviews/pending')
  const data: any = await http.get('/reviews/passed')
  passed.value = data
}

async function review(type: string, row: any, result: string) {
  await http.post(`/reviews/${type}`, { target_id: row.id, result, comment: '' })
  ElMessage.success('审核完成')
  load()
}

async function reject(type: string, row: any) {
  const { value } = await ElMessageBox.prompt('请输入驳回意见（必填）', '驳回', { inputValidator: (v) => !!v })
  await http.post(`/reviews/${type}`, { target_id: row.id, result: 'reject', comment: value })
  ElMessage.success('已驳回')
  load()
}

function openScore(row: any) {
  Object.assign(score, { student_id: row.student_id, summary_id: row.id, q_consultation: 0, q_history: 0, q_communication: 0, q_summary: 0, comment: '' })
  scoreVisible.value = true
}

async function submitScore() {
  if (!score.comment.trim()) return ElMessage.warning('请填写评语')
  await http.post('/doctor/scores', score)
  ElMessage.success('评分已录入')
  scoreVisible.value = false
}

onMounted(load)
</script>
