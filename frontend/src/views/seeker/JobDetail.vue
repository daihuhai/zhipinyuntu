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
          <el-button :icon="Share" @click="openShareCard">分享职位</el-button>
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

    <!-- 企业评价 + 相似职位推荐 (tab 切换) -->
    <el-card v-if="job" shadow="never" class="info-tabs-card">
      <el-tabs v-model="activeTab" class="info-tabs">
        <!-- 企业评价 -->
        <el-tab-pane label="企业评价" name="review">
          <div v-loading="reviewLoading" class="review-wrap">
            <template v-if="reviewData && reviewData.total > 0">
              <div class="review-summary">
                <div class="review-overall">
                  <div class="overall-num">{{ reviewData.overall }}</div>
                  <div class="overall-label">综合评分</div>
                  <el-rate :model-value="Math.round(reviewData.overall)" disabled />
                </div>
                <div class="review-dims">
                  <div class="dim-item">
                    <span class="dim-label">面试体验</span>
                    <el-rate :model-value="reviewData.avg_interview" disabled allow-half />
                    <span class="dim-score">{{ reviewData.avg_interview }}</span>
                  </div>
                  <div class="dim-item">
                    <span class="dim-label">HR 响应速度</span>
                    <el-rate :model-value="reviewData.avg_hr" disabled allow-half />
                    <span class="dim-score">{{ reviewData.avg_hr }}</span>
                  </div>
                  <div class="dim-item">
                    <span class="dim-label">描述准确度</span>
                    <el-rate :model-value="reviewData.avg_accuracy" disabled allow-half />
                    <span class="dim-score">{{ reviewData.avg_accuracy }}</span>
                  </div>
                </div>
              </div>
              <el-divider />
              <div class="review-list">
                <div v-for="(r, i) in reviewData.items" :key="i" class="review-item">
                  <div class="review-item-head">
                    <span class="review-anon">匿名求职者</span>
                    <span class="review-job-tag">{{ r.job_title || '职位' }}</span>
                    <span class="review-time">{{ formatDate(r.created_at) }}</span>
                  </div>
                  <div class="review-item-scores">
                    <el-rate :model-value="r.interview_score" disabled size="small" />
                    <span class="review-meta">HR响应 {{ r.hr_score }} · 描述准确 {{ r.accuracy_score }}</span>
                  </div>
                  <div v-if="r.comment" class="review-comment">{{ r.comment }}</div>
                </div>
              </div>
            </template>
            <el-empty v-else-if="!reviewLoading" description="该企业暂无评价, 期待第一位求职者反馈" :image-size="80" />
          </div>
        </el-tab-pane>

        <!-- 相似职位推荐 -->
        <el-tab-pane label="相似职位推荐" name="similar">
          <div v-if="similarJobs.length" class="similar-grid">
            <div v-for="s in similarJobs" :key="s.id" class="similar-item" @click="$router.push(`/seeker/jobs/${s.id}`)">
              <div class="similar-item-top">
                <span class="similar-title">{{ s.title }}</span>
                <span class="similar-salary">{{ formatSalary(s.salary_min, s.salary_max) }}</span>
              </div>
              <div class="similar-company">{{ s.company || '匿名企业' }} · {{ s.work_city || '不限' }}</div>
              <div class="similar-meta">
                <el-tag v-if="s.experience_required" size="small" type="info">{{ s.experience_required }}</el-tag>
                <el-tag v-if="s.education_required" size="small" type="info">{{ s.education_required }}</el-tag>
              </div>
              <el-button link type="primary" class="similar-go">查看详情 →</el-button>
            </div>
          </div>
          <el-empty v-else description="暂无相似职位推荐" :image-size="80" />
        </el-tab-pane>
      </el-tabs>
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

    <!-- 分享卡片对话框 -->
    <el-dialog v-model="shareVisible" title="职位分享卡片" width="440px" class="share-dialog">
      <div class="share-card" ref="shareCardRef">
        <div class="share-card-header">
          <div class="share-brand">
            <img src="@/assets/logo.png" class="share-logo" alt="智聘云图" loading="lazy" />
            <span class="share-brand-name">智聘云图</span>
          </div>
          <div class="share-tag">热门职位</div>
        </div>
        <div class="share-card-body">
          <h3 class="share-job-title">{{ job?.title }}</h3>
          <div class="share-salary">{{ formatSalary(job?.salary_min, job?.salary_max) }}</div>
          <div class="share-info-row">
            <el-icon><OfficeBuilding /></el-icon>
            <span>{{ job?.company || '匿名企业' }}</span>
          </div>
          <div class="share-info-row">
            <el-icon><Location /></el-icon>
            <span>{{ job?.work_city || '城市不限' }}</span>
            <el-divider direction="vertical" />
            <span>{{ job?.experience_required || '经验不限' }}</span>
            <el-divider direction="vertical" />
            <span>{{ job?.education_required || '学历不限' }}</span>
          </div>
          <div class="share-skills" v-if="job?.requirements?.length">
            <span v-for="r in job.requirements.slice(0, 5)" :key="r.id" class="share-skill-tag">{{ r.skill_name }}</span>
          </div>
        </div>
        <div class="share-card-footer">
          <div class="share-qr-area">
            <canvas ref="qrCanvasRef" class="share-qr"></canvas>
          </div>
          <div class="share-cta">
            <div class="share-cta-title">扫码查看职位详情</div>
            <div class="share-cta-sub">智聘云图 · 智能人岗匹配平台</div>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="shareVisible = false">关闭</el-button>
        <el-button type="primary" :loading="shareLoading" @click="downloadShareCard">保存图片</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { Position, OfficeBuilding, ChatDotRound, Star, StarFilled, Share, Location } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { graphApi } from '@/api/graph'
