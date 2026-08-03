<template>
  <div>
    <van-cell-group inset title="录入健康数据">
      <van-field label="指标">
        <template #input>
          <van-radio-group v-model="form.metric_type" direction="horizontal">
            <van-radio name="bp">血压</van-radio>
            <van-radio name="bg">血糖</van-radio>
            <van-radio name="weight">体重</van-radio>
          </van-radio-group>
        </template>
      </van-field>
      <van-field v-if="form.metric_type === 'bp'" v-model="form.systolic" type="digit" label="收缩压" placeholder="mmHg" />
      <van-field v-if="form.metric_type === 'bp'" v-model="form.diastolic" type="digit" label="舒张压" placeholder="mmHg" />
      <van-field v-else v-model="form.value" type="digit" :label="form.metric_type === 'bg' ? '血糖值' : '体重'" :placeholder="form.metric_type === 'bg' ? 'mmol/L' : 'kg'" />
    </van-cell-group>
    <div style="padding: 0 16px">
      <van-button type="primary" block @click="save">保存</van-button>
    </div>

    <van-cell-group inset title="历史趋势" style="margin-top: 12px">
      <van-tabs v-model:active="activeTab" @change="renderChart">
        <van-tab title="血压" name="bp" />
        <van-tab title="血糖" name="bg" />
        <van-tab title="体重" name="weight" />
      </van-tabs>
      <div ref="chartRef" style="height: 280px"></div>
      <van-cell
        v-for="d in filtered"
        :key="d.id"
        :title="`${d.metric_type === 'bp' ? '血压' : d.metric_type === 'bg' ? '血糖' : '体重'}: ${d.value_primary}${d.value_secondary ? '/' + d.value_secondary : ''}${d.unit}`"
        :label="`${d.measured_at}${d.is_abnormal ? ' · 超出正常范围' : ''}`"
      />
      <van-empty v-if="!filtered.length" description="暂无该指标数据" />
    </van-cell-group>

    <van-cell-group inset title="用药时间轴" style="margin-top: 12px">
      <van-cell
        v-for="m in meds"
        :key="m.id"
        :title="m.medication_name"
        :label="`${m.dosage || '常规剂量'} · ${m.taken_at.slice(0, 16).replace('T', ' ')}`"
      />
      <van-empty v-if="!meds.length" description="暂无用药记录" />
      <van-cell center title="记录本次用药" label="点击补记一条服药记录">
        <van-button size="small" type="primary" @click="medVisible = true">记录</van-button>
      </van-cell>
    </van-cell-group>

    <van-popup v-model:show="medVisible" position="bottom" round style="padding: 16px">
      <van-field v-model="med.name" label="药品名称" placeholder="如：氨氯地平" />
      <van-field v-model="med.dosage" label="用量" placeholder="如：5mg 每日一次" />
      <div style="margin-top: 12px">
        <van-button type="primary" block @click="saveMed">保存记录</van-button>
      </div>
    </van-popup>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { showSuccessToast } from 'vant'
import http from '@/api/http'

const form = reactive({ metric_type: 'bp', systolic: '', diastolic: '', value: '' })
const data = ref<any[]>([])
const meds = ref<any[]>([])
const chartRef = ref<HTMLDivElement>()
const activeTab = ref('bp')
const medVisible = ref(false)
const med = reactive({ name: '', dosage: '' })
let chart: echarts.ECharts | null = null

const filtered = computed(() => data.value.filter((d) => d.metric_type === activeTab.value))

const META: Record<string, { label: string; unit: string; refs?: number[] }> = {
  bp: { label: '血压', unit: 'mmHg', refs: [140, 90] },
  bg: { label: '血糖', unit: 'mmol/L', refs: [7.0] },
  weight: { label: '体重', unit: 'kg' },
}

async function load() {
  data.value = await http.get('/patient/health-data')
  meds.value = await http.get('/patient/medications')
  await nextTick()
  renderChart()
}

function renderChart() {
  const meta = META[activeTab.value]
  if (!chartRef.value) return
  if (!chart) chart = echarts.init(chartRef.value)
  const rows = filtered.value
  const dates = rows.map((d) => d.measured_at.slice(5, 16).replace('T', ' '))
  const series: any[] = [{ name: meta.label, type: 'line', data: rows.map((d) => d.value_primary), markPoint: { data: rows.map((d, i) => (d.is_abnormal ? { coord: [i, d.value_primary], value: '异常', itemStyle: { color: '#ee0a24' } } : null)).filter(Boolean) } }]
  if (activeTab.value === 'bp') {
    series.push({ name: '舒张压', type: 'line', data: rows.map((d) => d.value_secondary), lineStyle: { type: 'dashed' } })
  }
  if (meta.refs) {
    series[0].markLine = { data: meta.refs.map((v) => ({ yAxis: v, label: { formatter: `参考 ${v}` }, lineStyle: { type: 'dashed', color: '#909399' } })) }
  }
  chart.setOption(
    {
      tooltip: { trigger: 'axis' },
      legend: { data: series.map((s) => s.name) },
      grid: { left: 40, right: 16, top: 32, bottom: 40 },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: meta.unit },
      series,
    },
    true,
  )
}

async function save() {
  const payload: any =
    form.metric_type === 'bp'
      ? { metric_type: 'bp', value_primary: Number(form.systolic), value_secondary: Number(form.diastolic), unit: 'mmHg' }
      : { metric_type: form.metric_type, value_primary: Number(form.value), unit: form.metric_type === 'bg' ? 'mmol/L' : 'kg' }
  payload.measured_at = new Date().toISOString()
  const res: any = await http.post('/patient/health-data', payload)
  showSuccessToast(res.is_abnormal ? '已保存（超出正常范围）' : '已保存')
  form.systolic = form.diastolic = form.value = ''
  load()
}

async function saveMed() {
  if (!med.name.trim()) return
  await http.post('/patient/medication-logs', { medication_name: med.name, dosage: med.dosage || null, taken_at: new Date().toISOString() })
  showSuccessToast('已记录')
  med.name = med.dosage = ''
  medVisible.value = false
  load()
}

onMounted(load)
</script>
