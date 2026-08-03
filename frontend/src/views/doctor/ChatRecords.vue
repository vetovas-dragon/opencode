<template>
  <div>
    <h3>问诊聊天记录</h3>
    <el-form inline>
      <el-form-item label="关键词">
        <el-input v-model="query.keyword" placeholder="检索消息内容（≥2字）" clearable @keyup.enter="search" />
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status" clearable placeholder="全部" style="width: 120px">
          <el-option label="进行中" value="active" />
          <el-option label="已结束" value="ended" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">筛选</el-button>
        <el-button @click="clearSearch">重置</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="rows" border stripe @row-click="openMessages">
      <el-table-column prop="id" label="会话ID" width="90" />
      <el-table-column prop="patient_id" label="患者ID" width="90" />
      <el-table-column prop="student_id" label="医学生ID" width="100" />
      <el-table-column prop="doctor_id" label="介入医生" width="100">
        <template #default="{ row }">{{ row.doctor_id || '-' }}</template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '进行中' : '已结束' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="200" />
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" type="primary" link @click.stop="openMessages(row)">查看记录</el-button>
          <el-button v-if="row.status === 'active' && !row.doctor_id" size="small" type="warning" link @click.stop="join(row)">介入问诊</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-drawer v-model="msgVisible" :title="interactive ? '问诊会话（可互动）' : '完整聊天记录（全程留痕）'" size="60%">
      <template v-if="interactive">
        <el-button size="small" type="primary" plain style="margin-bottom: 10px" @click="openProfile">维护患者档案</el-button>
        <ChatPanel :conversation-id="activeId" />
      </template>
      <template v-else>
        <div v-for="m in messages" :key="m.id" class="msg">
          <div class="meta">[{{ m.sender_role }}] {{ m.sender_id }} · {{ m.created_at }}</div>
          <div>{{ m.content }}</div>
          <div v-if="m.translated_text" class="trans">译文：{{ m.translated_text }}</div>
        </div>
      </template>
    </el-drawer>

    <el-dialog v-model="profileVisible" title="维护患者档案（协同更新）" width="480">
      <el-form label-width="90px">
        <el-form-item label="住址">
          <el-input v-model="profileForm.address" />
        </el-form-item>
        <el-form-item label="过敏史">
          <el-input v-model="profileForm.allergy_history" type="textarea" :rows="2" placeholder="如：青霉素过敏" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="profileVisible = false">取消</el-button>
        <el-button type="primary" @click="saveProfile">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import ChatPanel from '@/components/ChatPanel.vue'

const query = reactive({ keyword: '', status: '' })
const rows = ref<any[]>([])
const messages = ref<any[]>([])
const msgVisible = ref(false)
const interactive = ref(false)
const activeId = ref(0)
const activePatientId = ref(0)
const profileVisible = ref(false)
const profileForm = reactive({ address: '', allergy_history: '' })

async function load() {
  const params: any = { status: query.status || undefined }
  const data: any = await http.get('/doctor/conversations', { params })
  rows.value = data.items
}

async function search() {
  if (!query.keyword.trim()) return load()
  const keyword = query.keyword.trim()
  if (keyword.length < 2) return ElMessage.warning('关键词至少 2 个字符')
  const data: any = await http.get('/conversations/search', { params: { keyword, limit: 50 } })
  messages.value = data
  interactive.value = false
  msgVisible.value = true
}

function clearSearch() {
  query.keyword = ''
  load()
}

async function openMessages(row: any) {
  activeId.value = row.id
  activePatientId.value = row.patient_id
  interactive.value = row.status === 'active'
  if (!interactive.value) {
    messages.value = await http.get(`/doctor/conversations/${row.id}/messages`)
  }
  msgVisible.value = true
}

async function openProfile() {
  profileForm.address = ''
  profileForm.allergy_history = ''
  profileVisible.value = true
}

async function saveProfile() {
  await http.put(`/doctor/patients/${activePatientId.value}/profile`, profileForm)
  ElMessage.success('档案已更新')
  profileVisible.value = false
}

async function join(row: any) {
  await http.post(`/doctor/conversations/${row.id}/join`)
  ElMessage.success('已介入问诊')
  load()
}

onMounted(load)
</script>

<style scoped>
.msg { border-bottom: 1px solid #f0f0f0; padding: 8px 0; }
.meta { color: #909399; font-size: 12px; }
.trans { color: #67c23a; }
</style>
