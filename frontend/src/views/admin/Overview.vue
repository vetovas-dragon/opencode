<template>
  <div>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">问诊量</div>
        <div class="value">{{ business.consultation_count ?? 0 }}</div>
        <div class="extra">历史累计会话</div>
      </div>
      <div class="stat-card alt1">
        <div class="label">已结束会话</div>
        <div class="value">{{ business.ended_count ?? 0 }}</div>
        <div class="extra">已归档问诊</div>
      </div>
      <div class="stat-card alt2">
        <div class="label">消息数</div>
        <div class="value">{{ business.message_count ?? 0 }}</div>
        <div class="extra">医患沟通消息</div>
      </div>
      <div class="stat-card alt3">
        <div class="label">服务患者数</div>
        <div class="value">{{ business.service_patient_count ?? 0 }}</div>
        <div class="extra">覆盖患者人数</div>
      </div>
    </div>

    <div class="page-card">
      <div class="page-title">教学数据（近30天）</div>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="总结数">{{ teaching.summary_count }}</el-descriptions-item>
        <el-descriptions-item label="通过率">{{ (teaching.pass_rate * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="平均评分">{{ teaching.avg_score }}</el-descriptions-item>
        <el-descriptions-item label="评分记录">{{ teaching.score_count }}</el-descriptions-item>
      </el-descriptions>
      <div ref="chartRef" style="height: 280px; margin-top: 12px"></div>
    </div>

    <div class="page-card">
      <div class="page-title">患者数据（近30天）</div>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="注册患者数">{{ patient.patient_count }}</el-descriptions-item>
        <el-descriptions-item label="民族分布">{{ formatDist(patient.ethnicity_distribution) }}</el-descriptions-item>
        <el-descriptions-item label="性别分布">{{ formatDist(patient.gender_distribution) }}</el-descriptions-item>
      </el-descriptions>
    </div>
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

async function load() {
  business.value = await http.get('/stats', { params: { dimension: 'business' } })
  teaching.value = await http.get('/stats', { params: { dimension: 'teaching' } })
  patient.value = await http.get('/stats', { params: { dimension: 'patient' } })
  await nextTick()
  if (chartRef.value) {
    const chart = echarts.init(chartRef.value)
    const dist = teaching.value.grade_distribution || {}
    chart.setOption({
      backgroundColor: 'transparent',
      title: { text: '评分等级分布' },
      xAxis: { type: 'category', data: Object.keys(dist) },
      yAxis: { type: 'value' },
      series: [{ type: 'bar', data: Object.values(dist), itemStyle: { color: '#1677ff', borderRadius: [6, 6, 0, 0] }, barWidth: 36 }],
    })
  }
}

function formatDist(dist: Record<string, number> | undefined): string {
  if (!dist || !Object.keys(dist).length) return '—'
  return Object.entries(dist).map(([k, v]) => `${k} ${v}`).join(' / ')
}

onMounted(load)
</script>