<!--
  管理后台仪表盘 - 运营监控 (KPI + ECharts 图表)
-->
<template>
  <div class="admin-dashboard" v-loading="loading">
    <!-- KPI 总览 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="kpi in kpiCards" :key="kpi.label">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon" :style="{ background: kpi.bg, color: kpi.color }">
            <el-icon :size="24"><component :is="kpi.icon" /></el-icon>
          </div>
          <div class="kpi-meta">
            <div class="kpi-value">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 第一行 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">用户增长趋势 (近 14 天)</div></template>
          <div ref="userGrowthChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">简历解析状态分布</div></template>
          <div ref="resumeStatusChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区 第二行 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">职位状态分布</div></template>
          <div ref="jobStatusChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">热门技能 Top10</div></template>
          <div ref="hotSkillsChartRef" class="chart-box"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据明细 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">匹配统计</div></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="匹配记录数">{{ stats.matches?.total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="平均匹配分">{{ stats.matches?.avg_score || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">最近新增用户</div></template>
          <el-table :data="stats.recent_users || []" size="small" :max-height="220">
            <el-table-column prop="username" label="用户名" min-width="100" />
            <el-table-column prop="role" label="角色" width="120">
              <template #default="{ row }">{{ roleText(row.role) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" min-width="140">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, nextTick, ref } from 'vue'
import { User, Document, Briefcase, Connection, CirclePlus, Link, TrendCharts } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { adminApi } from '@/api/admin'

const stats = ref<any>({})
const trend = ref<any>({})
const loading = ref(false)

// 图表 DOM 引用
const userGrowthChartRef = ref<HTMLElement>()
const resumeStatusChartRef = ref<HTMLElement>()
const jobStatusChartRef = ref<HTMLElement>()
const hotSkillsChartRef = ref<HTMLElement>()

// 图表实例
let userGrowthChart: echarts.ECharts | null = null
let resumeStatusChart: echarts.ECharts | null = null
let jobStatusChart: echarts.ECharts | null = null
let hotSkillsChart: echarts.ECharts | null = null

const kpiCards = computed(() => [
  { label: '用户总数', value: stats.value.users?.total || 0, icon: User, color: '#1677ff', bg: '#e6f4ff' },
  { label: '简历总数', value: stats.value.resumes?.total || 0, icon: Document, color: '#52c41a', bg: '#f6ffed' },
  { label: '职位总数', value: stats.value.jobs?.total || 0, icon: Briefcase, color: '#faad14', bg: '#fffbe6' },
  { label: '匹配记录', value: stats.value.matches?.total || 0, icon: Connection, color: '#722ed1', bg: '#f9f0ff' },
  { label: '今日新增用户', value: stats.value.today_new_users ?? '--', icon: CirclePlus, color: '#eb2f96', bg: '#fff0f6' },
  { label: '今日匹配次数', value: stats.value.today_matches ?? '--', icon: Link, color: '#13c2c2', bg: '#e6fffb' },
  { label: '活跃用户数', value: stats.value.active_users ?? '--', icon: TrendCharts, color: '#fa8c16', bg: '#fff7e6' },
])

const roleText = (r: string) => ({ ROLE_SEEKER: '个人', ROLE_EMPLOYER: '企业', ROLE_ADMIN: '管理员' }[r] || r)
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const initUserGrowthChart = () => {
  if (!userGrowthChartRef.value) return
  userGrowthChart = echarts.init(userGrowthChartRef.value)
  const data = trend.value.user_growth || {}
  userGrowthChart.setOption({
    tooltip: { trigger: 'axis' },
    legend: { data: ['每日新增', '累计用户'], top: 0 },
    grid: { top: 40, left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.days || [], axisLabel: { fontSize: 11 } },
    yAxis: [
      { type: 'value', name: '每日新增' },
      { type: 'value', name: '累计' },
    ],
    series: [
      {
        name: '每日新增', type: 'bar', data: data.daily || [],
        itemStyle: { color: '#4096ff' },
      },
      {
        name: '累计用户', type: 'line', yAxisIndex: 1, data: data.cumulative || [],
        smooth: true, itemStyle: { color: '#52c41a' },
        areaStyle: { color: 'rgba(82,196,26,0.1)' },
      },
    ],
  })
}

