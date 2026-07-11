<template>
  <div class="dc-panel">
    <div class="dc-panel-title">热门技能词云</div>
    <div ref="chartRef" class="wordcloud-chart"></div>
  </div>
</template>

<script setup lang="ts">
import 'echarts-wordcloud'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'

interface Skill {
  name: string
  count: number
}

const props = defineProps<{ skills: Skill[] }>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const colors = ['#a78bfa', '#60a5fa', '#52c41a', '#ff6b35', '#fbbf24', '#f472b6']
const MIN_SIZE = 12
const MAX_SIZE = 38

const buildOption = () => {
  const skills = props.skills || []
  const counts = skills.map((s) => Number(s.count) || 0)
  const maxCount = Math.max(...counts, 1)
  const minCount = Math.min(...counts, 0)
  const data = skills.map((s) => {
    const c = Number(s.count) || 0
    let size = MIN_SIZE
    if (maxCount > minCount) {
      size = MIN_SIZE + ((c - minCount) / (maxCount - minCount)) * (MAX_SIZE - MIN_SIZE)
    } else if (c > 0) {
      size = (MIN_SIZE + MAX_SIZE) / 2
    }
    return {
      name: s.name,
      value: c,
      textStyle: {
        color: colors[Math.floor(Math.random() * colors.length)],
      },
    }
  })
  return {
    backgroundColor: 'transparent',
    tooltip: {
      show: true,
      formatter: (p: any) => `${p.name}: ${p.value}`,
    },
    series: [
      {
        type: 'wordCloud',
        shape: 'circle',
        left: 'center',
        top: 'center',
        width: '100%',
        height: '100%',
        sizeRange: [MIN_SIZE, MAX_SIZE],
        rotationRange: [-30, 30],
        rotationStep: 30,
        gridSize: 8,
        drawOutOfBound: false,
        layoutAnimation: true,
        textStyle: {
          fontFamily: 'sans-serif',
          fontWeight: 'bold',
        },
        emphasis: {
          textStyle: {
            textShadowBlur: 10,
            textShadowColor: 'rgba(167,139,250,0.7)',
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

watch(() => props.skills, render, { deep: true })
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
.wordcloud-chart {
  height: 320px;
}
</style>
