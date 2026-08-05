<!--
  企业投递管理 - 查看投递记录, 简历预览, 匹配分析, 批量操作
-->
<template>
  <div class="emp-app-page">
    <el-card shadow="never" class="filter-card">
      <div class="filter-bar">
        <span class="label">投递管理</span>
        <el-select
          v-model="jobId"
          placeholder="全部职位"
          clearable
          style="width: 280px"
          :loading="jobsLoading"
          @change="onJobChange"
        >
          <el-option
            v-for="j in jobs"
            :key="j.id"
            :label="`${j.title} - ${j.work_city || '不限'}`"
            :value="j.id"
          />
        </el-select>
        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          style="width: 130px"
        >
          <el-option label="已投递" :value="0" />
          <el-option label="已查看" :value="1" />
          <el-option label="面试邀请" :value="2" />
          <el-option label="不合适" :value="3" />
          <el-option label="已录用" :value="4" />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索候选人姓名"
          clearable
          style="width: 180px"
        />
        <el-select
          v-model="sortBy"
          placeholder="排序方式"
          style="width: 160px"
        >
          <el-option label="匹配度从高到低" value="match_desc" />
          <el-option label="投递时间最新" value="time_desc" />
          <el-option label="投递时间最早" value="time_asc" />
        </el-select>
        <el-tag v-if="!loading" type="info" size="small">{{ countText }}</el-tag>
        <el-button :icon="Refresh" :loading="loading" @click="fetchApplications">刷新</el-button>
        <el-button :icon="Download" plain @click="exportExcel">导出Excel</el-button>

        <!-- 批量操作区 -->
        <div v-if="selectedIds.length" class="batch-bar">
          <span class="batch-count">已选 {{ selectedIds.length }} 项</span>
          <el-select v-model="batchStatus" placeholder="批量改状态" size="small" style="width: 140px">
            <el-option :value="0" label="已投递" />
            <el-option :value="1" label="已查看" />
            <el-option :value="2" label="面试邀请" />
            <el-option :value="3" label="不合适" />
            <el-option :value="4" label="已录用" />
          </el-select>
          <el-button type="primary" size="small" @click="doBatchUpdate">确认</el-button>
          <el-button size="small" @click="selectedIds = []">取消</el-button>
        </div>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card">
      <SkeletonList v-if="loading && !list.length" :count="4" />
      <el-empty
        v-else-if="!loading && !list.length"
        description="暂无投递记录"
      />
      <el-table v-else :data="filteredList" row-key="id" stripe :empty-text="filterEmptyText" @selection-change="onSelectionChange">
        <el-table-column type="selection" width="42" />
        <el-table-column label="候选人" min-width="200">
          <template #default="{ row }">
            <div class="cand-name">{{ row.resume?.name || '匿名' }}</div>
            <div class="cand-sub">
              {{ row.resume?.education || '-' }} · {{ row.resume?.school || '学校未填' }} ·
              {{ row.resume?.work_years ?? 0 }} 年经验
            </div>
          </template>
        </el-table-column>
        <el-table-column v-if="!jobId" label="应聘职位" width="160">
          <template #default="{ row }">
            <span class="job-title-text">{{ row.job_title || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="匹配度" width="110" align="center">
          <template #default="{ row }">
            <div class="match-cell">
              <el-tag
                :type="matchTagType(row.match_analysis?.match_score)"
                effect="dark"
                size="small"
              >
                {{ row.match_analysis?.match_score ?? 0 }}%
              </el-tag>
              <div class="match-detail-hint">
                缺 {{ row.match_analysis?.missing?.length ?? 0 }} 项
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="投递时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="320" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="View" @click="showDetail(row)">查看简历</el-button>
            <el-select
              :model-value="row.status"
              size="small"
              style="width: 120px"
              @change="(v: any) => updateStatus(row.id, v)"
            >
              <el-option :value="0" label="已投递" />
              <el-option :value="1" label="已查看" />
              <el-option :value="2" label="面试邀请" />
              <el-option :value="3" label="不合适" />
              <el-option :value="4" label="已录用" />
            </el-select>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 简历预览抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="简历详情 & 匹配分析"
      direction="rtl"
      size="560px"
      :destroy-on-close="true"
    >
      <template v-if="currentDetail">
        <!-- 视图切换: 解析视图 / 原文件预览 (原文件预览可直接点击, 自动加载) -->
        <el-radio-group v-model="resumeViewMode" class="view-switch" size="small">
          <el-radio-button label="parsed">解析视图</el-radio-button>
          <el-radio-button label="file">原文件预览</el-radio-button>
        </el-radio-group>

        <!-- 原文件在线预览 -->
        <div v-if="resumeViewMode === 'file'" class="file-preview">
          <div v-if="fileLoading" v-loading="true" class="file-loading">正在加载原文件...</div>
          <iframe
            v-else-if="filePreviewUrl"
            :src="filePreviewUrl"
            class="file-iframe"
            frameborder="0"
          />
          <el-empty v-else description="原文件无法预览或加载失败" :image-size="80">
            <el-button type="primary" @click="loadFileUrl">重新加载</el-button>
          </el-empty>
        </div>

        <template v-else>
        <!-- 匹配度卡片 -->
        <div class="match-card">
          <div class="match-score-ring" :style="ringStyle">
            <span class="score-num">{{ currentDetail.match_analysis?.match_score ?? 0 }}</span>
            <span class="score-unit">%</span>
          </div>
          <div class="match-info">
            <div class="match-title">岗位匹配度</div>
            <div class="match-sub">
              要求 {{ currentDetail.match_analysis?.total_required ?? 0 }} 项技能 ·
              已匹配 {{ currentDetail.match_analysis?.matched?.length ?? 0 }} 项 ·
              缺失 {{ currentDetail.match_analysis?.missing?.length ?? 0 }} 项
            </div>
          </div>
        </div>

        <!-- 缺失技能警告 -->
        <div v-if="currentDetail.match_analysis?.missing?.length" class="missing-warn">
          <el-icon><WarningFilled /></el-icon>
          <span>能力缺失:</span>
          <el-tag
            v-for="s in currentDetail.match_analysis.missing"
            :key="s"
            type="danger"
            size="small"
            effect="light"
            class="missing-tag"
          >{{ s }}</el-tag>
        </div>

        <!-- 已匹配技能 -->
        <div v-if="currentDetail.match_analysis?.matched?.length" class="matched-section">
          <div class="section-title">已匹配技能</div>
          <div class="skills-row">
            <el-tag
              v-for="s in currentDetail.match_analysis.matched"
              :key="s"
              type="success"
              size="small"
              effect="light"
            >{{ s }}</el-tag>
          </div>
        </div>

        <el-divider>简历信息</el-divider>

        <!-- 基本信息 -->
        <div class="info-section">
          <div class="info-row">
            <span class="info-label">姓名</span>
            <span class="info-value">{{ currentDetail.resume?.name || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">性别</span>
            <span class="info-value">{{ currentDetail.resume?.gender || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">年龄</span>
            <span class="info-value">{{ currentDetail.resume?.age || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">学历</span>
            <span class="info-value">{{ currentDetail.resume?.education || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">学校</span>
            <span class="info-value">{{ currentDetail.resume?.school || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">专业</span>
            <span class="info-value">{{ currentDetail.resume?.major || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">工作年限</span>
            <span class="info-value">{{ currentDetail.resume?.work_years ?? '-' }} 年</span>
          </div>
          <div class="info-row">
            <span class="info-label">所在城市</span>
            <span class="info-value">{{ currentDetail.resume?.current_city || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">电话</span>
            <span class="info-value">{{ currentDetail.resume?.phone || '-' }}</span>
          </div>
          <div class="info-row">
            <span class="info-label">邮箱</span>
            <span class="info-value">{{ currentDetail.resume?.email || '-' }}</span>
          </div>
        </div>

        <!-- 自我评价 -->
        <div v-if="currentDetail.resume?.self_evaluation" class="eval-section">
          <div class="section-title">自我评价</div>
          <div class="eval-text">{{ currentDetail.resume.self_evaluation }}</div>
        </div>

        <!-- 工作经历 -->
        <div v-if="currentDetail.resume?.work_experience?.length" class="work-section">
          <div class="section-title">工作经历</div>
          <el-timeline>
            <el-timeline-item
              v-for="(w, i) in currentDetail.resume.work_experience"
              :key="i"
              :timestamp="w.duration || w.start_date || ''"
              placement="top"
              type="primary"
            >
              <div class="exp-card">
                <div class="exp-company">{{ w.company || '-' }} · {{ w.position || w.title || '-' }}</div>
                <div v-if="w.description" class="exp-desc">{{ w.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 项目经历 -->
        <div v-if="currentDetail.resume?.projects?.length" class="project-section">
          <div class="section-title">项目经历</div>
          <el-timeline>
            <el-timeline-item
              v-for="(p, i) in currentDetail.resume.projects"
              :key="i"
              :timestamp="p.duration || p.time || ''"
              placement="top"
              type="success"
            >
              <div class="exp-card">
                <div class="exp-company">{{ p.name || p.title || '-' }} · {{ p.role || '-' }}</div>
                <div v-if="p.description" class="exp-desc">{{ p.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>

        <!-- 技能列表 -->
        <div v-if="currentDetail.resume?.skills?.length" class="skills-section">
          <div class="section-title">技能列表</div>
          <div class="skills-row">
            <el-tag
              v-for="sk in currentDetail.resume.skills"
              :key="sk.skill_name"
              :type="levelTagType(sk.skill_level)"
              size="small"
            >
              {{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}
            </el-tag>
          </div>
        </div>

        <!-- 求职信 -->
        <div v-if="currentDetail.cover_letter" class="cover-section">
          <div class="section-title">求职信</div>
          <div class="cover-text">{{ currentDetail.cover_letter }}</div>
        </div>

        <!-- 操作按钮 -->
        <div class="contact-section">
          <el-button type="primary" :icon="ChatDotRound" plain @click="contactCandidate">
            联系候选人
          </el-button>
          <el-button type="warning" :icon="Document" plain @click="viewOriginalFile">
            查看原文件
          </el-button>
          <el-button
            type="success"
            :icon="MagicStick"
            plain
            :loading="generatingQuestions"
            @click="handleGenerateQuestions"
          >灵犀AI生成面试题</el-button>
        </div>
        </template>

        <!-- 灵犀AI面试题面板 -->
        <div v-if="questionResult" class="question-panel">
          <div class="question-panel-title">
            <el-icon><MagicStick /></el-icon>
            <span>灵犀AI面试题</span>
          </div>
          <!-- 候选人简评 -->
          <div v-if="questionResult.candidate_brief" class="candidate-brief">
            {{ questionResult.candidate_brief }}
          </div>
          <!-- 问题列表 -->
          <div
            v-for="(q, i) in questionResult.questions"
            :key="i"
            class="question-card"
            :style="{ borderLeftColor: categoryColorMap[q.category] || '#1677ff' }"
          >
            <div class="question-meta">
              <el-tag
                size="small"
                effect="light"
                :style="{
                  color: categoryColorMap[q.category] || '#1677ff',
                  borderColor: categoryColorMap[q.category] || '#1677ff',
                  backgroundColor: 'transparent',
                }"
              >{{ q.category }}</el-tag>
              <el-tag v-if="q.difficulty" size="small" :type="difficultyTagType(q.difficulty)" effect="light">
                {{ q.difficulty }}
              </el-tag>
            </div>
            <div class="question-content">{{ q.question }}</div>
            <div v-if="q.focus" class="question-focus">考察要点: {{ q.focus }}</div>
          </div>
          <!-- 复制全部 + 导出PDF 按钮 -->
          <div class="question-footer">
            <el-button type="primary" plain size="small" @click="copyAllQuestions">复制全部</el-button>
            <el-button type="success" plain size="small" :icon="Download" :loading="pdfExporting" @click="exportQuestionsPDF">导出PDF</el-button>
          </div>
          <!-- PDF导出进度条 -->
          <div v-if="pdfExporting" class="pdf-progress">
            <el-progress :percentage="pdfProgress" :stroke-width="6" :show-text="true" status="success" />
            <span class="pdf-progress-text">{{ pdfProgressText }}</span>
          </div>
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Document, MagicStick, Refresh, View, WarningFilled, Download } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { applicationApi } from '@/api/application'
import { resumeApi } from '@/api/resume'
import { interviewApi } from '@/api/interview'
import { exportToExcel } from '@/utils/exportExcel'
import SkeletonList from '@/components/SkeletonList.vue'

const route = useRoute()
const router = useRouter()
const jobs = ref<any[]>([])
const jobId = ref<number | null>(null)
const jobsLoading = ref(false)
const list = ref<any[]>([])
const loading = ref(false)
const total = ref(0)

// 二次过滤 (前端过滤, 数据已全量加载)
const statusFilter = ref<number | null>(null)
const keyword = ref('')
const sortBy = ref<string>('time_desc')

// 过滤后的列表
const filteredList = computed(() => {
  let result = list.value
  if (statusFilter.value !== null) {
    result = result.filter((r: any) => r.status === statusFilter.value)
  }
  const kw = keyword.value.trim().toLowerCase()
  if (kw) {
    result = result.filter((r: any) =>
      (r.resume?.name || '').toLowerCase().includes(kw)
    )
  }
  // 排序
  if (sortBy.value === 'match_desc') {
    result = [...result].sort((a: any, b: any) =>
      (b.match_analysis?.match_score ?? 0) - (a.match_analysis?.match_score ?? 0)
    )
  } else if (sortBy.value === 'time_desc') {
    result = [...result].sort((a: any, b: any) =>
      new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
  } else if (sortBy.value === 'time_asc') {
    result = [...result].sort((a: any, b: any) =>
      new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    )
  }
  return result
})

// 计数文案: 有过滤条件时展示 "已筛选 X / 共 Y 条"
const hasFilter = computed(() =>
  statusFilter.value !== null || keyword.value.trim() !== ''
)
const countText = computed(() =>
  hasFilter.value
    ? `已筛选 ${filteredList.value.length} / 共 ${total.value} 条`
    : `共 ${total.value} 条投递`
)
const filterEmptyText = computed(() =>
  hasFilter.value ? '没有符合条件的候选人, 试试调整筛选条件' : '暂无投递记录'
)

// 导出当前筛选结果到 Excel
const exportExcel = async () => {
  const rows = filteredList.value
  if (!rows.length) {
    ElMessage.warning('当前没有可导出的数据')
    return
  }
  try {
    await exportToExcel(
      [
        { title: '候选人', key: 'name', formatter: (r: any) => r.resume?.name || '匿名' },
        { title: '学历', key: 'edu', formatter: (r: any) => r.resume?.education || '-' },
        { title: '学校', key: 'school', formatter: (r: any) => r.resume?.school || '-' },
        { title: '工作年限', key: 'years', formatter: (r: any) => r.resume?.work_years ?? 0 },
        { title: '应聘职位', key: 'job', formatter: (r: any) => r.job_title || '-' },
        { title: '匹配度', key: 'match', formatter: (r: any) => `${r.match_analysis?.match_score ?? 0}%` },
        { title: '投递时间', key: 'time', formatter: (r: any) => formatDate(r.created_at) },
        { title: '状态', key: 'status', formatter: (r: any) => statusText(r.status) },
      ],
      rows,
      `投递记录-${new Date().toISOString().slice(0, 10)}`,
      '投递记录',
      '智聘云图 · 投递记录报表',
    )
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出失败, 请重试')
  }
}

// 批量操作
const selectedIds = ref<number[]>([])
const batchStatus = ref<number | null>(null)

// 简历预览抽屉
const drawerVisible = ref(false)
const currentDetail = ref<any>(null)
const resumeViewMode = ref<'parsed' | 'file'>('parsed')
const filePreviewUrl = ref('')
const fileLoading = ref(false)

// 灵犀AI生成面试题
const generatingQuestions = ref(false)
const questionResult = ref<any>(null)

// 面试问题类别颜色映射
const categoryColorMap: Record<string, string> = {
  '技术深度': '#1677ff',
  '项目追问': '#52c41a',
  '行为面试': '#faad14',
  '开放思考': '#722ed1',
}
// 难度标签类型映射
const difficultyTagType = (d?: string): any => {
  if (d === '简单') return 'info'
  if (d === '中等') return 'warning'
  if (d === '较难') return 'danger'
  return 'info'
}

// 匹配度环形样式
const ringStyle = computed(() => {
  const score = currentDetail.value?.match_analysis?.match_score ?? 0
  const color = score >= 80 ? '#52c41a' : score >= 60 ? '#1677ff' : score >= 40 ? '#faad14' : '#ff4d4f'
  const deg = (score / 100) * 360
  return {
    background: `conic-gradient(${color} ${deg}deg, rgba(0,0,0,0.06) ${deg}deg)`,
  }
})

const fetchJobs = async () => {
  jobsLoading.value = true
  try {
    const res: any = await jobApi.myList()
    jobs.value = res.data?.items || []
    if (route.query.job_id) {
      const id = Number(route.query.job_id)
      if (jobs.value.some(j => j.id === id)) {
        jobId.value = id
      }
    }
    // 默认加载全部投递
    fetchApplications()
  } catch (e: any) {
    ElMessage.error(e?.message || '职位列表加载失败')
  } finally {
    jobsLoading.value = false
  }
}

const fetchApplications = async () => {
  loading.value = true
  try {
    const res: any = await applicationApi.employerList(jobId.value || undefined)
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '加载投递记录失败')
    list.value = []
  } finally {
    loading.value = false
  }
}

// 切换职位筛选: 重置二次过滤条件后重新拉取
const onJobChange = () => {
  statusFilter.value = null
  keyword.value = ''
  fetchApplications()
}

const updateStatus = async (id: number, status: number) => {
  try {
    await applicationApi.updateStatus(id, status)
    ElMessage.success('状态已更新')
    fetchApplications()
  } catch (e: any) {
    ElMessage.error(e?.message || '状态更新失败')
  }
}

// 批量操作
const onSelectionChange = (rows: any[]) => {
  selectedIds.value = rows.map(r => r.id)
}
const doBatchUpdate = async () => {
  if (batchStatus.value === null) {
    ElMessage.warning('请选择要更改的状态')
    return
  }
  try {
    const res: any = await applicationApi.batchStatus(selectedIds.value, batchStatus.value)
    ElMessage.success(res.message || '批量更新成功')
    selectedIds.value = []
    batchStatus.value = null
    fetchApplications()
  } catch (e: any) {
    ElMessage.error(e?.message || '批量更新失败')
  }
}

// 简历预览
const showDetail = (row: any) => {
  currentDetail.value = row
  // 每次打开抽屉重置为解析视图, 清空上次的原文件预览, 避免残留上一候选人状态
  resumeViewMode.value = 'parsed'
  filePreviewUrl.value = ''
  drawerVisible.value = true
}

// 联系候选人
const contactCandidate = () => {
  const userId = currentDetail.value?.applicant_id
  if (!userId) {
    ElMessage.warning('无法获取候选人用户信息')
    return
  }
  drawerVisible.value = false
  router.push({ path: '/employer/messages', query: { user_id: userId } })
}

// 加载原文件 URL (供"原文件预览" tab 使用)
const loadFileUrl = async () => {
  const resumeId = currentDetail.value?.resume?.id
  if (!resumeId) {
    ElMessage.warning('无法获取简历信息')
    return
  }
  fileLoading.value = true
  try {
    const res: any = await resumeApi.getFile(resumeId)
    const url = res.data?.doc_url
    if (url) {
      filePreviewUrl.value = url
    } else {
      ElMessage.warning('简历文件路径不存在')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取文件失败')
  } finally {
    fileLoading.value = false
  }
}

// 查看原文件: 切换到原文件预览 tab (若未加载则自动加载)
const viewOriginalFile = () => {
  resumeViewMode.value = 'file'
}

// 切换到"原文件预览" tab 时, 若尚未加载文件则自动加载
watch(resumeViewMode, (mode) => {
  if (mode === 'file' && !filePreviewUrl.value && !fileLoading.value) {
    loadFileUrl()
  }
})

// 灵犀AI生成面试题
const handleGenerateQuestions = async () => {
  const applicationId = currentDetail.value?.id
  if (!applicationId) {
    ElMessage.warning('无法获取投递记录信息')
    return
  }
  generatingQuestions.value = true
  questionResult.value = null
  try {
    const res: any = await interviewApi.generateQuestions(applicationId)
    if (res.data) {
      questionResult.value = res.data
    } else {
      ElMessage.warning('未获取到面试问题')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '生成面试题失败')
  } finally {
    generatingQuestions.value = false
  }
}

// 复制全部面试题到剪贴板
const copyAllQuestions = async () => {
  if (!questionResult.value?.questions?.length) {
    ElMessage.warning('暂无可复制的问题')
    return
  }
  const text = questionResult.value.questions
    .map(
      (q: any, i: number) =>
        `${i + 1}. 【${q.category} | ${q.difficulty}】${q.question}\n考察要点: ${q.focus || '-'}`
    )
    .join('\n\n')
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('已复制全部面试题到剪贴板')
  } catch (e: any) {
    ElMessage.error('复制失败, 请手动选择文本复制')
  }
}

// 导出面试题 PDF (jspdf + html2canvas 逐块渲染, 智能分页不截断)
const pdfExporting = ref(false)
const pdfProgress = ref(0)
const pdfProgressText = ref('')

const exportQuestionsPDF = async () => {
  if (!questionResult.value?.questions?.length) {
    ElMessage.warning('暂无可导出的面试题')
    return
  }
  pdfExporting.value = true
  pdfProgress.value = 0
  pdfProgressText.value = '正在加载组件...'

  try {
    const jsPDF = (await import('jspdf')).default
    const html2canvas = (await import('html2canvas')).default

    pdfProgress.value = 10
    pdfProgressText.value = '正在渲染内容...'

    const r = questionResult.value
    const candidateName = currentDetail.value?.resume?.name || currentDetail.value?.applicant_name || '候选人'
    const jobTitle = currentDetail.value?.job_title || ''
    const dateStr = new Date().toLocaleDateString('zh-CN')

    // 离屏容器
    const offscreen = document.createElement('div')
    offscreen.style.cssText = 'position:fixed;left:-9999px;top:0;width:750px;background:#fff;'
    document.body.appendChild(offscreen)

    // 辅助: 把一段 HTML 渲染成 canvas → JPEG dataURL
    const renderBlock = async (innerHTML: string): Promise<{ data: string; h: number }> => {
      offscreen.innerHTML = innerHTML
      const canvas = await html2canvas(offscreen, { scale: 2, backgroundColor: '#fff', useCORS: true })
      return { data: canvas.toDataURL('image/jpeg', 0.95), h: canvas.height }
    }

    const A4_W = 210 // mm
    const A4_H = 297
    const MARGIN = 10 // 页边距 mm

    const pdf = new jsPDF('p', 'mm', 'a4')
    let cursorY = MARGIN // 当前页 Y 坐标 (mm)

    // 计算总块数用于进度
    const totalBlocks = 1 + (r.candidate_brief ? 1 : 0) + r.questions.length + 1 // 标题 + 简评 + 问题 + 页脚
    let doneBlocks = 0

    const updateProgress = (label: string) => {
      doneBlocks++
      pdfProgress.value = Math.round(10 + (doneBlocks / totalBlocks) * 85)
      pdfProgressText.value = label
    }

    // 1. 标题块
    const titleBlock = `
      <div style="padding:24px 28px;text-align:center;border-bottom:2px solid #1677ff;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
        <div style="font-size:22px;font-weight:700;color:#1677ff;">灵犀AI面试题</div>
        <div style="font-size:12px;color:#888;margin-top:6px;">候选人: ${candidateName}　|　职位: ${jobTitle}　|　生成日期: ${dateStr}</div>
      </div>
    `
    {
      const { data, h } = await renderBlock(titleBlock)
      const blockHmm = h / (2 * (750 / A4_W))
      pdf.addImage(data, 'JPEG', MARGIN, cursorY, A4_W - 2 * MARGIN, blockHmm)
      cursorY += blockHmm + 4
      updateProgress('标题渲染完成')
    }

    // 2. 候选人简评
    if (r.candidate_brief) {
      const briefBlock = `
        <div style="padding:28px;background:#f0f5ff;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
          <div style="font-size:13px;line-height:1.6;color:#555;">候选人简评: ${r.candidate_brief}</div>
        </div>
      `
      const { data, h } = await renderBlock(briefBlock)
      const blockHmm = h / (2 * (750 / A4_W))
      if (cursorY + blockHmm > A4_H - MARGIN) {
        pdf.addPage()
        cursorY = MARGIN
      }
      pdf.addImage(data, 'JPEG', MARGIN, cursorY, A4_W - 2 * MARGIN, blockHmm)
      cursorY += blockHmm + 4
      updateProgress('简评渲染完成')
    }

    // 3. 逐个问题渲染 (每题一个块, 不被分页截断)
    for (let i = 0; i < r.questions.length; i++) {
      const q = r.questions[i]
      const qBlock = `
        <div style="padding:28px;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
          <div style="padding:12px 14px;border-left:3px solid ${categoryColorMap[q.category] || '#1677ff'};background:#fafafa;border-radius:4px;">
            <div style="display:flex;gap:8px;margin-bottom:6px;">
              <span style="font-size:12px;font-weight:600;color:${categoryColorMap[q.category] || '#1677ff'};">${q.category}</span>
              <span style="font-size:12px;color:#999;">${q.difficulty || ''}</span>
            </div>
            <div style="font-size:14px;line-height:1.6;color:#333;">${i + 1}. ${q.question}</div>
            ${q.focus ? `<div style="font-size:12px;color:#888;margin-top:6px;line-height:1.5;">考察要点: ${q.focus}</div>` : ''}
          </div>
        </div>
      `
      const { data, h } = await renderBlock(qBlock)
      const blockHmm = h / (2 * (750 / A4_W))
      if (cursorY + blockHmm > A4_H - MARGIN) {
        pdf.addPage()
        cursorY = MARGIN
      }
      pdf.addImage(data, 'JPEG', MARGIN, cursorY, A4_W - 2 * MARGIN, blockHmm)
      cursorY += blockHmm + 2
      updateProgress(`正在渲染面试题 (${i + 1}/${r.questions.length})`)
    }

    // 4. 页脚
    const footerBlock = `
      <div style="padding:16px 28px;text-align:center;font-family:'Microsoft YaHei','PingFang SC',sans-serif;">
        <div style="font-size:11px;color:#ccc;">由智聘云图灵犀AI智能生成</div>
      </div>
    `
    {
      const { data, h } = await renderBlock(footerBlock)
      const blockHmm = h / (2 * (750 / A4_W))
      if (cursorY + blockHmm > A4_H - MARGIN) {
        pdf.addPage()
        cursorY = MARGIN
      }
      pdf.addImage(data, 'JPEG', MARGIN, cursorY, A4_W - 2 * MARGIN, blockHmm)
      updateProgress('页脚渲染完成')
    }

    pdfProgress.value = 98
    pdfProgressText.value = '正在生成PDF文件...'
    pdf.save(`面试题-${candidateName}-${dateStr}.pdf`)
    document.body.removeChild(offscreen)
    pdfProgress.value = 100
    pdfProgressText.value = '导出完成'
    ElMessage.success('PDF已下载')
    setTimeout(() => { pdfExporting.value = false }, 800)
  } catch (e) {
    ElMessage.error('导出失败, 请重试')
    pdfExporting.value = false
  }
}

const statusText = (s: number) =>
  ({ 0: '已投递', 1: '已查看', 2: '面试邀请', 3: '不合适', 4: '已录用' }[s] || '未知')
const statusTagType = (s: number): any =>
  ({ 0: 'info', 1: '', 2: 'success', 3: 'danger', 4: 'success' }[s] || 'info')
const matchTagType = (s?: number): any => {
  if (s == null) return 'info'
  if (s >= 80) return 'success'
  if (s >= 60) return ''
  if (s >= 40) return 'warning'
  return 'danger'
}
const levelTagType = (l?: string): any => {
  if (l === '精通') return 'danger'
  if (l === '熟练') return 'warning'
  if (l === '掌握') return 'success'
  return 'info'
}
const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(fetchJobs)
</script>

<style scoped>
.emp-app-page { display: flex; flex-direction: column; gap: 16px; }
.filter-card { border-radius: 12px; }
.filter-card :deep(.el-card__body) { padding: 14px 16px; }
.filter-bar { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.filter-bar .label { font-weight: 600; }
.list-card { border-radius: 12px; }
.cand-name { font-weight: 600; color: var(--text-primary); }
.cand-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.job-title-text { font-size: 13px; color: #1677ff; font-weight: 500; }
.match-cell { display: flex; flex-direction: column; align-items: center; gap: 2px; }
.match-detail-hint { font-size: 11px; color: #999; text-align: center; }

/* 批量操作 */
.batch-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: auto;
  padding: 4px 12px;
  background: #e6f4ff;
  border-radius: 6px;
}
.batch-count { font-size: 13px; color: #1677ff; font-weight: 600; }

/* 抽屉样式 */
.view-switch { margin-bottom: 16px; display: flex; justify-content: center; }
.file-preview { margin-bottom: 16px; }
.file-loading { height: 180px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 13px; }
.file-iframe { width: 100%; height: 560px; border: 1px solid #f0f0f0; border-radius: 8px; background: #fff; }
.match-card {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f5ff, #e6fffb);
  border-radius: 12px;
  margin-bottom: 16px;
}
.match-score-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
}
.match-score-ring::after {
  content: '';
  position: absolute;
  inset: 8px;
  border-radius: 50%;
  background: #fff;
}
.score-num { font-size: 24px; font-weight: 700; position: relative; z-index: 1; }
.score-unit { font-size: 12px; position: relative; z-index: 1; }
.match-title { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
.match-sub { font-size: 12px; color: #666; }

.missing-warn {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
  padding: 12px;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
  color: #cf1322;
}
.missing-tag { margin-left: 4px; }

.matched-section, .skills-section, .eval-section, .cover-section, .info-section, .work-section, .project-section {
  margin-bottom: 16px;
}
.section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid #1677ff;
}
.skills-row { display: flex; flex-wrap: wrap; gap: 6px; }
.exp-card { padding: 8px 12px; background: #f9fafc; border-radius: 6px; }
.exp-company { font-size: 13px; font-weight: 600; color: #333; }
.exp-desc { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.5; }

.info-row {
  display: flex;
  padding: 6px 0;
  border-bottom: 1px dashed #f0f0f0;
  font-size: 13px;
}
.info-label { width: 80px; color: #999; flex-shrink: 0; }
.info-value { color: #333; }

.eval-text, .cover-text {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  padding: 10px;
  background: #fafafa;
  border-radius: 6px;
}

.contact-section {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  text-align: center;
}

/* 灵犀AI面试题面板 */
.question-panel {
  margin-top: 16px;
  padding: 16px;
  background: #fff;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  animation: panel-fade-in 0.3s ease;
}
@keyframes panel-fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
.question-panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #52c41a;
  margin-bottom: 12px;
}
.candidate-brief {
  padding: 10px 12px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 6px;
  font-size: 13px;
  color: #389e0d;
  line-height: 1.6;
  margin-bottom: 12px;
}
.question-card {
  padding: 10px 12px;
  background: #fafafa;
  border-left: 3px solid #1677ff;
  border-radius: 6px;
  margin-bottom: 10px;
}
.question-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}
.question-content {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  line-height: 1.5;
}
.question-focus {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.5;
}
.question-footer {
  text-align: center;
  margin-top: 8px;
  display: flex;
  justify-content: center;
  gap: 10px;
}
.pdf-progress {
  margin-top: 12px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}
.pdf-progress-text {
  display: block;
  text-align: center;
  font-size: 12px;
  color: #888;
  margin-top: 6px;
}
</style>
