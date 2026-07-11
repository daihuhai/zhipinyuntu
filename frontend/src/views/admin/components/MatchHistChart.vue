<template>
  <div class="dc-panel">
    <div class="dc-panel-title">匹配分分布</div>
    <div class="legend-row">
      <span class="legend-item"><span class="dot red"></span>均值 <b>{{ Number(data?.avg_score || 0).toFixed(1) }}</b></span>
      <span class="legend-item"><span class="dot green"></span>中位数 <b>{{ Number(data?.median_score || 0).toFixed(1) }}</b></span>
    </div>
    <div ref="chartRef" class="hist-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface HistData {
  buckets: string[]
  counts: number[]
  avg_score: number
  median_score: number
}

const props = defineProps<{ data: HistData }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

// 匹配分默认 0-100 区间，按桶数线性映射到类别轴索引以定位均值/中位数线
const MAX_SCORE = 100

const buildOption = () => {
  const d = props.data || { buckets: [], counts: [], avg_score: 0, median_score: 0 }
  const buckets = d.buckets || []
  const counts = d.counts || []
  const total = Math.max(buckets.length, 1)
  const avgIndex = (Number(d.avg_score || 0) / MAX_SCORE) * total - 0.5
  const medianIndex = (Number(d.median_score || 0) / MAX_SCORE) * total - 0.5
  return {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { top: 30, left: 40, right: 30, bottom: 30 },
    xAxis: {
      type: 'category',
      data: buckets,
      axisLabel: { color: '#c4b5fd', fontSize: 11 },
      axisLine: { lineStyle: { color: 'rgba(167,139,250,0.3)' } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#c4b5fd', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(167,139,250,0.1)' } },
    },
    series: [
      {
        type: 'bar',
        data: counts,
        barWidth: '60%',
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#a78bfa' },
            { offset: 1, color: 'rgba(167,139,250,0.2)' },
          ]),
        },
        markLine: {
          symbol: 'none',
          silent: true,
          label: { show: false },
          data: [
            {
              name: '均值',
              xAxis: avgIndex,
              lineStyle: { color: '#ff4d4f', type: 'dashed', width: 1.5 },
            },
            {
              name: '中位数',
              xAxis: medianIndex,
              lineStyle: { color: '#52c41a', type: 'dashed', width: 1.5 },
            },
          ],
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
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
  padding: 16px;
}
.dc-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #a78bfa;
  margin-bottom: 8px;
  letter-spacing: 1px;
}
.legend-row {
  display: flex;
  gap: 20px;
  font-size: 13px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(167, 139, 250, 0.08);
  border-radius: 6px;
}
.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #e0e7ff;
  white-space: nowrap;
}
.legend-item b {
  font-size: 15px;
  font-weight: 700;
}
.dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dot.red { background: #ff4d4f; box-shadow: 0 0 6px rgba(255, 77, 79, 0.5); }
.dot.green { background: #52c41a; box-shadow: 0 0 6px rgba(82, 196, 26, 0.5); }
.hist-chart {
  height: 300px;
}
</style>
