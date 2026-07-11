<template>
  <div class="dc-panel">
    <div class="dc-panel-title">用户增长趋势</div>
    <div ref="chartRef" class="user-growth-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface UserGrowthData {
  days: string[]
  daily: number[]
  cumulative: number[]
}

const props = defineProps<{ data: UserGrowthData }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const buildOption = () => {
  const d = props.data || { days: [], daily: [], cumulative: [] }
  const days = d.days || []
  const daily = d.daily || []
  const cumulative = d.cumulative || []
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' },
    legend: { top: 0, data: ['每日新增', '累计用户'], textStyle: { color: '#c4b5fd' } },
    grid: { top: 40, left: 45, right: 45, bottom: 30 },
    xAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: '#c4b5fd', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(167,139,250,0.3)' } },
      axisTick: { show: false },
    },
    yAxis: [
      {
        type: 'value',
        name: '每日新增',
        nameTextStyle: { color: '#c4b5fd' },
        axisLabel: { color: '#c4b5fd', fontSize: 11 },
        splitLine: { lineStyle: { color: 'rgba(167,139,250,0.1)' } },
      },
      {
        type: 'value',
        name: '累计用户',
        nameTextStyle: { color: '#c4b5fd' },
        axisLabel: { color: '#c4b5fd', fontSize: 11 },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '每日新增',
        type: 'bar',
        data: daily,
        barWidth: '50%',
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#4096ff' },
            { offset: 1, color: 'rgba(64,150,255,0.2)' },
          ]),
        },
      },
      {
        name: '累计用户',
        type: 'line',
        yAxisIndex: 1,
        data: cumulative,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: '#52c41a', width: 2 },
        itemStyle: { color: '#52c41a' },
        areaStyle: { color: 'rgba(82,196,26,0.1)' },
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
.user-growth-chart {
  height: 360px;
}
</style>
