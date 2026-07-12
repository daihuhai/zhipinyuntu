<!--
  职位详情 (求职者浏览)
-->
<template>
  <div class="job-detail-page" v-loading="loading">
    <el-page-header @back="$router.back()" class="page-header">
      <template #content>
        <span class="header-title">职位详情</span>
      </template>
    </el-page-header>

    <el-card v-if="job" shadow="never" class="detail-card">
      <div class="job-head">
        <div class="head-left">
          <h2 class="job-title">{{ job.title }}</h2>
          <div class="job-salary">{{ formatSalary(job.salary_min, job.salary_max) }}</div>
        </div>
        <div class="head-right">
          <el-button
            v-if="isSeeker"
            :type="favorited ? 'warning' : 'default'"
            :icon="favorited ? StarFilled : Star"
            :loading="favoriteLoading"
            @click="toggleFavorite"
          >
            {{ favorited ? '已收藏' : '收藏' }}
          </el-button>
          <el-button type="success" :icon="Position" :loading="applying" @click="openApplyDialog">立即投递</el-button>
          <el-button :icon="ChatDotRound" @click="contactEmployer">联系企业</el-button>
          <el-button :icon="Position" @click="goRecommend">去推荐职位</el-button>
        </div>
      </div>

      <div class="job-company">
        <el-icon><OfficeBuilding /></el-icon>
        <span>{{ job.company || '匿名企业' }}</span>
        <el-divider direction="vertical" />
        <span>{{ job.department || '部门未公开' }}</span>
        <el-divider direction="vertical" />
        <span>{{ job.work_city || '城市不限' }}</span>
      </div>

      <div class="job-meta">
        <el-tag type="info">经验: {{ job.experience_required || '不限' }}</el-tag>
        <el-tag type="info">学历: {{ job.education_required || '不限' }}</el-tag>
        <el-tag type="info">类型: {{ job.job_type || '全职' }}</el-tag>
        <el-tag type="info">招聘人数: {{ job.headcount || '-' }}</el-tag>
      </div>

      <el-divider content-position="left">职位描述</el-divider>
      <div class="job-desc">
        <pre>{{ job.description || '暂无描述' }}</pre>
      </div>

      <template v-if="job.requirements?.length">
        <el-divider content-position="left">技能要求</el-divider>
        <div class="skill-reqs">
          <el-tag
            v-for="r in job.requirements"
            :key="r.id"
            :type="reqTagType(r.req_type)"
            effect="light"
            class="req-tag"
          >
            {{ r.skill_name }}
            <span v-if="r.skill_level" class="req-level"> · {{ r.skill_level }}</span>
            <span v-if="r.req_type" class="req-type"> ({{ reqTypeText(r.req_type) }})</span>
          </el-tag>
        </div>
      </template>

      <el-divider />
      <div class="job-footer">
        <span class="muted">发布时间: {{ formatDate(job.created_at) }}</span>
      </div>
    </el-card>

    <el-empty v-if="!loading && !job" description="职位不存在或已下架">
      <el-button type="primary" @click="$router.push('/seeker/jobs')">返回职位广场</el-button>
    </el-empty>

    <!-- 岗位能力要求图谱 -->
    <el-card v-if="job" shadow="never" class="graph-card">
      <template #header>
        <div class="card-header">
          <span>岗位能力要求图谱</span>
          <el-tag type="info" size="small">力导向图</el-tag>
        </div>
      </template>
      <div v-loading="graphLoading" class="graph-wrap">
        <div ref="chartRef" id="jobGraphChart" class="job-graph-chart"></div>
        <el-empty v-if="!graphLoading && graphEmpty" description="暂无能力要求数据" :image-size="80" />
      </div>
    </el-card>

    <!-- 投递对话框 -->
    <el-dialog v-model="dialogVisible" title="投递简历" width="520px">
      <el-descriptions :column="1" border v-if="job">
        <el-descriptions-item label="职位">{{ job.title }}</el-descriptions-item>
        <el-descriptions-item label="公司">{{ job.company || '匿名企业' }}</el-descriptions-item>
        <el-descriptions-item label="薪资">{{ formatSalary(job.salary_min, job.salary_max) }}</el-descriptions-item>
      </el-descriptions>
      <div class="apply-form">
        <div class="form-label">选择简历:</div>
        <el-select v-model="applyResumeId" placeholder="请选择简历" style="width: 100%" :disabled="resumes.length === 0">
          <el-option
            v-for="r in resumes"
            :key="r.id"
            :label="`${r.name || '简历#' + r.id} - ${r.education || ''}`"
            :value="r.id"
          />
        </el-select>
        <div v-if="resumes.length === 0" class="empty-tip">
          暂无可用简历, 请先
          <el-link type="primary" @click="$router.push('/seeker/resume/upload')">上传简历</el-link>
        </div>
        <div class="form-label" style="margin-top: 12px">求职信 (选填):</div>
        <el-input
          v-model="coverLetter"
          type="textarea"
          :rows="4"
          placeholder="向 HR 展示你的诚意"
        />
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" :disabled="!applyResumeId" @click="submitApply">确认投递</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Position, OfficeBuilding, ChatDotRound, Star, StarFilled } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { graphApi } from '@/api/graph'
import { resumeApi } from '@/api/resume'
import { applicationApi } from '@/api/application'
import { useUserStore } from '@/stores/user'
import { formatSalary } from '@/utils/format'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 当前用户是否为求职者
const isSeeker = computed(() => userStore.userInfo?.role === 'ROLE_SEEKER')

