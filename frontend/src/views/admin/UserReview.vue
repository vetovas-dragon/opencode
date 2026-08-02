<template>
  <div>
    <h3>身份审核（医生 / 医学生）</h3>
    <el-table :data="pending" border stripe>
      <el-table-column prop="id" label="用户ID" width="90" />
      <el-table-column prop="name" label="姓名" width="120" />
      <el-table-column prop="role" label="角色" width="110">
        <template #default="{ row }">
          <el-tag :type="row.role === 'doctor' ? 'success' : 'warning'">
            {{ row.role === 'doctor' ? '医生' : '医学生' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="phone" label="手机号" width="140" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="created_at" label="申请时间" width="200" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" type="success" @click="approve(row)">通过</el-button>
          <el-button size="small" type="danger" plain @click="reject(row)">驳回</el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!pending.length" description="暂无待审核申请" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import http from '@/api/http'

const pending = ref<any[]>([])

async function load() {
  pending.value = await http.get('/admin/pending-users')
}

async function approve(row: any) {
  await http.post('/admin/users/review', { user_id: row.id, result: 'approve' })
  ElMessage.success(`已通过 ${row.name} 的注册申请`)
  load()
}

async function reject(row: any) {
  const { value } = await ElMessageBox.prompt('请输入驳回原因（必填）', '驳回注册申请', {
    inputValidator: (v) => !!v,
  })
  await http.post('/admin/users/review', { user_id: row.id, result: 'reject', reason: value })
  ElMessage.success('已驳回')
  load()
}

onMounted(load)
</script>
