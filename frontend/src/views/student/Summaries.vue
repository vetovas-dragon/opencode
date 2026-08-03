<template>
  <div>
    <div class="page-title">问诊总结</div>
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

    <div class="page-title" style="font-size:15px">历史总结</div>
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
      <el-table-column label="操作" width="110">
        <template #default="{ row }">
          <el-button v-if="row.status === 'rejected'" size="small" type="warning" plain @click="openEdit(row)">编辑重提</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="editVisible" title="编辑总结并重新提交" width="620">
      <el-form label-width="90px">
        <el-form-item label="主诉">
          <el-input v-model="editForm.chief_complaint" maxlength="100" show-word-limit />
        </el-form-item>
        <el-form-item label="现病史"><el-input v-model="editForm.present_illness" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="既往史"><el-input v-model="editForm.past_illness" type="textarea" :rows="2" /></el-form-item>
        <el-form-item label="问诊过程"><el-input v-model="editForm.consultation_process" type="textarea" :rows="3" /></el-form-item>
        <el-form-item label="初步判断"><el-input v-model="editForm.initial_diagnosis" /></el-form-item>
        <el-form-item label="诊疗建议"><el-input v-model="editForm.treatment_advice" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editVisible = false">取消</el-button>
        <el-button type="primary" @click="resubmit">重新提交</el-button>
      </template>
    </el-dialog>
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
const editVisible = ref(false)
const editId = ref(0)
const editForm = reactive({
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

function openEdit(row: any) {
  editId.value = row.id
  Object.assign(editForm, {
    chief_complaint: row.chief_complaint || '',
    present_illness: row.present_illness || '',
    past_illness: row.past_illness || '',
    consultation_process: row.consultation_process || '',
    initial_diagnosis: row.initial_diagnosis || '',
    treatment_advice: row.treatment_advice || '',
  })
  editVisible.value = true
}

async function resubmit() {
  await http.post('/student/summaries', { conversation_id: summaries.value.find((s) => s.id === editId.value)?.conversation_id, ...editForm })
  ElMessage.success('已重新提交，等待医生审核')
  editVisible.value = false
  load()
}

onMounted(load)
</script>
