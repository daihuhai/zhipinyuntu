<!--
  企业用户仪表盘 (重设计版)
  - 欢迎横幅 + KPI 概览 + 投递趋势曲线图 + 状态分布饼图 + 职位热度榜
  - 使用 ECharts 6 直观展示数据
-->
<template>
  <div class="employer-dashboard">
    <!-- 欢迎横幅 -->
    <el-card class="hero-card" shadow="never" :body-style="{ padding: '24px 28px' }">
      <div class="hero">
        <div class="hero-text">
          <h2>{{ companyName }} 的人才中台</h2>
          <p>用灵犀解析每份简历,把对的人推到对的位置。</p>
          <div class="hero-actions">
            <el-button type="primary" :icon="EditPen" @click="$router.push('/employer/job/create')">
              发布新职位
            </el-button>
            <el-button :icon="Tickets" plain @click="$router.push('/employer/applications')">
              投递管理
            </el-button>
          </div>
        </div>
        <el-icon class="hero-icon"><Briefcase /></el-icon>
      </div>
    </el-card>

    <!-- KPI 卡片 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="kpi in kpiList" :key="kpi.label">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon" :style="{ background: kpi.bg, color: kpi.color }">
            <el-icon :size="22"><component :is="kpi.icon" /></el-icon>
          </div>
          <div class="kpi-meta">
            <div class="kpi-value">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区: 投递趋势曲线 + 状态分布饼图 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="16">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>投递趋势</span>
              <el-tag type="info" size="small">近 14 天</el-tag>
            </div>
          </template>
          <div ref="trendChartRef" class="chart-box" v-loading="loading"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>投递状态分布</span>
              <el-tag type="info" size="small">实时</el-tag>
            </div>
          </template>
          <div ref="statusChartRef" class="chart-box" v-loading="loading"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 职位热度榜 + 招聘漏斗 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>职位投递热度 Top10</span>
              <el-tag type="info" size="small">全部</el-tag>
            </div>
          </template>
          <div ref="jobDistChartRef" class="chart-box" v-loading="loading"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>招聘漏斗</span>
              <el-tag type="info" size="small">转化</el-tag>
            </div>
          </template>
          <div v-loading="loading" class="funnel">
            <div class="funnel-item" v-for="stage in funnelStages" :key="stage.label">
              <div class="funnel-info">
                <span class="funnel-label">{{ stage.label }}</span>
                <span class="funnel-count">{{ stage.count }}</span>
              </div>
              <div class="funnel-track">
                <div class="funnel-bar" :style="{ width: stage.width, background: stage.color }"></div>
              </div>
              <span class="funnel-rate">{{ stage.rate }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import {
  EditPen,
  Briefcase,
  Document,
  User,
  OfficeBuilding,
  Tickets,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { applicationApi } from '@/api/application'

const userStore = useUserStore()
const companyName = computed(
  () => userStore.userInfo?.nickname || userStore.userInfo?.username || '贵公司'
)

const loading = ref(false)
const activeJobs = ref(0)
const totalApps = ref(0)
const byStatus = ref<Record<string, number>>({ '0': 0, '1': 0, '2': 0, '3': 0, '4': 0 })

// 趋势数据
const trendDays = ref<string[]>([])
const trendCounts = ref<number[]>([])
const jobDistribution = ref<{ name: string; value: number }[]>([])

// ECharts 实例
const trendChartRef = ref<HTMLElement>()
const statusChartRef = ref<HTMLElement>()
const jobDistChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let statusChart: echarts.ECharts | null = null
let jobDistChart: echarts.ECharts | null = null

const fetchSummary = async () => {
  loading.value = true
  try {
    const [sumRes, trendRes] = await Promise.all([
      applicationApi.employerSummary(),
      applicationApi.employerTrend(),
    ])
    const d = (sumRes as any).data || {}
    activeJobs.value = d.active_jobs || 0
    totalApps.value = d.total_applications || 0
    byStatus.value = d.by_status || { '0': 0, '1': 0, '2': 0, '3': 0, '4': 0 }

    const td = (trendRes as any).data || {}
    trendDays.value = td.days || []
    trendCounts.value = td.counts || []
    jobDistribution.value = td.job_distribution || []

    await nextTick()
    renderCharts()
  } catch (e) {
    // 静默失败, KPI 保持 0
  } finally {
    loading.value = false
  }
}

// KPI 数据
const kpiList = computed(() => [
  { label: '在招职位', value: String(activeJobs.value), icon: Briefcase, color: '#1677ff', bg: '#e6f4ff' },
  { label: '收到简历', value: String(totalApps.value), icon: Document, color: '#52c41a', bg: '#f6ffed' },
  { label: '面试邀请', value: String(byStatus.value['2'] || 0), icon: User, color: '#faad14', bg: '#fffbe6' },
  { label: '已录用', value: String(byStatus.value['4'] || 0), icon: OfficeBuilding, color: '#722ed1', bg: '#f9f0ff' },
])

// 招聘漏斗
const funnelStages = computed(() => {
  const s = byStatus.value
  const applied = s['0'] + s['1'] + s['2'] + s['3'] + s['4']
  const viewed = s['1'] + s['2'] + s['4']
  const interview = s['2']
  const offered = s['4']
  const max = Math.max(applied, 1)
  const pct = (n: number) => `${Math.max((n / max) * 100, 8)}%`
  const rate = (n: number) => (applied > 0 ? `${((n / applied) * 100).toFixed(0)}%` : '0%')
  return [
    { label: '简历投递', count: applied, width: '100%', color: 'linear-gradient(90deg,#1677ff,#4096ff)', rate: rate(applied) },
    { label: '已查看', count: viewed, width: pct(viewed), color: 'linear-gradient(90deg,#0958d9,#1677ff)', rate: rate(viewed) },
    { label: '面试邀请', count: interview, width: pct(interview), color: 'linear-gradient(90deg,#faad14,#fa8c16)', rate: rate(interview) },
    { label: '最终录用', count: offered, width: pct(offered), color: 'linear-gradient(90deg,#52c41a,#73d13d)', rate: rate(offered) },
  ]
})

// 渲染 ECharts 图表
const renderCharts = () => {
  // 投递趋势折线图
  if (trendChartRef.value) {
    if (trendChart) trendChart.dispose()
    trendChart = echarts.init(trendChartRef.value)
    trendChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: 40, right: 20, top: 30, bottom: 30 },
      xAxis: {
        type: 'category',
        data: trendDays.value,
        axisLabel: { fontSize: 11, color: '#888' },
        axisLine: { lineStyle: { color: '#ddd' } },
      },
      yAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { fontSize: 11, color: '#888' },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
      },
      series: [{
        name: '投递量',
        type: 'line',
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        data: trendCounts.value,
        itemStyle: { color: '#1677ff' },
        lineStyle: { width: 3, color: '#1677ff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(22,119,255,0.3)' },
            { offset: 1, color: 'rgba(22,119,255,0.02)' },
          ]),
        },
      }],
    })
  }

  // 状态分布饼图
  if (statusChartRef.value) {
    if (statusChart) statusChart.dispose()
    statusChart = echarts.init(statusChartRef.value)
    const s = byStatus.value
    const pieData = [
      { name: '已投递', value: s['0'] || 0, itemStyle: { color: '#1677ff' } },
      { name: '已查看', value: s['1'] || 0, itemStyle: { color: '#13c2c2' } },
      { name: '面试邀请', value: s['2'] || 0, itemStyle: { color: '#faad14' } },
      { name: '不合适', value: s['3'] || 0, itemStyle: { color: '#bfbfbf' } },
      { name: '已录用', value: s['4'] || 0, itemStyle: { color: '#52c41a' } },
    ].filter(d => d.value > 0)
    statusChart.setOption({
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0, left: 'center', textStyle: { fontSize: 12 } },
      series: [{
        type: 'pie',
        radius: ['40%', '65%'],
        center: ['50%', '42%'],
        avoidLabelOverlap: true,
        label: { show: false },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
        },
        data: pieData.length ? pieData : [{ name: '暂无数据', value: 1, itemStyle: { color: '#f0f0f0' } }],
      }],
    })
  }

  // 职位投递热度柱状图
  if (jobDistChartRef.value) {
    if (jobDistChart) jobDistChart.dispose()
    jobDistChart = echarts.init(jobDistChartRef.value)
    const dist = jobDistribution.value
    const names = dist.map(d => d.name.length > 8 ? d.name.slice(0, 8) + '…' : d.name)
    const values = dist.map(d => d.value)
    jobDistChart.setOption({
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: 10, right: 30, top: 20, bottom: 10, containLabel: true },
      xAxis: {
        type: 'value',
        minInterval: 1,
        axisLabel: { fontSize: 11, color: '#888' },
        splitLine: { lineStyle: { color: '#f0f0f0' } },
      },
      yAxis: {
        type: 'category',
        data: names.reverse(),
        axisLabel: { fontSize: 11, color: '#555' },
        axisLine: { lineStyle: { color: '#ddd' } },
      },
      series: [{
        type: 'bar',
        data: values.reverse(),
        barWidth: '55%',
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#4096ff' },
            { offset: 1, color: '#1677ff' },
          ]),
          borderRadius: [0, 4, 4, 0],
        },
        label: { show: true, position: 'right', fontSize: 11, color: '#555' },
      }],
    })
  }
}