const job = ref<any>(null)
const loading = ref(false)

// 投递相关
const resumes = ref<any[]>([])
const applyResumeId = ref<number | null>(null)
const coverLetter = ref('')
const dialogVisible = ref(false)
const submitting = ref(false)
const applying = ref(false)

// 收藏相关
const favorited = ref(false)
const favoriteLoading = ref(false)

// 能力图谱相关
const chartRef = ref<HTMLElement>()
let chartInstance: echarts.ECharts | null = null
const graphLoading = ref(false)
const graphEmpty = ref(false)

const fetchDetail = async () => {
  const id = Number(route.params.id)
  if (!id) return
  loading.value = true
  try {
    const res: any = await jobApi.detail(id)
    job.value = res.data || null
  } finally {
    loading.value = false
  }
}

const fetchResumes = async () => {
  try {
    const res: any = await resumeApi.list()
    resumes.value = (res.data?.items || []).filter((r: any) => r.parse_status === 2)
  } catch (e) {
    resumes.value = []
  }
}

// 检查当前职位是否已收藏 (拉取收藏列表比对)
const checkFavorite = async () => {
  if (!isSeeker.value) return
  const jobId = Number(route.params.id)
  if (!jobId) return
  try {
    const res: any = await jobApi.listFavorites()
    const items = res.data?.items || res.data || []
    favorited.value = items.some((it: any) => Number(it.job_id || it.id) === jobId)
  } catch (e) {
    // 静默失败
  }
}

// 切换收藏状态
const toggleFavorite = async () => {
  if (!job.value) return
  const jobId = job.value.id
  favoriteLoading.value = true
  try {
    if (favorited.value) {
      await jobApi.removeFavorite(jobId)
      favorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await jobApi.addFavorite(jobId)
      favorited.value = true
      ElMessage.success('收藏成功')
    }
  } catch (e) {
    // 拦截器已提示
  } finally {
    favoriteLoading.value = false
  }
}

// 初始化岗位能力图谱
const initChart = async () => {
  const jobId = Number(route.params.id)
  if (!jobId) return
  graphLoading.value = true
  graphEmpty.value = false
  try {
    const res: any = await graphApi.jobGraph(jobId)
    const data = res.data?.data || res.data || { nodes: [], edges: [] }
    const nodes: any[] = data.nodes || []
    const edges: any[] = data.edges || []
    if (!nodes.length) {
      graphEmpty.value = true
      return
    }
    await nextTick()
    if (!chartRef.value) return
    if (chartInstance) chartInstance.dispose()
    chartInstance = echarts.init(chartRef.value)

    // 转换节点: 中心职位节点蓝色大圆, 技能节点按 req_type 着色
    const colorMust = '#f56c6c' // 必须 - 红
    const colorOptional = '#e6a23c' // 优先 - 橙
    const colorJob = '#409eff' // 职位 - 蓝

    const chartNodes = nodes.map((n: any) => {
      const isJob = n.type === 'Job' || n.type === 'job' || n.labels?.includes('Job')
      const reqType = String(n.props?.req_type || n.req_type || '')
      let color = colorJob
      let symbolSize = 60
      if (!isJob) {
        symbolSize = 36
        if (reqType === '必须' || reqType === 'required' || reqType === '1') {
          color = colorMust
        } else if (reqType === '优先' || reqType === 'optional' || reqType === '2') {
          color = colorOptional
        } else {
          color = '#909399'
        }
      }
      // 中心节点(职位)显示岗位名称, 而非内部 ID
      const nodeName = isJob ? (job.value?.title || n.props?.name || n.name || String(n.id))
                              : (n.props?.name || n.name || n.title || String(n.id))
      return {
        id: String(n.id),
        name: nodeName,
        symbolSize,
        itemStyle: { color },
        category: isJob ? 0 : 1,
        label: { show: true, position: isJob ? 'inside' : 'right', fontSize: isJob ? 14 : 12 },
      }
    })

    const chartEdges = edges.map((e: any) => ({
      source: String(e.source),
      target: String(e.target),
      label: {
        show: true,
        formatter: e.label || e.type || 'REQUIRES',
        fontSize: 10,
        color: '#999',
      },
      lineStyle: { color: '#c0c4cc', curveness: 0.1 },
    }))

    chartInstance.setOption({
      tooltip: {
        formatter: (p: any) => {
          if (p.dataType === 'node') return p.data.name || p.data.id
          if (p.dataType === 'edge') return p.data.label?.formatter || 'REQUIRES'
          return ''
        },
      },
      legend: [
        {
          data: ['职位', '技能要求'],
          top: 0,
        },
      ],
      series: [
        {
          type: 'graph',
          layout: 'force',
          roam: true,
          draggable: true,
          label: { show: true },
          edgeLabel: { show: true },
          force: {
            repulsion: 300,
            edgeLength: [120, 200],
            gravity: 0.1,
          },
          categories: [
            { name: '职位' },
            { name: '技能要求' },
          ],
          data: chartNodes,
          links: chartEdges,
          lineStyle: { color: '#c0c4cc', width: 1, curveness: 0.1 },
          emphasis: {
            focus: 'adjacency',
            lineStyle: { width: 3 },
          },
        },
      ],
    })
  } catch (e) {
    console.error('图谱加载失败', e)
    graphEmpty.value = true
  } finally {
    graphLoading.value = false
  }
}

