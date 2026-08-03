<template>
  <div>
    <h3>接诊工作台</h3>
    <el-tabs v-model="tab">
      <el-tab-pane label="待介入会话" name="pending">
        <el-table :data="pendingRows" border stripe>
          <el-table-column prop="id" label="会话ID" width="90" />
          <el-table-column prop="patient_id" label="患者ID" width="90" />
          <el-table-column prop="student_id" label="医学生ID" width="100" />
          <el-table-column prop="created_at" label="开始时间" width="200" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="warning" @click="join(row)">介入问诊</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!pendingRows.length" description="暂无待介入的会话（名下学生的进行中会话）" />
      </el-tab-pane>
      <el-tab-pane label="我介入的会话" name="mine">
        <el-table :data="mineRows" border stripe @row-click="openChat">
          <el-table-column prop="id" label="会话ID" width="90" />
          <el-table-column prop="patient_id" label="患者ID" width="90" />
          <el-table-column prop="student_id" label="医学生ID" width="100" />
          <el-table-column prop="created_at" label="开始时间" width="200" />
          <el-table-column label="操作" width="120">
            <template #default="{ row }">
              <el-button size="small" type="primary" link @click.stop="openChat(row)">进入会话</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!mineRows.length" description="暂无介入的会话" />
      </el-tab-pane>
    </el-tabs>

    <el-drawer v-model="chatVisible" title="问诊会话（实时互动）" size="60%">
      <ChatPanel v-if="activeId" :conversation-id="activeId" />
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'
import ChatPanel from '@/components/ChatPanel.vue'

const tab = ref('pending')
const rows = ref<any[]>([])
const chatVisible = ref(false)
const activeId = ref(0)

const pendingRows = computed(() => rows.value.filter((r) => r.status === 'active' && !r.doctor_id))
const mineRows = computed(() => rows.value.filter((r) => r.status === 'active' && r.doctor_id))

async function load() {
  const data: any = await http.get('/doctor/conversations', { params: { status: 'active' } })
  rows.value = data.items
}

async function join(row: any) {
  await http.post(`/doctor/conversations/${row.id}/join`)
  ElMessage.success('已介入问诊')
  load()
}

function openChat(row: any) {
  activeId.value = row.id
  chatVisible.value = true
}

onMounted(load)
</script>
