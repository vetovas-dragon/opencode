<template>
  <div>
    <h3>学生信息管理</h3>
    <el-form inline>
      <el-form-item label="关键词">
        <el-input v-model="query.keyword" placeholder="姓名/学号" clearable @keyup.enter="load" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
      </el-form-item>
    </el-form>
    <el-table :data="rows" border stripe>
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="school" label="院校" />
      <el-table-column prop="major" label="专业" width="140" />
      <el-table-column prop="grade" label="年级" width="100" />
      <el-table-column prop="student_no" label="学号" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
            {{ row.status === 'active' ? '正常' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="归属" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.mentor_doctor_id" type="warning">名下</el-tag>
          <el-tag v-else type="info">未认领</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="230">
        <template #default="{ row }">
          <el-button v-if="!row.mentor_doctor_id" size="small" type="primary" plain @click="take(row)">设为名下</el-button>
          <el-button size="small" @click="viewStats(row)">统计</el-button>
          <el-button size="small" @click="openScore(row)">评分</el-button>
          <el-popconfirm :title="`确认${row.status === 'active' ? '停用' : '启用'}该学生？`" @confirm="toggle(row)">
            <template #reference>
              <el-button size="small" type="danger" plain>{{ row.status === 'active' ? '停用' : '启用' }}</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
    <el-dialog v-model="statsVisible" title="学生实训统计">
      <el-descriptions :column="1" border v-if="stats">
        <el-descriptions-item label="问诊次数">{{ stats.consultation_count }}</el-descriptions-item>
        <el-descriptions-item label="总结数量">{{ stats.summary_count }}</el-descriptions-item>
        <el-descriptions-item label="通过率">{{ (stats.pass_rate * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="平均评分">{{ stats.avg_score }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>

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
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const query = reactive({ keyword: '', status: '' })
const rows = ref<any[]>([])
const statsVisible = ref(false)
const stats = ref<any>(null)
const scoreVisible = ref(false)
const score = reactive({ student_id: 0, summary_id: null as number | null, q_consultation: 0, q_history: 0, q_communication: 0, q_summary: 0, comment: '' })

async function load() {
  const data: any = await http.get('/doctor/students', { params: query })
  rows.value = data.items
}

async function take(row: any) {
  await http.post(`/doctor/students/${row.id}/take`)
  ElMessage.success('已设为名下学生')
  load()
}

async function viewStats(row: any) {
  stats.value = await http.get(`/doctor/students/${row.id}/stats`)
  statsVisible.value = true
}

function openScore(row: any) {
  Object.assign(score, { student_id: row.id, summary_id: null, q_consultation: 0, q_history: 0, q_communication: 0, q_summary: 0, comment: '' })
  scoreVisible.value = true
}

async function submitScore() {
  if (!score.comment.trim()) return ElMessage.warning('请填写评语')
  await http.post('/doctor/scores', score)
  ElMessage.success('评分已录入')
  scoreVisible.value = false
}

async function toggle(row: any) {
  await http.post(`/doctor/students/${row.id}/toggle`)
  load()
}

onMounted(load)
</script>
