<template>
  <div>
    <van-cell-group inset title="录入健康数据">
      <van-field v-model="form.metric_type" label="指标">
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
      <div ref="chartRef" style="height: 260px"></div>
      <van-cell v-for="d in data" :key="d.id" :title="`${d.metric_type}: ${d.value_primary}${d.value_secondary ? '/' + d.value_secondary : ''}${d.unit}`" :label="`${d.measured_at}${d.is_abnormal ? ' · 超出正常范围' : ''}`" />
    </van-cell-group>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, reactive, ref } from 'vue'
import * as echarts from 'echarts'
import { showSuccessToast } from 'vant'
import http from '@/api/http'

const form = reactive({ metric_type: 'bp', systolic: '', diastolic: '', value: '' })
const data = ref<any[]>([])
const chartRef = ref<HTMLDivElement>()

async function load() {
  data.value = await http.get('/patient/health-data')
  await nextTick()
  if (chartRef.value) {
    const chart = echarts.init(chartRef.value)
    chart.setOption({
      xAxis: { type: 'category', data: data.value.map((d) => d.measured_at.slice(5, 10)) },
      yAxis: { type: 'value' },
      series: [{ type: 'line', data: data.value.map((d) => d.value_primary) }],
    })
  }
}

async function save() {
  const payload: any =
    form.metric_type === 'bp'
      ? { metric_type: 'bp', value_primary: Number(form.systolic), value_secondary: Number(form.diastolic), unit: 'mmHg' }
      : { metric_type: form.metric_type, value_primary: Number(form.value), unit: form.metric_type === 'bg' ? 'mmol/L' : 'kg' }
  payload.measured_at = new Date().toISOString()
  await http.post('/patient/health-data', payload)
  showSuccessToast('已保存')
  load()
}

onMounted(load)
</script>
