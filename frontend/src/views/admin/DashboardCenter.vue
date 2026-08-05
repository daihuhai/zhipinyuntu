<!--
  管理员大数据指挥中心 - 深色科技风大屏
  整合 6 KPI + 9 图表模块 + 实时日志流 + 底部跑马灯
-->
<template>
  <div class="dc-page" :class="{ 'dc-fullscreen': isFullscreen }">
    <!-- 顶部栏 -->
    <DHeader
      @refresh="fetchAll"
      @range-change="onRangeChange"
      @fullscreen="toggleFullscreen"
    />

    <!-- KPI 卡片行 -->
    <KpiRow :data="overview?.kpi as any" />

    <!-- 图表网格 -->
    <div class="dc-grid">
      <!-- 第一行 -->
      <UserGrowthChart :data="trend?.user_growth" class="col-4" />
      <CoreGauges :gauges="overview?.gauges || defaultGauges" class="col-4" />
      <LogStream :items="logs" class="col-4" />

      <!-- 第二行 -->
      <ResumeFunnel
        :data="trend?.resume_status"
        :parse-trend="trend?.resume_parse_trend"
        :ai-usage="trend?.ai_usage"
        class="col-4"
      />
      <CityDistChart :data="cityDist" class="col-4" />
      <SkillWordCloud :skills="trend?.hot_skills || []" class="col-4" />

      <!-- 第三行 -->
      <ApplicationFunnel :data="appStats" class="col-4" />
      <MatchHistChart :data="matchDist" class="col-4" />
      <SchoolRank :schools="schoolRank" class="col-4" />
    </div>

    <!-- 底部跑马灯 -->
    <div class="dc-marquee">
      <div class="marquee-content">
        <span v-for="(t, i) in marqueeTexts" :key="i">{{ t }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import DHeader from './components/DHeader.vue'
import KpiRow from './components/KpiRow.vue'
import UserGrowthChart from './components/UserGrowthChart.vue'
import CoreGauges from './components/CoreGauges.vue'
import LogStream from './components/LogStream.vue'
import ResumeFunnel from './components/ResumeFunnel.vue'
import CityDistChart from './components/CityDistChart.vue'
import SkillWordCloud from './components/SkillWordCloud.vue'
import ApplicationFunnel from './components/ApplicationFunnel.vue'
import MatchHistChart from './components/MatchHistChart.vue'
import SchoolRank from './components/SchoolRank.vue'
import { adminApi } from '@/api/admin'

const overview = ref<any>(null)
const trend = ref<any>(null)
const logs = ref<any[]>([])
const appStats = ref<any>({ total: 0, names: [], values: [] })
const matchDist = ref<any>({ buckets: [], counts: [], avg_score: 0, median_score: 0 })
const cityDist = ref<any>({ names: [], values: [] })
const schoolRank = ref<any[]>([])
const range = ref('7d')

// 全屏状态
const isFullscreen = ref(false)

const defaultGauges = { parse_rate: 0, job_active_rate: 0, avg_match_score: 0 }

const marqueeTexts = computed(() => {
  const k = overview.value?.kpi
  if (!k) return ['系统加载中...']
  return [
    `今日新增 ${k.users.delta} 用户`,
    `新增 ${k.resumes.delta} 简历`,
    `新增 ${k.jobs.delta} 职位`,
    `新增 ${k.applications.delta} 投递`,
    `匹配分 ${k.avg_score.total}`,
    `系统运行正常`,
    `后端状态 OK`,
  ]
})

const fetchOverview = async () => {
  try {
    const res: any = await adminApi.dashboardOverview()
    overview.value = res.data
  } catch {}
}

const fetchTrend = async () => {
  try {
    const days = range.value === '30d' ? 30 : range.value === '90d' ? 90 : 7
    const end = new Date()
    const start = new Date()
    start.setDate(start.getDate() - days)
    const fmt = (d: Date) => d.toISOString().split('T')[0]
    const res: any = await adminApi.dashboardTrend({ start_date: fmt(start), end_date: fmt(end) })
    trend.value = res.data
  } catch {}
}

const fetchLogs = async () => {
  try {
    const res: any = await adminApi.realtimeLogs(20)
    logs.value = res.data?.items || []
  } catch {}
}

const fetchAppStats = async () => {
  try {
    const res: any = await adminApi.applicationStats()
    appStats.value = res.data
  } catch {}
}

const fetchMatchDist = async () => {
  try {
    const res: any = await adminApi.matchDistribution()
    matchDist.value = res.data
  } catch {}
}

const fetchCityDist = async () => {
  try {
    const res: any = await adminApi.cityDistribution()
    cityDist.value = res.data
  } catch {}
}

const fetchSchoolRank = async () => {
  try {
    const res: any = await adminApi.schoolRank()
    schoolRank.value = res.data || []
  } catch {}
}

const fetchAll = async () => {
  await Promise.all([
    fetchOverview(),
    fetchTrend(),
    fetchLogs(),
    fetchAppStats(),
    fetchMatchDist(),
    fetchCityDist(),
    fetchSchoolRank(),
  ])
}

const onRangeChange = (v: string) => {
  range.value = v
  fetchAll()
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

// 轮询: 30s 刷新 KPI + 日志
let fastTimer: ReturnType<typeof setInterval> | null = null
// 轮询: 5min 刷新全量
let slowTimer: ReturnType<typeof setInterval> | null = null

const startTimers = () => {
  fastTimer = setInterval(() => { fetchOverview(); fetchLogs() }, 30000)
  slowTimer = setInterval(() => { fetchAll() }, 300000)
}
const clearTimers = () => {
  if (fastTimer) clearInterval(fastTimer)
  if (slowTimer) clearInterval(slowTimer)
}

const onVisibilityChange = () => {
  if (document.hidden) clearTimers()
  else startTimers()
}

onMounted(() => {
  fetchAll()
  startTimers()
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  clearTimers()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<style scoped>
.dc-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: calc(100vh - 100px);
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  padding: 12px;
  border-radius: 16px;
  overflow: visible;
}

/* 全屏模式 */
.dc-fullscreen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
  min-height: 100vh;
  border-radius: 0;
  padding: 16px;
  overflow-y: auto;
}

/* 网格: 3 列 */
.dc-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  flex: 1;
}
.col-4 { /* 占 1 列 */ }

/* 底部跑马灯 */
.dc-marquee {
  height: 32px;
  background: rgba(15, 12, 41, 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  align-items: center;
}
.marquee-content {
  display: flex;
  gap: 48px;
  white-space: nowrap;
  animation: marquee 30s linear infinite;
  padding-left: 100%;
}
.marquee-content span {
  font-size: 13px;
  color: #c4b5fd;
  display: flex;
  align-items: center;
}
.marquee-content span::before {
  content: '◆';
  margin-right: 6px;
  color: #a78bfa;
  font-size: 8px;
}
@keyframes marquee {
  0% { transform: translateX(0); }
  100% { transform: translateX(-200%); }
}

/* 响应式: 中屏 2 列 */
@media (max-width: 1400px) {
  .dc-grid { grid-template-columns: repeat(2, 1fr); }
}
/* 小屏 1 列 */
@media (max-width: 768px) {
  .dc-grid { grid-template-columns: 1fr; }
}
</style>
