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

    <el-card shadow="never" class="list-card" v-loading="loading">
      <el-empty
        v-if="!loading && !list.length"
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
        </div>
      </template>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Document, Refresh, View, WarningFilled } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { applicationApi } from '@/api/application'
import { resumeApi } from '@/api/resume'

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

// 批量操作
const selectedIds = ref<number[]>([])
const batchStatus = ref<number | null>(null)

// 简历预览抽屉
const drawerVisible = ref(false)
const currentDetail = ref<any>(null)

// 匹配度环形样式
const ringStyle = computed(() => {
  const score = currentDetail.value?.match_analysis?.match_score ?? 0
  const color = score >= 80 ? '#52c41a' : score >= 60 ? '#1677ff' : score >= 40 ? '#faad14' : '#ff4d4f'
  const deg = (score / 100) * 360
  return {
    background: `conic-gradient(${color} ${deg}deg, rgba(0,0,0,0.06) ${deg}deg)`,
    color,
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

// 查看简历原文件
const viewOriginalFile = async () => {
  const resumeId = currentDetail.value?.resume?.id
  if (!resumeId) {
    ElMessage.warning('无法获取简历信息')
    return
  }
  try {
    const res: any = await resumeApi.getFile(resumeId)
    const url = res.data?.doc_url
    if (url) {
      window.open(url, '_blank')
    } else {
      ElMessage.warning('简历文件路径不存在')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取文件失败')
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
}
.score-num { font-size: 24px; font-weight: 700; }
.score-unit { font-size: 12px; }
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
</style>