const handleResize = () => chartInstance?.resize()

const goRecommend = () => {
  // Recommend.vue 不读取 job_id, 直接跳转推荐页让用户选择简历匹配
  router.push({ path: '/seeker/recommend' })
}

const contactEmployer = () => {
  if (!job.value?.user_id) {
    ElMessage.warning('该职位未提供企业联系方式')
    return
  }
  router.push({ path: '/seeker/messages', query: { user_id: job.value.user_id } })
}

const openApplyDialog = async () => {
  applying.value = true
  try {
    if (resumes.value.length === 0) {
      await fetchResumes()
    }
    if (resumes.value.length === 0) {
      ElMessage.warning('您还没有已解析的简历, 请先上传简历')
      return
    }
    applyResumeId.value = resumes.value[0].id
    coverLetter.value = ''
    dialogVisible.value = true
  } finally {
    applying.value = false
  }
}

const submitApply = async () => {
  if (!applyResumeId.value || !job.value) return
  submitting.value = true
  try {
    await applicationApi.apply({
      resume_id: applyResumeId.value,
      job_id: job.value.id,
      cover_letter: coverLetter.value || undefined,
    })
    ElMessage.success('投递成功!')
    dialogVisible.value = false
  } catch (e: any) {
    // axios 拦截器已提示
  } finally {
    submitting.value = false
  }
}

const reqTypeText = (t?: string | number) => {
  const map: Record<string, string> = { required: '必备', optional: '加分', 1: '必备', 2: '加分', '必须': '必备', '优先': '加分' }
  return map[String(t)] || '要求'
}
const reqTagType = (t?: string | number): any => {
  const v = String(t)
  if (v === 'required' || v === '1' || v === '必须') return 'danger'
  if (v === 'optional' || v === '2' || v === '优先') return 'warning'
  return 'info'
}
const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(async () => {
  await fetchDetail()
  // 详情加载完成后并行检查收藏状态 + 初始化能力图谱
  checkFavorite()
  initChart()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance?.dispose()
  chartInstance = null
})
</script>

<style scoped>
.job-detail-page { max-width: 960px; margin: 0 auto; }
.page-header { margin-bottom: 16px; }
.header-title { font-weight: 600; }
.detail-card { border-radius: 12px; }
.job-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 12px;
}
.job-title { font-size: 22px; font-weight: 700; margin: 0; color: var(--text-primary); }
.job-salary { font-size: 18px; font-weight: 700; color: #ff6b35; margin-top: 6px; }
.job-company {
  display: flex; align-items: center; gap: 6px;
  color: var(--text-secondary); font-size: 14px; margin-bottom: 12px;
}
.job-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 8px; }
.job-desc pre {
  white-space: pre-wrap; word-break: break-word;
  font-family: inherit; line-height: 1.7; color: var(--text-primary);
  margin: 0;
}
.skill-reqs { display: flex; flex-wrap: wrap; gap: 8px; }
.req-tag .req-level, .req-tag .req-type { font-size: 12px; opacity: 0.85; }
.job-footer { color: var(--text-secondary); font-size: 13px; }
.muted { color: var(--text-secondary); }
.head-right { display: flex; gap: 8px; }
.apply-form { margin-top: 16px; }
.form-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
.empty-tip { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }
/* 能力图谱卡片 */
.graph-card { border-radius: 12px; margin-top: 16px; }
.graph-card .card-header {
  display: flex; align-items: center; justify-content: space-between;
  font-weight: 600;
}
.graph-wrap { position: relative; min-height: 400px; }
.job-graph-chart { width: 100%; height: 400px; }
</style>
