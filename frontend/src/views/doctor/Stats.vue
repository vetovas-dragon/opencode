<template>
  <div>
    <div class="stat-grid">
      <div class="stat-card">
        <div class="label">问诊量</div>
        <div class="value">{{ (data?.consultation_count ?? 0) }}</div>
        <div class="extra">历史累计会话</div>
      </div>
      <div class="stat-card alt1">
        <div class="label">消息数</div>
        <div class="value">{{ (data?.message_count ?? 0) }}</div>
        <div class="extra">咨询与回复消息</div>
      </div>
      <div class="stat-card alt2">
        <div class="label">服务患者数</div>
        <div class="value">{{ (data?.service_patient_count ?? 0) }}</div>
        <div class="extra">覆盖不同患者人群</div>
      </div>
      <div class="stat-card alt3">
        <div class="label">总结通过率</div>
        <div class="value">{{ data?.pass_rate != null ? ((data.pass_rate as number) * 100).toFixed(1) : '—' }}%</div>
        <div class="extra">带教审核质量</div>
      </div>
    </div>

    <div class="page-card">
      <div class="page-title">数据统计面板</div>
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
  await nextTick()
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
    backgroundColor: 'transparent',
    title: { text: dimension.value === 'teaching' ? '评分等级分布' : '人群分布' },
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: values, itemStyle: { color: '#1677ff', borderRadius: [6, 6, 0, 0] }, barWidth: 32 }],
  })
}

onMounted(load)
</script>