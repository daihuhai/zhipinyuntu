<!--
  管理后台仪表盘 - 9 图表 + 时间筛选 + 全屏数据大屏
-->
<template>
  <div class="admin-dashboard" :class="{ 'fs-on': isFullscreen }">
    <!-- ===== 非全屏工具栏 ===== -->
    <div v-if="!isFullscreen" class="toolbar">
      <div class="toolbar-left">
        <span class="toolbar-label">数据时间范围:</span>
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          start-placeholder="开始日期"
          end-placeholder="结束日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          :clearable="true"
          style="width: 280px"
          @change="onDateChange"
        />
        <el-button :icon="Refresh" :loading="loading" @click="fetchAll">刷新</el-button>
      </div>
      <el-button type="primary" :icon="FullScreen" plain size="small" @click="toggleFullscreen">全屏展示</el-button>
    </div>

    <!-- ===== KPI 总览 ===== -->
    <el-row :gutter="12" class="kpi-row">
      <el-col :xs="12" :sm="8" :md="isFullscreen ? 3 : 6" v-for="kpi in kpiCards" :key="kpi.label">
        <div class="kpi-card" :style="{ borderLeft: `4px solid ${kpi.color}` }">
          <div class="kpi-icon" :style="{ background: kpi.bg, color: kpi.color }">
            <el-icon :size="22"><component :is="kpi.icon" /></el-icon>
          </div>
          <div class="kpi-meta">
            <div class="kpi-value">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- ===== 9 图表网格 ===== -->
    <div class="chart-grid" :class="{ 'fs-grid': isFullscreen }">
      <div v-for="c in chartConfigs" :key="c.id" class="chart-cell">
        <div class="chart-cell-header">{{ c.title }}</div>
        <div :ref="el => setChartRef(c.id, el)" class="chart-canvas"></div>
      </div>
    </div>
  </div>

  <!-- ===== 全屏顶栏 (Teleport 到 body 确保覆盖侧边栏) ===== -->
  <Teleport v-if="isFullscreen" to="body">
    <div class="fs-overlay">
      <div class="fs-brand">
        <el-icon :size="22" color="#1677ff"><Odometer /></el-icon>
        <span>智聘云图 · 数据指挥中心</span>
      </div>
      <div class="fs-clock">{{ clockText }}</div>
      <el-button type="danger" :icon="Close" plain size="small" @click="toggleFullscreen">退出全屏</el-button>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, nextTick, ref, watch } from 'vue'
import { User, Document, Briefcase, Connection, CirclePlus, Link, TrendCharts, FullScreen, Close, Odometer, Refresh } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { adminApi } from '@/api/admin'

const stats = ref<any>({})
const trend = ref<any>({})
const extData = ref<any>({}) // applications, match-dist, city-dist
const loading = ref(false)

// 时间筛选
const dateRange = ref<[string, string] | null>(null)

// 全屏模式
const isFullscreen = ref(false)
const clockText = ref('')
let clockTimer: any = null

const updateClock = () => {
  clockText.value = new Date().toLocaleString('zh-CN', { hour12: false })
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  if (isFullscreen.value) {
    clockTimer = setInterval(updateClock, 1000)
    updateClock()
  } else {
    if (clockTimer) { clearInterval(clockTimer); clockTimer = null }
  }
  nextTick(() => setTimeout(() => resizeAll(), 350))
}

// ===== 图表 DOM 引用 =====
const chartRefs: Record<string, HTMLElement | null> = {}
const chartInstances: Record<string, echarts.ECharts | null> = {}

const setChartRef = (id: string, el: any) => {
  chartRefs[id] = el
}

// 9 个图表配置
const chartConfigs = [
  { id: 'userGrowth', title: '用户增长趋势' },
  { id: 'resumeStatus', title: '简历解析状态分布' },
  { id: 'jobStatus', title: '职位状态分布' },
  { id: 'hotSkills', title: '热门技能 Top10' },
  { id: 'aiParseTrend', title: '灵犀AI解析趋势' },
  { id: 'aiUsage', title: '灵犀AI调用统计' },
  { id: 'appStats', title: '投递状态分布' },
  { id: 'matchDist', title: '匹配分分布' },
  { id: 'cityDist', title: '职位城市分布 Top10' },
]