import { resumeApi } from '@/api/resume'
import { applicationApi } from '@/api/application'
import { reviewApi } from '@/api/review'
import { useUserStore } from '@/stores/user'
import { formatSalary } from '@/utils/format'
import QRCode from 'qrcode'

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

// ===== 企业评价 =====
const reviewData = ref<any>(null)
const reviewLoading = ref(false)

const fetchReviews = async () => {
  const companyId = job.value?.user_id
  if (!companyId) return
  reviewLoading.value = true
  try {
    const res: any = await reviewApi.companyList(companyId, { page: 1, size: 20 })
    reviewData.value = res.data || null
  } catch (e) {
    reviewData.value = null
  } finally {
    reviewLoading.value = false
  }
}

// ===== 企业评价 + 相似职位推荐 tab =====
const activeTab = ref('review')

// ===== 相似职位推荐 =====
const similarJobs = ref<any[]>([])

const fetchSimilar = async () => {
  const id = Number(route.params.id)
  if (!id) return
  try {
    const res: any = await jobApi.similar(id, 6)
    similarJobs.value = res.data?.items || []
  } catch {
    similarJobs.value = []
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

    // 转换节点: 中心职位节点蓝色大圆, 技能节点统一橙色 (与图例一致)
    const colorJob = '#409eff' // 职位 - 蓝
    const colorSkill = '#e6a23c' // 技能要求 - 橙

    const chartNodes = nodes.map((n: any) => {
      const isJob = n.type === 'Job' || n.type === 'job' || n.labels?.includes('Job')
      const color = isJob ? colorJob : colorSkill
      const symbolSize = isJob ? 60 : 36
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
            { name: '职位', itemStyle: { color: '#409eff' } },
            { name: '技能要求', itemStyle: { color: '#e6a23c' } },
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

// ===== 分享卡片 =====
const shareVisible = ref(false)
const shareLoading = ref(false)
const shareCardRef = ref<HTMLElement>()
const qrCanvasRef = ref<HTMLCanvasElement>()

const openShareCard = async () => {
  shareVisible.value = true
  await nextTick()
  // 生成真实二维码 (使用 qrcode 库)
  drawQRCode()
}

const drawQRCode = async () => {
  const canvas = qrCanvasRef.value
  if (!canvas) return
  // 二维码内容: 职位详情页 URL
  const shareUrl = `${window.location.origin}/seeker/jobs/${job.value?.id || ''}`
  try {
    await QRCode.toCanvas(canvas, shareUrl, {
      width: 100,
      margin: 1,
      color: { dark: '#1a1a2e', light: '#ffffff' },
      errorCorrectionLevel: 'M',
    })
  } catch {
    // 生成失败时静默处理
  }
}

const downloadShareCard = async () => {
  if (!shareCardRef.value) return
  shareLoading.value = true
  try {
    const html2canvas = (await import('html2canvas')).default
    const canvas = await html2canvas(shareCardRef.value, {
      backgroundColor: null,
      scale: 2,
      useCORS: true,
    })
    const link = document.createElement('a')
    link.download = `职位卡片-${job.value?.title || 'unknown'}.png`
    link.href = canvas.toDataURL('image/png')
    link.click()
    ElMessage.success('卡片已保存到本地')
  } catch (e) {
    ElMessage.error('保存失败, 请重试')
  } finally {
    shareLoading.value = false
  }
}

// ===== 浏览历史 (localStorage) =====
const recordBrowseHistory = () => {
  if (!job.value) return
  const key = 'browse_history'
  let history: any[] = []
  try {
    history = JSON.parse(localStorage.getItem(key) || '[]')
  } catch { history = [] }
  // 去重: 移除相同 job_id
  history = history.filter(h => h.job_id !== job.value.id)
  // 头部插入
  history.unshift({
    job_id: job.value.id,
    title: job.value.title,
    company: job.value.company || '匿名企业',
    salary_min: job.value.salary_min,
    salary_max: job.value.salary_max,
    work_city: job.value.work_city || '',
    education_required: job.value.education_required || '',
    experience_required: job.value.experience_required || '',
    browsed_at: new Date().toISOString(),
  })
  // 只保留最近 20 条
  history = history.slice(0, 20)
  localStorage.setItem(key, JSON.stringify(history))
}

onMounted(async () => {
  await fetchDetail()
  // 详情加载完成后并行检查收藏状态 + 初始化能力图谱 + 记录浏览历史 + 加载企业评价 + 加载相似职位
  checkFavorite()
  initChart()
  recordBrowseHistory()
  fetchReviews()
  fetchSimilar()
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

/* 企业评价 + 相似职位 tab 卡片 */
.info-tabs-card { border-radius: 12px; margin-top: 16px; }
.info-tabs :deep(.el-tabs__header) { margin: 0 0 16px; }
.info-tabs :deep(.el-tabs__nav-wrap::after) { height: 1px; }
.review-wrap { min-height: 120px; }
.review-summary { display: flex; align-items: center; gap: 40px; }
.review-overall { text-align: center; }
.overall-num { font-size: 42px; font-weight: 700; color: #1677ff; line-height: 1; }
.overall-label { font-size: 13px; color: var(--text-secondary); margin: 6px 0 4px; }
.review-dims { flex: 1; display: flex; flex-direction: column; gap: 10px; }
.dim-item { display: flex; align-items: center; gap: 10px; }
.dim-label { width: 84px; font-size: 13px; color: var(--text-secondary); }
.dim-score { font-size: 13px; font-weight: 600; color: #1677ff; min-width: 24px; }
.review-list { display: flex; flex-direction: column; gap: 14px; }
.review-item { border: 1px solid #f0f0f0; border-radius: 8px; padding: 12px 14px; background: #fafbfc; }
.review-item-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.review-anon { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.review-job-tag { font-size: 12px; color: #1677ff; background: #e6f4ff; padding: 1px 8px; border-radius: 4px; }
.review-time { margin-left: auto; font-size: 12px; color: #bbb; }
.review-item-scores { display: flex; align-items: center; gap: 10px; }
.review-meta { font-size: 12px; color: #999; }
.review-comment { margin-top: 8px; font-size: 13px; color: var(--text-primary); line-height: 1.6; }

/* 相似职位推荐 */
.similar-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.similar-item {
  border: 1px solid #f0f0f0; border-radius: 10px; padding: 14px;
  cursor: pointer; transition: all 0.2s; background: #fff;
}
.similar-item:hover { border-color: #1677ff; box-shadow: 0 4px 16px rgba(22, 119, 255, 0.12); transform: translateY(-2px); }
.similar-item-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.similar-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
.similar-salary { font-size: 15px; font-weight: 700; color: #ff6b35; }
.similar-company { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; }
.similar-meta { display: flex; gap: 6px; margin-bottom: 8px; }
.similar-go { align-self: flex-start; }

/* 分享卡片 */
.share-card {
  width: 380px;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(145deg, #1677ff 0%, #0958d9 100%);
  box-shadow: 0 8px 32px rgba(22, 119, 255, 0.3);
}
.share-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
}
.share-brand {
  display: flex;
  align-items: center;
  gap: 8px;
}
.share-logo {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  object-fit: contain;
}
.share-brand-name {
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 1px;
}
.share-tag {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 10px;
  backdrop-filter: blur(4px);
}
.share-card-body {
  background: #fff;
  margin: 0 12px;
  border-radius: 12px;
  padding: 20px;
}
.share-job-title {
  font-size: 20px;
  font-weight: 700;
  color: #1a1a2e;
  margin: 0 0 8px;
}
.share-salary {
  font-size: 22px;
  font-weight: 800;
  color: #ff6b35;
  margin-bottom: 14px;
}
.share-info-row {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}
.share-info-row .el-icon { color: #999; font-size: 14px; }
.share-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
}
.share-skill-tag {
  background: #e6f4ff;
  color: #1677ff;
  font-size: 11px;
  padding: 3px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.share-card-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
}
.share-qr-area {
  background: #fff;
  padding: 4px;
  border-radius: 8px;
}
.share-qr {
  display: block;
  width: 100px;
  height: 100px;
}
.share-cta-title {
  color: #fff;
  font-size: 14px;
  font-weight: 600;
}
.share-cta-sub {
  color: rgba(255, 255, 255, 0.7);
  font-size: 11px;
  margin-top: 4px;
}
</style>