const initResumeStatusChart = () => {
  if (!resumeStatusChartRef.value) return
  resumeStatusChart = echarts.init(resumeStatusChartRef.value)
  const data = trend.value.resume_status || {}
  resumeStatusChart.setOption({
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    legend: { bottom: 0 },
    series: [{
      type: 'pie', radius: ['40%', '65%'], center: ['50%', '45%'],
      data: (data.names || []).map((n: string, i: number) => ({ name: n, value: (data.values || [])[i] || 0 })),
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      label: { fontSize: 12 },
      color: ['#d9d9d9', '#faad14', '#52c41a', '#ff4d4f'],
    }],
  })
}

const initJobStatusChart = () => {
  if (!jobStatusChartRef.value) return
  jobStatusChart = echarts.init(jobStatusChartRef.value)
  const data = trend.value.job_status || {}
  jobStatusChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 30, left: 40, right: 20, bottom: 30 },
    xAxis: { type: 'category', data: data.names || [] },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar', data: data.values || [],
      itemStyle: {
        color: (params: any) => ['#d9d9d9', '#52c41a', '#ff4d4f'][params.dataIndex] || '#4096ff',
        borderRadius: [4, 4, 0, 0],
      },
      barWidth: '40%',
      label: { show: true, position: 'top' },
    }],
  })
}

const initHotSkillsChart = () => {
  if (!hotSkillsChartRef.value) return
  hotSkillsChart = echarts.init(hotSkillsChartRef.value)
  const skills = trend.value.hot_skills || []
  hotSkillsChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { top: 20, left: 100, right: 30, bottom: 20 },
    xAxis: { type: 'value' },
    yAxis: {
      type: 'category',
      data: skills.map((s: any) => s.name).reverse(),
      axisLabel: { fontSize: 11 },
    },
    series: [{
      type: 'bar',
      data: skills.map((s: any) => s.count).reverse(),
      itemStyle: {
        color: new (echarts as any).graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#1677ff' },
          { offset: 1, color: '#722ed1' },
        ]),
        borderRadius: [0, 4, 4, 0],
      },
      label: { show: true, position: 'right' },
    }],
  })
}

const handleResize = () => {
  userGrowthChart?.resize()
  resumeStatusChart?.resize()
  jobStatusChart?.resize()
  hotSkillsChart?.resize()
}

const fetch = async () => {
  loading.value = true
  try {
    const [statRes, trendRes]: any = await Promise.all([
      adminApi.dashboard(),
      adminApi.dashboardTrend(),
    ])
    stats.value = statRes.data || {}
    trend.value = trendRes.data || {}
    await nextTick()
    initUserGrowthChart()
    initResumeStatusChart()
    initJobStatusChart()
    initHotSkillsChart()
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetch()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  userGrowthChart?.dispose()
  resumeStatusChart?.dispose()
  jobStatusChart?.dispose()
  hotSkillsChart?.dispose()
})
</script>

<style scoped>
.kpi-row { margin-bottom: 16px; }
.kpi-card { border-radius: 10px; }
.kpi-card :deep(.el-card__body) { display: flex; align-items: center; gap: 14px; padding: 16px; }
.kpi-icon { width: 52px; height: 52px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.kpi-value { font-size: 24px; font-weight: 700; line-height: 1.2; }
.kpi-label { color: var(--text-secondary); font-size: 13px; margin-top: 2px; }
.section-card { border-radius: 10px; margin-bottom: 16px; }
.card-header { font-weight: 600; }
.chart-box { height: 280px; }
</style>