const kpiCards = computed(() => [
  { label: '用户总数', value: stats.value.users?.total || 0, icon: User, color: '#1677ff', bg: '#e6f4ff' },
  { label: '简历总数', value: stats.value.resumes?.total || 0, icon: Document, color: '#52c41a', bg: '#f6ffed' },
  { label: '职位总数', value: stats.value.jobs?.total || 0, icon: Briefcase, color: '#faad14', bg: '#fffbe6' },
  { label: '匹配记录', value: stats.value.matches?.total || 0, icon: Connection, color: '#722ed1', bg: '#f9f0ff' },
  { label: '今日新增用户', value: stats.value.today_new_users ?? '--', icon: CirclePlus, color: '#eb2f96', bg: '#fff0f6' },
  { label: '今日匹配次数', value: stats.value.today_matches ?? '--', icon: Link, color: '#13c2c2', bg: '#e6fffb' },
  { label: '活跃用户数', value: stats.value.active_users ?? '--', icon: TrendCharts, color: '#fa8c16', bg: '#fff7e6' },
])

// ===== 图表初始化 =====
const initChart = (id: string, option: any) => {
  const el = chartRefs[id]
  if (!el) return
  if (chartInstances[id]) {
    chartInstances[id]!.dispose()
  }
  const inst = echarts.init(el)
  inst.setOption(option)
  chartInstances[id] = inst
}

const initUserGrowth = () => {
  const d = trend.value.user_growth || {}
  initChart('userGrowth', {
    tooltip: { trigger: 'axis' },
    legend: { data: ['每日新增', '累计用户'], top: 0, textStyle: { fontSize: 11 } },
    grid: { top: 36, left: 40, right: 40, bottom: 30 },
    xAxis: { type: 'category', data: d.days || [], axisLabel: { fontSize: 10, rotate: d.days?.length > 10 ? 30 : 0 } },
    yAxis: [{ type: 'value', name: '新增' }, { type: 'value', name: '累计' }],
    series: [
      { name: '每日新增', type: 'bar', data: d.daily || [], itemStyle: { color: '#4096ff' } },
      { name: '累计用户', type: 'line', yAxisIndex: 1, data: d.cumulative || [], smooth: true, itemStyle: { color: '#52c41a' }, areaStyle: { color: 'rgba(82,196,26,0.1)' } },
    ],
  })
}

const initResumeStatus = () => {
  const d = trend.value.resume_status || {}
  initChart('resumeStatus', {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'pie', radius: ['38%', '62%'], center: ['50%', '42%'],
      data: (d.names || []).map((n: string, i: number) => ({ name: n, value: (d.values || [])[i] || 0 })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { fontSize: 11 },
      color: ['#d9d9d9', '#faad14', '#52c41a', '#ff4d4f'],
    }],
  })
}

const initJobStatus = () => {
  const d = trend.value.job_status || {}
  initChart('jobStatus', {
    tooltip: { trigger: 'axis' },
    grid: { top: 20, left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: d.names || [], axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: d.values || [], barWidth: '40%',
      itemStyle: { color: (p: any) => ['#d9d9d9', '#52c41a', '#ff4d4f'][p.dataIndex] || '#4096ff', borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: 'top', fontSize: 11 },
    }],
  })
}

const initHotSkills = () => {
  const skills = trend.value.hot_skills || []
  initChart('hotSkills', {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, left: 90, right: 30, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: skills.map((s: any) => s.name).reverse(), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: skills.map((s: any) => s.count).reverse(),
      itemStyle: { color: new (echarts as any).graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#1677ff' }, { offset: 1, color: '#722ed1' }]), borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 11 },
    }],
  })
}

