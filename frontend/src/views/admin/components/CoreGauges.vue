<template>
  <div class="dc-panel">
    <div class="dc-panel-title">平台核心指标</div>
    <div ref="chartRef" class="core-gauges-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface Gauges {
  parse_rate: number
  job_active_rate: number
  avg_match_score: number
}

const props = defineProps<{ gauges: Gauges }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const colorByValue = (v: number) => {
  if (v < 60) return '#ff4d4f'
  if (v < 80) return '#faad14'
  return '#52c41a'
}

const buildOption = () => {
  const g = props.gauges || { parse_rate: 0, job_active_rate: 0, avg_match_score: 0 }
  const items = [
    { name: '简历解析成功率', value: Number(g.parse_rate) || 0, unit: '%' },
    { name: '职位活跃率', value: Number(g.job_active_rate) || 0, unit: '%' },
    { name: '平均匹配分', value: Number(g.avg_match_score) || 0, unit: '' },
  ]
  // 3 个仪表盘中心: 16.67% / 50% / 83.33%, 间距 33.33%
  // 半径 26%，环宽 16，数字显示在环下方
  const centers = ['16.67%', '50%', '83.33%']
  const radius = '26%'
  return {
    backgroundColor: 'transparent',
    series: items.map((it, idx) => ({
      type: 'gauge',
      radius,
      center: [centers[idx], '42%'],
      startAngle: 90,
      endAngle: -270,
      min: 0,
      max: 100,
      splitNumber: 5,
      progress: {
        show: true,
        overlap: false,
        roundCap: true,
        clip: false,
        width: 16,
        itemStyle: { color: colorByValue(it.value) },
      },
      pointer: { show: false },
      axisLine: {
        lineStyle: {
          width: 16,
          color: [[1, 'rgba(167,139,250,0.12)']],
        },
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      anchor: { show: false },
      title: {
        show: true,
        offsetCenter: [0, '120%'],
        color: '#c4b5fd',
        fontSize: 12,
      },
      detail: {
        valueAnimation: true,
        fontSize: 22,
        fontWeight: 'bold',
        color: colorByValue(it.value),
        offsetCenter: [0, '175%'],
        formatter: (val: number) => val.toFixed(1) + it.unit,
      },
      data: [{ value: it.value, name: it.name }],
    })),
  }
}

const render = () => {
  if (!chart) return
  chart.setOption(buildOption(), true)
}

const handleResize = () => {
  if (!chart) return
  chart.resize()
  render()
}

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

watch(() => props.gauges, render, { deep: true })
</script>

<style scoped>
.dc-panel {
  background: rgba(48, 43, 99, 0.25);
  backdrop-filter: blur(16px);
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
.core-gauges-chart {
  height: 360px;
}
</style>
