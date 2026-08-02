<template>
  <div>
    <h3>数据统计面板</h3>
    <el-form inline>
      <el-form-item label="维度">
        <el-radio-group v-model="dimension">
          <el-radio-button value="business">业务数据</el-radio-button>
          <el-radio-button value="teaching">教学数据</el-radio-button>
          <el-radio-button value="patient">患者数据</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="load">查询</el-button>
        <el-button @click="exportExcel">导出 Excel</el-button>
      </el-form-item>
    </el-form>

    <el-descriptions :column="3" border v-if="data">
      <el-descriptions-item v-for="(value, key) in displayData" :key="key" :label="key">{{ value }}</el-descriptions-item>
    </el-descriptions>

    <div ref="chartRef" style="height: 380px; margin-top: 24px"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import http from '@/api/http'

const dimension = ref('business')
const data = ref<any>(null)
const chartRef = ref<HTMLDivElement>()

const displayData = computed(() => {
  const d = data.value || {}
  if (dimension.value === 'teaching') {
    return { '总结数': d.summary_count, '通过率': `${(d.pass_rate * 100).toFixed(1)}%`, '平均分': d.avg_score }
  }
  if (dimension.value === 'patient') {
    return { '患者数': d.patient_count }
  }
  return { '问诊量': d.consultation_count, '消息数': d.message_count, '服务人次': d.service_patient_count }
})

async function load() {
  data.value = await http.get('/stats', { params: { dimension: dimension.value } })
  renderChart()
}

async function exportExcel() {
  await http.post('/stats/export', { dimension: dimension.value })
}

function renderChart() {
  const d = data.value || {}
  const el = chartRef.value
  if (!el) return
  const chart = echarts.init(el)
  const categories = Object.keys(d.grade_distribution || d.ethnicity_distribution || {})
  const values = Object.values(d.grade_distribution || d.ethnicity_distribution || {})
  chart.setOption({
    title: { text: dimension.value === 'teaching' ? '评分等级分布' : '人群分布' },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: values }],
  })
}

onMounted(load)
</script>
