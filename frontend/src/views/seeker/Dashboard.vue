<!--
  个人用户仪表盘
  - 欢迎横幅 + KPI 概览 + 快捷入口 + 后端连通状态
-->
<template>
  <div class="seeker-dashboard">
    <!-- 欢迎横幅 -->
    <el-card class="hero-card" shadow="never" :body-style="{ padding: '24px 28px' }">
      <div class="hero">
        <div class="hero-text">
          <h2>你好,{{ userInfo?.nickname || userInfo?.username || '求职者' }} 👋</h2>
          <p>欢迎回到智聘云图,让 AI 帮你看清每一段经历的价值。</p>
          <div class="hero-actions">
            <el-button type="primary" :icon="Upload" @click="$router.push('/seeker/resume/upload')">
              上传新简历
            </el-button>
            <el-button :icon="Search" plain @click="$router.push('/seeker/jobs')">
              浏览职位广场
            </el-button>
            <el-button :icon="Star" plain @click="$router.push('/seeker/favorites')">
              我的收藏
            </el-button>
          </div>
        </div>
        <el-icon class="hero-icon"><DataAnalysis /></el-icon>
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

    <!-- 主体内容 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="16">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="card-header">
              <span>简历解析进度</span>
              <el-button link type="primary" @click="$router.push('/seeker/resume/list')">查看全部</el-button>
            </div>
          </template>
          <div v-loading="resumeLoading">
            <el-empty v-if="!resumeList.length" description="尚未上传简历,点击上方按钮开始第一步">
              <el-button type="primary" plain @click="$router.push('/seeker/resume/upload')">立即上传</el-button>
            </el-empty>
            <el-table v-else :data="resumeList" stripe>
              <el-table-column prop="name" label="姓名" width="100" />
              <el-table-column prop="education" label="学历" width="80" />
              <el-table-column prop="work_years" label="工作年限" width="100">
                <template #default="{ row }">{{ row.work_years || 0 }} 年</template>
              </el-table-column>
              <el-table-column label="解析状态" width="100">
                <template #default="{ row }">
                  <el-tag :type="statusTag(row.parse_status)">{{ statusText(row.parse_status) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="created_at" label="上传时间" min-width="160">
                <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
              </el-table-column>
              <el-table-column label="操作" width="200" fixed="right">
                <template #default="{ row }">
                  <el-button link type="primary" @click="$router.push(`/seeker/graph?resume_id=${row.id}`)">能力图谱</el-button>
                  <el-button link type="success" @click="$router.push(`/seeker/recommend?resume_id=${row.id}`)">推荐职位</el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="8">
        <el-card shadow="never" class="section-card">
          <template #header>
            <div class="card-header">
              <span>求职动态</span>
              <el-tag type="info" size="small">近 14 天</el-tag>
            </div>
          </template>
          <div v-loading="trendLoading" class="trend-section">
            <!-- 投递趋势曲线图 -->
            <div ref="trendChartRef" class="trend-chart"></div>
            <!-- 投递状态分布 -->
            <div class="status-section">
              <div class="status-title">投递状态分布</div>
              <div class="status-item" v-for="s in statusList" :key="s.label">
                <span class="status-dot" :style="{ background: s.color }"></span>
                <span class="status-label">{{ s.label }}</span>
                <div class="status-bar-track">
                  <div class="status-bar-fill" :style="{ width: s.percent, background: s.color }"></div>
                </div>
                <span class="status-count">{{ s.count }}</span>
              </div>
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
  Upload,
  Search,
  Document,
  Position,
  Star,
  TrendCharts,
  DataAnalysis,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { resumeApi } from '@/api/resume'
import { applicationApi } from '@/api/application'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)

const resumeList = ref<any[]>([])
const resumeLoading = ref(false)
const applicationCount = ref(0)

// 求职动态
const trendLoading = ref(false)
const trendChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
const trendDays = ref<string[]>([])
const trendCounts = ref<number[]>([])
const byStatus = ref<Record<string, number>>({ '0': 0, '1': 0, '2': 0, '3': 0, '4': 0 })

// 投递状态列表
const statusList = computed(() => {
  const s = byStatus.value
  const total = Object.values(s).reduce((a, b) => a + b, 0) || 1
  const items = [
    { label: '已投递', key: '0', count: s['0'] || 0, color: '#1677ff' },
    { label: '已查看', key: '1', count: s['1'] || 0, color: '#13c2c2' },
    { label: '面试邀请', key: '2', count: s['2'] || 0, color: '#faad14' },
    { label: '不合适', key: '3', count: s['3'] || 0, color: '#bfbfbf' },
    { label: '已录用', key: '4', count: s['4'] || 0, color: '#52c41a' },
  ]
  return items.map(it => ({
    ...it,
    percent: `${Math.max((it.count / total) * 100, 4)}%`,
  }))
})

const fetchTrend = async () => {
  trendLoading.value = true
  try {
    const res: any = await applicationApi.myTrend()
    const d = res.data || {}
    trendDays.value = d.days || []
    trendCounts.value = d.counts || []
    byStatus.value = d.by_status || { '0': 0, '1': 0, '2': 0, '3': 0, '4': 0 }
    applicationCount.value = d.total || 0
    await nextTick()
    renderTrendChart()
  } catch (e) {
    // 静默失败
  } finally {
    trendLoading.value = false
  }
}

const renderTrendChart = () => {
  if (!trendChartRef.value) return
  if (trendChart) trendChart.dispose()
  trendChart = echarts.init(trendChartRef.value)
  trendChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: 30, right: 10, top: 20, bottom: 25 },
    xAxis: {
      type: 'category',
      data: trendDays.value,
      axisLabel: { fontSize: 10, color: '#888', interval: 1 },
      axisLine: { lineStyle: { color: '#ddd' } },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLabel: { fontSize: 10, color: '#888' },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
    },
    series: [{
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 5,
      data: trendCounts.value,
      itemStyle: { color: '#1677ff' },
      lineStyle: { width: 2.5, color: '#1677ff' },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(22,119,255,0.3)' },
          { offset: 1, color: 'rgba(22,119,255,0.02)' },
        ]),
      },
    }],
  })
}

