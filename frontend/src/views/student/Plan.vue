<template>
  <div>
    <h3>实训计划与待办</h3>
    <el-form inline>
      <el-form-item label="计划名称"><el-input v-model="planForm.title" placeholder="如：本月问诊实训计划" /></el-form-item>
      <el-form-item label="周期"><el-input v-model="planForm.period" placeholder="如：2026-08" style="width: 130px" /></el-form-item>
      <el-form-item label="目标"><el-input v-model="planForm.goal" style="width: 260px" /></el-form-item>
      <el-form-item>
        <el-button type="primary" @click="createPlan">新建计划</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="plans" border stripe>
      <el-table-column prop="title" label="计划名称" />
      <el-table-column prop="period" label="周期" width="120" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'passed' ? 'success' : row.status === 'pending' ? 'warning' : 'info'">
            {{ planStatusMap[row.status] }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="review_comment" label="审核意见" show-overflow-tooltip />
      <el-table-column label="操作" width="140">
        <template #default="{ row }">
          <el-button v-if="row.status !== 'pending' && row.status !== 'passed'" size="small" type="primary" @click="submitPlan(row)">提交审核</el-button>
        </template>
      </el-table-column>
    </el-table>

    <h4>待办事项</h4>
    <el-input v-model="todoTitle" placeholder="新增待办" style="width: 320px" @keyup.enter="createTodo" />
    <el-button type="primary" plain style="margin-left: 8px" @click="createTodo">添加</el-button>
    <el-table :data="todos" border stripe style="margin-top: 12px">
      <el-table-column prop="title" label="待办" />
      <el-table-column prop="due_at" label="截止时间" width="200" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'done' ? 'success' : row.status === 'overdue' ? 'danger' : 'warning'">
            {{ todoStatusMap[row.status] || row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" @click="toggleTodo(row)">{{ row.status === 'done' ? '重开' : '完成' }}</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import http from '@/api/http'

const planForm = reactive({ title: '', period: '', goal: '' })
const plans = ref<any[]>([])
const todos = ref<any[]>([])
const todoTitle = ref('')
const planStatusMap: Record<string, string> = { draft: '草稿', pending: '待审核', passed: '已通过', rejected: '已驳回' }
const todoStatusMap: Record<string, string> = { pending: '待办', done: '已完成', overdue: '已逾期' }

async function load() {
  plans.value = await http.get('/student/plans')
  todos.value = await http.get('/student/todos')
}

async function createPlan() {
  await http.post('/student/plans', planForm)
  ElMessage.success('计划已创建')
  planForm.title = planForm.period = planForm.goal = ''
  load()
}

async function submitPlan(row: any) {
  await http.post(`/student/plans/${row.id}/submit`)
  ElMessage.success('已提交审核')
  load()
}

async function createTodo() {
  if (!todoTitle.value) return
  await http.post('/student/todos', { plan_id: plans.value[0]?.id ?? 0, title: todoTitle.value })
  todoTitle.value = ''
  load()
}

async function toggleTodo(row: any) {
  await http.post(`/student/todos/${row.id}/toggle`)
  load()
}

onMounted(load)
</script>
