<template>
  <div class="dc-panel">
    <div class="dc-panel-title">
      <span>简历解析次数 & AI Token 消耗</span>
      <el-tag size="small" type="success" effect="dark" class="live-tag">实时</el-tag>
    </div>

    <!-- AI Token 消耗汇总卡片 -->
    <div class="ai-summary">
      <div class="summary-card total">
        <div class="summary-label">AI 总调用</div>
        <div class="summary-value">{{ aiData.total_calls || 0 }}<span class="unit">次</span></div>
      </div>
      <div class="summary-card token">
        <div class="summary-label">Token 总消耗</div>
        <div class="summary-value">{{ formatTokens(aiData.total_tokens) }}</div>
      </div>
    </div>

    <!-- AI 调用分类明细 -->
    <div class="ai-breakdown">
      <div v-for="item in (aiData.breakdown || [])" :key="item.label" class="breakdown-item">
        <div class="breakdown-header">
          <span class="breakdown-label">{{ item.label }}</span>
          <span class="breakdown-count">{{ item.count }} 次</span>
        </div>
        <div class="breakdown-bar">
          <div class="bar-fill" :style="{ width: barWidth(item.tokens), background: barColor(item.label) }"></div>
        </div>
        <div class="breakdown-tokens">{{ formatTokens(item.tokens) }}</div>
      </div>
    </div>

    <!-- 解析次数趋势折线图 -->
    <div ref="chartRef" class="trend-chart"></div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch, computed } from 'vue'
import * as echarts from 'echarts'

interface AiUsage {
  total_calls: number
  total_tokens: number
  breakdown: Array<{ label: string; count: number; tokens: number }>
}

interface ParseTrend {
  days: string[]
  values: number[]
}

const props = defineProps<{
  data?: { names: string[]; values: number[] }
  parseTrend?: ParseTrend
  aiUsage?: AiUsage
}>()

const chartRef = ref<HTMLElement>()
let chart: echarts.ECharts | null = null

const aiData = computed<AiUsage>(() => props.aiUsage || { total_calls: 0, total_tokens: 0, breakdown: [] })
const trendData = computed<ParseTrend>(() => props.parseTrend || { days: [], values: [] })

const maxToken = computed(() => {
  const arr = aiData.value.breakdown || []
  return Math.max(...arr.map((i) => i.tokens), 1)
})

const barWidth = (tokens: number) => `${Math.max((tokens / maxToken.value) * 100, 2)}%`

const barColor = (label: string) => {
  const map: Record<string, string> = {
    简历解析: 'linear-gradient(90deg, #8b5cf6, #a78bfa)',
    解析失败: 'linear-gradient(90deg, #ff4d4f, #ff7875)',
    缺失分析: 'linear-gradient(90deg, #faad14, #ffc53d)',
    智能匹配: 'linear-gradient(90deg, #52c41a, #95de64)',
  }
  return map[label] || 'linear-gradient(90deg, #3b82f6, #60a5fa)'
}

const formatTokens = (n: number) => {
  if (!n) return '0'
  if (n >= 10000) return (n / 10000).toFixed(1) + '万'
  if (n >= 1000) return (n / 1000).toFixed(1) + 'K'
  return String(n)
}

const buildOption = () => {
  const days = trendData.value.days || []
  const values = trendData.value.values || []
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const p = params[0]
        return `${p.axisValue}<br/>解析次数: ${p.value} 次`
      },
    },
    grid: { top: 20, left: 40, right: 16, bottom: 30 },
    xAxis: {
      type: 'category',
      data: days,
      axisLabel: { color: '#c4b5fd', fontSize: 10, rotate: 30 },
      axisLine: { lineStyle: { color: 'rgba(167,139,250,0.3)' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { color: '#c4b5fd', fontSize: 10 },
      splitLine: { lineStyle: { color: 'rgba(167,139,250,0.1)' } },
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 3, color: '#8b5cf6', shadowBlur: 10, shadowColor: 'rgba(139,92,246,0.5)' },
        itemStyle: { color: '#a78bfa', borderColor: '#fff', borderWidth: 1 },
        areaStyle: {
          color: new (echarts as any).graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(139,92,246,0.4)' },
            { offset: 1, color: 'rgba(139,92,246,0.02)' },
          ]),
        },
        emphasis: {
          itemStyle: { borderWidth: 2, borderColor: '#fff', shadowBlur: 12 },
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

watch(() => [props.parseTrend, props.aiUsage], render, { deep: true })
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
  display: flex;
  align-items: center;
  gap: 8px;
}
.live-tag { font-size: 10px; }

/* AI 汇总卡片 */
.ai-summary {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}
.summary-card {
  flex: 1;
  padding: 12px 14px;
  border-radius: 10px;
  text-align: center;
}
.summary-card.total {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2), rgba(167, 139, 250, 0.1));
  border: 1px solid rgba(139, 92, 246, 0.3);
}
.summary-card.token {
  background: linear-gradient(135deg, rgba(82, 196, 26, 0.15), rgba(149, 222, 100, 0.08));
  border: 1px solid rgba(82, 196, 26, 0.3);
}
.summary-label {
  font-size: 11px;
  color: #c4b5fd;
  margin-bottom: 4px;
}
.summary-value {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
}
.summary-value .unit {
  font-size: 12px;
  font-weight: 400;
  color: #a78bfa;
  margin-left: 2px;
}

/* AI 分类明细 */
.ai-breakdown {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}
.breakdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
}
.breakdown-header {
  width: 90px;
  flex-shrink: 0;
}
.breakdown-label {
  font-size: 12px;
  color: #e0e0ff;
  display: block;
}
.breakdown-count {
  font-size: 10px;
  color: #a78bfa;
}
.breakdown-bar {
  flex: 1;
  height: 10px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 5px;
  overflow: hidden;
}
.bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s ease;
}
.breakdown-tokens {
  width: 60px;
  text-align: right;
  font-size: 12px;
  color: #95de64;
  font-weight: 600;
  flex-shrink: 0;
}

.trend-chart {
  height: 180px;
}
</style>
