<template>
  <div class="dc-panel">
    <div class="dc-panel-title">职位城市分布 TOP10</div>
    <div ref="chartRef" class="city-dist-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface CityDistData {
  names: string[]
  values: number[]
}

const props = defineProps<{ data: CityDistData }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const buildOption = () => {
  const d = props.data || { names: [], values: [] }
  const names = (d.names || []).slice().reverse()
  const values = (d.values || []).slice().reverse()
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 10, left: 80, right: 40, bottom: 10 },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#c4b5fd', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(167,139,250,0.1)' } },
    },
    yAxis: {
      type: 'category',
      data: names,
      axisLabel: { color: '#c4b5fd', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(167,139,250,0.3)' } },
      axisTick: { show: false },
    },
    series: [
      {
        type: 'bar',
        data: values,
        barWidth: '60%',
        label: {
          show: true,
          position: 'right',
          color: '#e0e7ff',
          fontSize: 11,
        },
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#1677ff' },
            { offset: 1, color: '#722ed1' },
          ]),
        },
      },
    ],
  }
}

const render = () => {
  if (!chart) return
  chart.setOption(buildOption(), true)
}

const handleResize = () => chart?.resize()

onMounted(() => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value, 'dark')
  render()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chart?.dispose()
  chart = null
})

watch(() => props.data, render, { deep: true })
</script>

<style scoped>
.dc-panel {
  background: rgba(48, 43, 99, 0.25);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
  padding: 16px;
}
.dc-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #a78bfa;
  margin-bottom: 12px;
  letter-spacing: 1px;
}
.city-dist-chart {
  height: 320px;
}
</style>
