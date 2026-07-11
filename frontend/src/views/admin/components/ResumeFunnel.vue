<template>
  <div class="dc-panel">
    <div class="dc-panel-title">简历解析漏斗</div>
    <div ref="chartRef" class="funnel-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface FunnelData {
  names: string[]
  values: number[]
}

const props = defineProps<{ data: FunnelData }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const palette = ['#8b5cf6', '#3b82f6', '#52c41a', '#ff4d4f']

const buildOption = () => {
  const d = props.data || { names: [], values: [] }
  const names = d.names && d.names.length ? d.names : ['待解析', '解析中', '成功', '失败']
  const values = d.values || []
  const total = values[0] || 0
  const data = names.map((n: string, i: number) => ({
    name: n,
    value: values[i] || 0,
    itemStyle: { color: palette[i % palette.length] },
  }))
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      formatter: (p: any) => {
        const rate = total ? ((p.value / total) * 100).toFixed(1) : '0.0'
        return `${p.name}<br/>数量: ${p.value}<br/>转化率: ${rate}%`
      },
    },
    series: [
      {
        type: 'funnel',
        left: '10%',
        right: '10%',
        top: 16,
        bottom: 16,
        width: '80%',
        min: 0,
        max: total || Math.max(...values, 1),
        minSize: '30%',
        maxSize: '100%',
        sort: 'descending',
        gap: 4,
        label: {
          show: true,
          position: 'inside',
          color: '#fff',
          fontSize: 13,
          formatter: (p: any) => {
            const rate = total ? ((p.value / total) * 100).toFixed(1) : '0.0'
            return `${p.name}  ${p.value} (${rate}%)`
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
.funnel-chart {
  height: 320px;
}
</style>
