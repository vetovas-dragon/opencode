<template>
  <div>
    <h3>问诊总结</h3>
    <el-form label-width="100px" style="max-width: 720px">
      <el-form-item label="关联会话">
        <el-select v-model="form.conversation_id" placeholder="选择已结束的问诊会话" style="width: 300px">
          <el-option v-for="c in convs" :key="c.id" :value="c.id" :label="`会话 #${c.id}（${c.status}）`" />
        </el-select>
      </el-form-item>
      <el-form-item label="主诉">
        <el-input v-model="form.chief_complaint" maxlength="100" show-word-limit placeholder="≤100字" />
      </el-form-item>
      <el-form-item label="现病史"><el-input v-model="form.present_illness" type="textarea" :rows="3" /></el-form-item>
      <el-form-item label="既往史"><el-input v-model="form.past_illness" type="textarea" :rows="2" /></el-form-item>
      <el-form-item label="问诊过程"><el-input v-model="form.consultation_process" type="textarea" :rows="3" /></el-form-item>
      <el-form-item label="初步判断"><el-input v-model="form.initial_diagnosis" /></el-form-item>
      <el-form-item label="诊疗建议"><el-input v-model="form.treatment_advice" type="textarea" :rows="2" /></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="submit">提交审核</el-button>
      </el-form-item>
    </el-form>

    <h4>历史总结</h4>
    <el-table :data="summaries" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="conversation_id" label="会话" width="90" />
      <el-table-column prop="chief_complaint" label="主诉" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'passed' ? 'success' : row.status === 'pending' ? 'warning' : 'danger'">
            {{ statusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="review_comment" label="审核意见" show-overflow-tooltip />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const convs = ref<any[]>([])
const summaries = ref<any[]>([])
const statusMap: Record<string, string> = { draft: '草稿', pending: '待审核', passed: '已通过', rejected: '已驳回' }
const form = reactive({
  conversation_id: null as number | null,
  chief_complaint: '',
  present_illness: '',
  past_illness: '',
  consultation_process: '',
  initial_diagnosis: '',
  treatment_advice: '',
})

async function load() {
  convs.value = await http.get('/student/conversations')
  summaries.value = await http.get('/student/summaries')
}

async function submit() {
  if (!form.conversation_id) {
    ElMessage.warning('请选择关联会话')
    return
  }
  await http.post('/student/summaries', form)
  ElMessage.success('已提交，等待医生审核')
  load()
}

onMounted(load)
</script>