const initAiParseTrend = () => {
  const d = trend.value.resume_parse_trend || {}
  initChart('aiParseTrend', {
    tooltip: { trigger: 'axis' },
    grid: { top: 20, left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: d.days || [], axisLabel: { fontSize: 10, rotate: d.days?.length > 10 ? 30 : 0 } },
    yAxis: { type: 'value', name: '次数' },
    series: [{
      type: 'line', data: d.values || [], smooth: true,
      itemStyle: { color: '#722ed1' },
      areaStyle: { color: 'rgba(114,46,209,0.12)' },
      lineStyle: { width: 2 },
    }],
  })
}

const initAiUsage = () => {
  const d = trend.value.ai_usage || {}
  const breakdown = d.breakdown || []
  initChart('aiUsage', {
    tooltip: { trigger: 'axis' },
    legend: { top: 0, textStyle: { fontSize: 11 } },
    grid: { top: 36, left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: breakdown.map((b: any) => b.label), axisLabel: { fontSize: 10, rotate: 15 } },
    yAxis: [{ type: 'value', name: '次数' }, { type: 'value', name: 'Token' }],
    series: [
      { name: '调用次数', type: 'bar', data: breakdown.map((b: any) => b.count), itemStyle: { color: '#4096ff', borderRadius: [4, 4, 0, 0] } },
      { name: 'Token消耗', type: 'line', yAxisIndex: 1, data: breakdown.map((b: any) => b.tokens), itemStyle: { color: '#fa8c16' }, smooth: true },
    ],
  })
}

const initAppStats = () => {
  const d = extData.value.applications || {}
  const names = d.names || ['已投递', '已查看', '面试邀请', '不合适', '已录用']
  const values = d.values || [0, 0, 0, 0, 0]
  initChart('appStats', {
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0, textStyle: { fontSize: 11 } },
    series: [{
      type: 'funnel',
      left: '10%', right: '10%', top: 10, bottom: 30,
      minSize: '20%',
      data: names.map((n: string, i: number) => ({ name: n, value: values[i] })),
      label: { fontSize: 11 },
      color: ['#4096ff', '#52c41a', '#722ed1', '#ff4d4f', '#faad14'],
    }],
  })
}

const initMatchDist = () => {
  const d = extData.value.matchDist || {}
  const buckets = d.buckets || ['0-20', '20-40', '40-60', '60-80', '80-100']
  const counts = d.counts || []
  initChart('matchDist', {
    tooltip: { trigger: 'axis' },
    grid: { top: 20, left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: buckets, axisLabel: { fontSize: 11 } },
    yAxis: { type: 'value', name: '人数' },
    series: [{
      type: 'bar', data: counts, barWidth: '50%',
      itemStyle: {
        color: new (echarts as any).graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#ff4d4f' },
          { offset: 0.5, color: '#faad14' },
          { offset: 1, color: '#52c41a' },
        ]),
        borderRadius: [4, 4, 0, 0],
      },
      label: { show: true, position: 'top', fontSize: 11 },
    }],
  })
}

const initCityDist = () => {
  const d = extData.value.cityDist || {}
  const names = d.names || []
  const values = d.values || []
  initChart('cityDist', {
    tooltip: { trigger: 'axis' },
    grid: { top: 10, left: 80, right: 30, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: [...names].reverse(), axisLabel: { fontSize: 11 } },
    series: [{
      type: 'bar',
      data: [...values].reverse(),
      itemStyle: { color: new (echarts as any).graphic.LinearGradient(0, 0, 1, 0, [{ offset: 0, color: '#13c2c2' }, { offset: 1, color: '#1677ff' }]), borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: 'right', fontSize: 11 },
    }],
  })
}

const initAllCharts = () => {
  initUserGrowth()
  initResumeStatus()
  initJobStatus()
  initHotSkills()
  initAiParseTrend()
  initAiUsage()
  initAppStats()
  initMatchDist()
  initCityDist()
}

