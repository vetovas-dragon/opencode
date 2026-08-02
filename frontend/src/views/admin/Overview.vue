<template>
  <div>
    <h3>全局概览</h3>
    <el-card shadow="never" class="metric-card">
      <el-row :gutter="16">
        <el-col :span="6" v-for="(item, key) in business" :key="key">
          <div class="metric">
            <div class="value">{{ item }}</div>
            <div class="label">{{ businessLabels[key] || key }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>教学数据（近30天）</template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="总结数">{{ teaching.summary_count }}</el-descriptions-item>
        <el-descriptions-item label="通过率">{{ (teaching.pass_rate * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="平均评分">{{ teaching.avg_score }}</el-descriptions-item>
        <el-descriptions-item label="评分记录">{{ teaching.score_count }}</el-descriptions-item>
      </el-descriptions>
      <div ref="chartRef" style="height: 280px; margin-top: 12px"></div>
    </el-card>

    <el-card shadow="never" style="margin-top: 16px">
      <template #header>患者数据（近30天）</template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="注册患者数">{{ patient.patient_count }}</el-descriptions-item>
        <el-descriptions-item label="民族分布">{{ formatDist(patient.ethnicity_distribution) }}</el-descriptions-item>
        <el-descriptions-item label="性别分布">{{ formatDist(patient.gender_distribution) }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import http from '@/api/http'

const business = ref<Record<string, number>>({})
const teaching = ref<any>({})
const patient = ref<any>({})
const chartRef = ref<HTMLDivElement>()
const businessLabels: Record<string, string> = {
  consultation_count: '问诊量',
  ended_count: '已结束会话',
  message_count: '消息数',
  service_patient_count: '服务人次',
}

async function load() {
  business.value = await http.get('/stats', { params: { dimension: 'business' } })
  teaching.value = await http.get('/stats', { params: { dimension: 'teaching' } })
  patient.value = await http.get('/stats', { params: { dimension: 'patient' } })
  await nextTick()
  if (chartRef.value) {
    const chart = echarts.init(chartRef.value)
    const dist = teaching.value.grade_distribution || {}
    chart.setOption({
      title: { text: '评分等级分布' },
      xAxis: { type: 'category', data: Object.keys(dist) },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: Object.values(dist), itemStyle: { color: '#409eff' } }],
    })
  }
}

function formatDist(dist: Record<string, number> | undefined): string {
  if (!dist || !Object.keys(dist).length) return '—'
  return Object.entries(dist).map(([k, v]) => `${k} ${v}`).join(' / ')
}

onMounted(load)
</script>

<style scoped>
.metric-card { margin-bottom: 4px; }
.metric { text-align: center; padding: 8px 0; }
.value { font-size: 28px; font-weight: bold; color: #409eff; }
.label { color: #909399; margin-top: 4px; }
</style>