// 响应式重绘
const handleResize = () => {
  trendChart?.resize()
  statusChart?.resize()
  jobDistChart?.resize()
}

onMounted(() => {
  fetchSummary()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  statusChart?.dispose()
  jobDistChart?.dispose()
})
</script>

<style scoped>
.employer-dashboard {
  padding: 4px;
}
.hero-card {
  border: none;
  background: linear-gradient(135deg, #0958d9 0%, #1677ff 100%);
  border-radius: 12px;
  margin-bottom: 16px;
}
.hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
}
.hero-text h2 {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 8px;
}
.hero-text p {
  opacity: 0.92;
  margin-bottom: 16px;
}
.hero-actions .el-button + .el-button {
  margin-left: 12px;
}
.hero-icon {
  font-size: 96px;
  opacity: 0.35;
}
.kpi-row {
  margin-bottom: 16px;
}
.kpi-card {
  border-radius: 10px;
  display: flex;
  align-items: center;
  padding: 16px;
}
.kpi-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
}
.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.kpi-value {
  font-size: 22px;
  font-weight: 600;
  line-height: 1.2;
}
.kpi-label {
  color: var(--text-secondary);
  font-size: 13px;
  margin-top: 2px;
}
.chart-card {
  border-radius: 10px;
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.chart-box {
  width: 100%;
  height: 300px;
}

/* 招聘漏斗 (横向进度条版) */
.funnel {
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 12px 8px;
  min-height: 240px;
  justify-content: center;
}
.funnel-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.funnel-info {
  width: 90px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}
.funnel-label { font-size: 13px; color: var(--text-secondary); }
.funnel-count { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.funnel-track {
  flex: 1;
  height: 28px;
  background: #f5f5f5;
  border-radius: 6px;
  overflow: hidden;
}
.funnel-bar {
  height: 100%;
  border-radius: 6px;
  transition: width 0.5s ease;
}
.funnel-rate {
  width: 42px;
  text-align: right;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  flex-shrink: 0;
}
</style>