const resizeAll = () => {
  Object.values(chartInstances).forEach(c => c?.resize())
}

// ===== 数据获取 =====
const fetchAll = async () => {
  loading.value = true
  try {
    const params: any = {}
    if (dateRange.value) {
      params.start_date = dateRange.value[0]
      params.end_date = dateRange.value[1]
    }
    const [statRes, trendRes, appRes, matchRes, cityRes]: any = await Promise.all([
      adminApi.dashboard(),
      adminApi.dashboardTrend(params),
      adminApi.applicationStats(),
      adminApi.matchDistribution(),
      adminApi.cityDistribution(),
    ])
    stats.value = statRes.data || {}
    trend.value = trendRes.data || {}
    extData.value = {
      applications: appRes.data || {},
      matchDist: matchRes.data || {},
      cityDist: cityRes.data || {},
    }
    await nextTick()
    initAllCharts()
  } finally {
    loading.value = false
  }
}

const onDateChange = () => {
  fetchAll()
}

// 监听全屏切换, 重新初始化图表
watch(isFullscreen, () => {
  nextTick(() => setTimeout(() => {
    initAllCharts()
    resizeAll()
  }, 400))
})

onMounted(() => {
  fetchAll()
  window.addEventListener('resize', resizeAll)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', resizeAll)
  if (clockTimer) clearInterval(clockTimer)
  Object.values(chartInstances).forEach(c => c?.dispose())
})
</script>

<style scoped>
/* ===== 工具栏 ===== */
.toolbar {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px; flex-wrap: wrap; gap: 8px;
}
.toolbar-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.toolbar-label { font-size: 13px; color: #666; white-space: nowrap; }

/* ===== KPI 卡片 ===== */
.kpi-row { margin-bottom: 14px; }
.kpi-card {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 14px; background: #fff; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06); margin-bottom: 8px;
}
.kpi-icon { width: 44px; height: 44px; border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-value { font-size: 22px; font-weight: 700; line-height: 1.2; }
.kpi-label { color: #888; font-size: 12px; margin-top: 2px; }

/* ===== 图表网格 ===== */
.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}
.chart-cell {
  background: #fff; border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  overflow: hidden;
  min-width: 0;
}
.chart-cell-header {
  padding: 10px 14px; font-size: 13px; font-weight: 600;
  border-bottom: 1px solid #f0f0f0; white-space: nowrap;
}
.chart-canvas { height: 240px; padding: 4px; }

/* ===== 全屏模式 ===== */
.fs-on {
  position: fixed !important;
  top: 0 !important; left: 0 !important;
  width: 100vw !important; height: 100vh !important;
  z-index: 99998 !important;
  background: #f0f2f5 !important;
  padding: 56px 16px 10px !important;
  overflow-y: auto !important;
}
.fs-on .toolbar { display: none !important; }
.fs-on .kpi-card { padding: 8px 10px; }
.fs-on .kpi-value { font-size: 18px; }
.fs-on .kpi-icon { width: 36px; height: 36px; }
.fs-on .kpi-label { font-size: 11px; }
.fs-grid { gap: 10px; grid-template-columns: repeat(3, 1fr) !important; }
.fs-on .chart-cell-header { padding: 6px 12px; font-size: 12px; }
.fs-on .chart-canvas { height: calc((100vh - 220px) / 3); }
</style>

<!-- 全屏覆盖层样式 (非 scoped, 确保 Teleport 元素生效) -->
<style>
.fs-overlay {
  position: fixed; top: 0; left: 0; right: 0;
  z-index: 99999;
  background: linear-gradient(135deg, #001529 0%, #003a70 100%);
  padding: 8px 24px;
  display: flex; align-items: center; justify-content: space-between;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}
.fs-brand {
  display: flex; align-items: center; gap: 10px;
  font-size: 18px; font-weight: 700; color: #fff;
}
.fs-clock {
  font-size: 16px; color: #ffffffaa;
  font-variant-numeric: tabular-nums;
}
</style>
