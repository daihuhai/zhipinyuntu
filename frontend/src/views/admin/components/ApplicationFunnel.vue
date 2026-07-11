<template>
  <div class="dc-panel">
    <div class="dc-panel-title">投递状态漏斗</div>
    <div ref="chartRef" class="app-funnel-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface AppFunnelData {
  total: number
  names: string[]
  values: number[]
}

const props = defineProps<{ data: AppFunnelData }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const colorMap: Record<string, string> = {
  已投递: '#4096ff',
  已查看: '#a78bfa',
  面试邀请: '#52c41a',
  不合适: '#ff4d4f',
  已录用: '#faad14',
}
const defaultPalette = ['#4096ff', '#a78bfa', '#52c41a', '#ff4d4f', '#faad14']

const buildOption = () => {
  const d = props.data || { total: 0, names: [], values: [] }
  const names = d.names || []
  const values = d.values || []
  const total = d.total || values[0] || 0
  const data = names.map((n: string, i: number) => ({
    name: n,
    value: values[i] || 0,
    itemStyle: { color: colorMap[n] || defaultPalette[i % defaultPalette.length] },
  }))
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const rate = total ? ((p.value / total) * 100).toFixed(1) : '0.0'
        return `${p.name}<br/>数量: ${p.value}<br/>占比: ${rate}%`
      },
    },
    series: [
      {
        type: 'funnel',
        left: '10%',
        right: '10%',
        top: 10,
        bottom: 10,
        width: '80%',
        min: 0,
        max: total || Math.max(...values, 1),
        minSize: '30%',
        maxSize: '100%',
        sort: 'descending',
        gap: 2,
        label: {
          show: true,
          position: 'inside',
          color: '#fff',
          fontSize: 13,
          formatter: (p: any) => {
            const rate = total ? ((p.value / total) * 100).toFixed(1) : '0.0'
            return `${p.name}: ${p.value} (${rate}%)`
          },
        },
        labelLine: { show: false },
        itemStyle: {
          borderColor: 'rgba(167,139,250,0.2)',
          borderWidth: 1,
        },
        emphasis: {
          label: { fontSize: 15, fontWeight: 'bold' },
          itemStyle: {
            shadowBlur: 14,
            shadowColor: 'rgba(167,139,250,0.6)',
          },
        },
        data,
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
.app-funnel-chart {
  height: 300px;
}
</style>