const fetchResumes = async () => {
  resumeLoading.value = true
  try {
    const res: any = await resumeApi.list()
    resumeList.value = res.data?.items || []
  } catch (e) {
    resumeList.value = []
  } finally {
    resumeLoading.value = false
  }
}

const statusText = (s: number) => ({ 0: '待解析', 1: '解析中', 2: '成功', 3: '失败' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }[s] || 'info')
const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

const handleResize = () => trendChart?.resize()

onMounted(() => {
  fetchResumes()
  fetchTrend()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
})

// KPI 数据(简历数/投递数实时, 推荐职位/收藏 M4 接入)
const kpiList = computed(() => [
  { label: '我的简历', value: String(resumeList.value.length), icon: Document, color: '#1677ff', bg: '#e6f4ff' },
  { label: '推荐职位', value: '0', icon: Position, color: '#52c41a', bg: '#f6ffed' },
  { label: '投递记录', value: String(applicationCount.value), icon: TrendCharts, color: '#faad14', bg: '#fffbe6' },
  { label: '面试邀请', value: String(byStatus.value['2'] || 0), icon: Star, color: '#722ed1', bg: '#f9f0ff' },
])
</script>

<style scoped>
.seeker-dashboard {
  padding: 4px;
}
.hero-card {
  border: none;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
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
.section-card {
  border-radius: 10px;
  margin-bottom: 16px;
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
/* 求职动态面板 */
.trend-section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.trend-chart {
  width: 100%;
  height: 160px;
}
.status-section {
  border-top: 1px dashed var(--border-color);
  padding-top: 12px;
}
.status-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 10px;
}
.status-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 12px;
}
.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 0 6px currentColor;
}
.status-label {
  width: 56px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.status-bar-track {
  flex: 1;
  height: 6px;
  background: var(--fill-color, #f0f0f0);
  border-radius: 3px;
  overflow: hidden;
}
.status-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}
.status-count {
  min-width: 24px;
  text-align: right;
  font-weight: 600;
  color: var(--text-primary);
  flex-shrink: 0;
}
</style>
