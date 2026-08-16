<!--
  候选人推荐 (企业) - 基于灵犀匹配引擎, 仅从已投递该职位的求职者中选取
-->
<template>
  <div class="candidates-page">
    <el-card shadow="never" class="filter-card">
      <span class="label">选择职位:</span>
      <el-select v-model="jobId" placeholder="请选择职位" style="width: 320px" @change="fetchRecommend">
        <el-option v-for="j in jobs" :key="j.id" :label="`${j.title} - ${j.work_city || '不限'}`" :value="j.id" />
      </el-select>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="fetchRecommend">智能匹配</el-button>
      <el-tag v-if="jobId" type="info" size="small" class="hint-tag">
        仅从已投递该职位的候选人中推荐
      </el-tag>
    </el-card>

    <div class="rec-list">
      <!-- 灵犀匹配中动画 -->
      <div v-if="loading" class="matching-animation">
        <div class="match-pulse">
          <div class="pulse-ring"></div>
          <div class="pulse-ring delay"></div>
          <el-icon :size="36" color="#1677ff"><MagicStick /></el-icon>
        </div>
        <div class="match-title">灵犀智能评估中</div>
        <div class="match-sub">召回→粗排→精排, 正在为企业挑选最佳候选人</div>
        <div class="match-steps">
          <div class="step-dot"><span class="dot active"></span><span>召回候选简历</span></div>
          <div class="step-line active"></div>
          <div class="step-dot"><span class="dot active"></span><span>多维特征粗排</span></div>
          <div class="step-line active"></div>
          <div class="step-dot"><span class="dot rotating"></span><span>灵犀大模型精排</span></div>
        </div>
        <div class="match-bar-wrap">
          <div class="match-bar"></div>
        </div>
        <div class="match-hint">正在调用灵犀大模型进行深度评估, 约 10-30 秒</div>
      </div>

      <template v-else>
      <el-card v-for="(item, idx) in list" :key="item.resume.id" shadow="hover" class="rec-card">
        <div class="rec-rank">#{{ idx + 1 }}</div>
        <div class="rec-body">
          <div class="rec-header">
            <div class="rec-name-row">
              <el-checkbox
                v-model="item._checked"
                :disabled="!item._checked && compareList.length >= 3"
                @change="onCompareChange"
                class="compare-cb"
              />
              <div>
                <div class="rec-name">{{ item.resume.name || '匿名候选人' }}</div>
                <div class="rec-meta">
                  {{ item.resume.education || '-' }} · {{ item.resume.school || '-' }} · {{ item.resume.major || '-' }} · {{ item.resume.work_years || 0 }} 年经验
                </div>
              </div>
            </div>
            <div class="rec-score">
              <div class="score-header">
                <span class="score-title">灵犀综合匹配度</span>
                <el-tooltip content="基于六维度加权计算: 技能(40%) + 经验(20%) + 学历(15%) + 城市(10%) + 薪资(10%) + 项目(5%), 由灵犀大模型精排得出" placement="top">
                  <el-icon class="score-info-icon"><InfoFilled /></el-icon>
                </el-tooltip>
              </div>
              <el-progress :percentage="item.total_score" :color="scoreColor(item.total_score)" :stroke-width="14" :format="(p: number) => p.toFixed(1)" />
            </div>
          </div>
          <div class="rec-skills">
            <el-tag v-for="sk in item.resume.skills?.slice(0, 8)" :key="sk.skill_name" size="small" :type="levelTag(sk.skill_level)">
              {{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}
            </el-tag>
          </div>
          <div class="rec-dims">
            <el-tag size="small">技能 {{ (item.skill_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="success">经验 {{ (item.exp_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="warning">学历 {{ (item.edu_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="info">城市 {{ (item.city_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="info">薪资 {{ (item.salary_score * 100).toFixed(0) }}</el-tag>
          </div>
          <div class="rec-reason">
            <el-icon><ChatLineRound /></el-icon>
            <span>{{ item.match_reason || '灵犀评估中...' }}</span>
          </div>
          <div class="rec-actions">
            <el-button size="small" type="primary" :icon="View" plain @click="showResumeDetail(item.resume)">查看简历</el-button>
            <el-tag v-if="item.application_status != null" :type="statusTagType(item.application_status)" size="small" class="app-status-tag">
              投递状态: {{ statusText(item.application_status) }}
            </el-tag>
            <el-select
              v-if="item.application_id != null"
              :model-value="item.application_status"
              size="small"
              placeholder="更新投递状态"
              style="width: 130px"
              @change="(v: any) => updateAppStatus(item, v)"
            >
              <el-option :value="0" label="已投递" />
              <el-option :value="1" label="已查看" />
              <el-option :value="2" label="面试邀请" />
              <el-option :value="3" label="不合适" />
              <el-option :value="4" label="已录用" />
            </el-select>
          </div>
        </div>
      </el-card>
      <EmptyState
        v-if="!list.length && hasFetched"
        icon="upload"
        title="该职位暂无投递"
        description="当前职位还没有候选人投递, 无法进行推荐匹配"
        action-text="返回职位列表"
        @action="$router.push('/employer/job/list')"
      />
      <EmptyState
        v-else-if="!list.length"
        icon="upload"
        title="请先选择职位"
        description="选择一个职位并点击匹配, 即可查看 AI 推荐的候选人"
        action-text="选择职位"
        @action="$router.back()"
      />
      </template>
    </div>

    <!-- 简历详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="候选人简历详情"
      direction="rtl"
      size="600px"
      :destroy-on-close="true"
    >
      <div v-loading="detailLoading" class="detail-wrap">
        <template v-if="currentDetail">
          <!-- 基本信息 -->
          <div class="section-title">基本信息</div>
          <div class="info-grid">
            <div class="info-row"><span class="info-label">姓名</span><span class="info-value">{{ currentDetail.name || '-' }}</span></div>
            <div class="info-row"><span class="info-label">性别</span><span class="info-value">{{ currentDetail.gender || '-' }}</span></div>
            <div class="info-row"><span class="info-label">年龄</span><span class="info-value">{{ currentDetail.age || '-' }}</span></div>
            <div class="info-row"><span class="info-label">学历</span><span class="info-value">{{ currentDetail.education || '-' }}</span></div>
            <div class="info-row"><span class="info-label">学校</span><span class="info-value">{{ currentDetail.school || '-' }}</span></div>
            <div class="info-row"><span class="info-label">专业</span><span class="info-value">{{ currentDetail.major || '-' }}</span></div>
            <div class="info-row"><span class="info-label">工作年限</span><span class="info-value">{{ currentDetail.work_years ?? '-' }} 年</span></div>
            <div class="info-row"><span class="info-label">所在城市</span><span class="info-value">{{ currentDetail.current_city || '-' }}</span></div>
          </div>

          <!-- 工作经历 -->
          <div v-if="currentDetail.work_experience?.length" class="section-title" style="margin-top:20px">工作经历</div>
          <el-timeline v-if="currentDetail.work_experience?.length">
            <el-timeline-item
              v-for="(w, i) in currentDetail.work_experience"
              :key="i"
              :timestamp="w.duration || w.start_date || ''"
              placement="top" type="primary"
            >
              <div class="exp-card">
                <div class="exp-company">{{ w.company || '-' }} · {{ w.position || w.title || '-' }}</div>
                <div v-if="w.description" class="exp-desc">{{ splitDesc(w.description) }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <!-- 项目经历 -->
          <div v-if="currentDetail.projects?.length" class="section-title" style="margin-top:20px">项目经历</div>
          <el-timeline v-if="currentDetail.projects?.length">
            <el-timeline-item
              v-for="(p, i) in currentDetail.projects"
              :key="i"
              :timestamp="p.duration || p.time || ''"
              placement="top" type="success"
            >
              <div class="exp-card">
                <div class="exp-company">{{ p.name || p.title || '-' }} · {{ p.role || '-' }}</div>
                <div v-if="p.description" class="exp-desc">{{ splitDesc(p.description) }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <!-- 技能列表 -->
          <div v-if="currentDetail.skills?.length" class="section-title skills-title-row" style="margin-top:20px">
            <span>技能列表</span>
            <el-radio-group v-model="skillViewMode" size="small">
              <el-radio-button value="list">列表</el-radio-button>
              <el-radio-button value="cloud">词云</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="currentDetail.skills?.length && skillViewMode === 'list'" class="skills-row">
            <el-tag v-for="sk in currentDetail.skills" :key="sk.id" :type="levelTag(sk.skill_level)" size="small">
              {{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}
            </el-tag>
          </div>
          <SkillWordCloud v-if="currentDetail.skills?.length && skillViewMode === 'cloud'" :skills="currentDetail.skills" />

          <!-- 查看原文件 -->
          <div class="file-section">
            <el-button type="primary" :icon="Document" plain @click="viewOriginalFile">
              查看原文件
            </el-button>
          </div>

          <!-- 投递状态操作 (简历详情抽屉内) -->
          <div v-if="currentAppId != null" class="status-section">
            <div class="section-title" style="margin-top:20px">投递状态管理</div>
            <div class="status-row">
              <el-tag :type="statusTagType(currentAppStatus)" size="default">
                当前状态: {{ statusText(currentAppStatus) }}
              </el-tag>
              <el-select
                :model-value="currentAppStatus"
                size="default"
                placeholder="更新投递状态"
                style="width: 160px"
                @change="(v: any) => updateDrawerStatus(v)"
              >
                <el-option :value="0" label="已投递" />
                <el-option :value="1" label="已查看" />
                <el-option :value="2" label="面试邀请" />
                <el-option :value="3" label="不合适" />
                <el-option :value="4" label="已录用" />
              </el-select>
            </div>
          </div>
        </template>
      </div>
    </el-drawer>

    <!-- 对比浮动按钮 -->
    <transition name="slide-up">
      <div v-if="compareList.length > 0" class="compare-bar">
        <span class="compare-info">已选 {{ compareList.length }}/3 位候选人</span>
        <el-button type="primary" :icon="DataAnalysis" @click="showCompareDialog = true" :disabled="compareList.length < 2">
          开始对比
        </el-button>
        <el-button text @click="clearCompare">清除选择</el-button>
      </div>
    </transition>

    <!-- 对比弹窗 -->
    <el-dialog v-model="showCompareDialog" title="候选人对比" width="800px" :close-on-click-modal="false">
      <el-table :data="compareRows" border stripe size="small">
        <el-table-column prop="label" label="对比维度" width="110" fixed />
        <el-table-column
          v-for="c in compareList"
          :key="c.resume.id"
          :label="c.resume.name || '匿名'"
          min-width="140"
          align="center"
        >
          <template #default="{ row }">
            <span v-if="row.key === 'total_score'" :class="{ 'best-val': row.best === c.resume.id }">
              <strong>{{ row.values[c.resume.id] }}</strong>
              <el-tag v-if="row.best === c.resume.id" size="small" type="success" effect="dark" style="margin-left:4px">最优</el-tag>
            </span>
            <span v-else-if="row.key === 'skills'" class="compare-skills">
              <el-tag v-for="sk in (row.values[c.resume.id] || []).slice(0, 4)" :key="sk" size="small" effect="plain">
                {{ sk }}
              </el-tag>
            </span>
            <span v-else :class="{ 'best-val': row.best === c.resume.id && row.best != null }">
              {{ row.values[c.resume.id] ?? '-' }}
              <el-tag v-if="row.best === c.resume.id && row.best != null" size="small" type="success" effect="dark" style="margin-left:4px">最优</el-tag>
            </span>
          </template>
        </el-table-column>
      </el-table>
      <template #footer>
        <el-button @click="showCompareDialog = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ChatLineRound, View, Document, MagicStick, InfoFilled, DataAnalysis } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { matchApi } from '@/api/match'
import { resumeApi } from '@/api/resume'
import { applicationApi } from '@/api/application'
import EmptyState from '@/components/EmptyState.vue'
import SkillWordCloud from '@/components/SkillWordCloud.vue'

// 技能展示模式: list=标签列表, cloud=词云
const skillViewMode = ref<'list' | 'cloud'>('list')

// 经历描述按序号 (1. 2. 3. ...) 自动换行展示
const splitDesc = (desc?: string) => {
  if (!desc) return ''
  return desc.replace(/(\d+[\.、])(?!\d)/g, '\n$1').replace(/^\n/, '').trim()
}

const route = useRoute()
const jobs = ref<any[]>([])
const jobId = ref<number | null>(null)
const list = ref<any[]>([])
const loading = ref(false)
const hasFetched = ref(false)

// 简历详情抽屉
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<any>(null)
const currentAppId = ref<number | null>(null)
const currentAppStatus = ref<number>(0)

// 候选人对比
const showCompareDialog = ref(false)

const compareList = computed(() => list.value.filter((it: any) => it._checked))

const onCompareChange = () => {
  // el-checkbox v-model 已自动更新 _checked
}

const clearCompare = () => {
  list.value.forEach((it: any) => { it._checked = false })
}

// 对比表格行数据
const compareRows = computed(() => {
  const items = compareList.value
  if (!items.length) return []

  const rows: any[] = []
  const getVal = (item: any, key: string) => {
    const r = item.resume
    switch (key) {
      case 'total_score': return item.total_score?.toFixed(1)
      case 'education': return r.education || '-'
      case 'work_years': return r.work_years != null ? `${r.work_years} 年` : '-'
      case 'school': return r.school || '-'
      case 'major': return r.major || '-'
      case 'skills': return (r.skills || []).map((s: any) => s.skill_name)
      case 'skill_score': return `${(item.skill_score * 100).toFixed(0)}`
      case 'exp_score': return `${(item.exp_score * 100).toFixed(0)}`
      case 'edu_score': return `${(item.edu_score * 100).toFixed(0)}`
      case 'current_city': return r.current_city || '-'
      case 'match_reason': return item.match_reason || '-'
      default: return '-'
    }
  }

  // 找最高值的候选人 id (用于高亮)
  const findBest = (key: string): number | null => {
    let bestId: number | null = null
    let bestVal = -Infinity
    for (const it of items) {
      const v = Number(getVal(it, key))
      if (!isNaN(v) && v > bestVal) {
        bestVal = v
        bestId = it.resume.id
      }
    }
    return bestId
  }

  const dims = [
    { label: '匹配得分', key: 'total_score' },
    { label: '学历', key: 'education' },
    { label: '学校', key: 'school' },
    { label: '专业', key: 'major' },
    { label: '工作年限', key: 'work_years' },
    { label: '所在城市', key: 'current_city' },
    { label: '技能覆盖', key: 'skills' },
    { label: '技能分', key: 'skill_score' },
    { label: '经验分', key: 'exp_score' },
    { label: '学历分', key: 'edu_score' },
    { label: '匹配理由', key: 'match_reason' },
  ]

  for (const dim of dims) {
    const valuesMap: Record<number, any> = {}
    for (const it of items) {
      valuesMap[it.resume.id] = getVal(it, dim.key)
    }
    let best: number | null = null
    if (['total_score', 'skill_score', 'exp_score', 'edu_score', 'work_years'].includes(dim.key)) {
      best = findBest(dim.key)
    }
    rows.push({ label: dim.label, key: dim.key, values: valuesMap, best })
  }

  return rows
})

const fetchJobs = async () => {
  try {
    const res: any = await jobApi.myList()
    jobs.value = res.data?.items || []
    if (route.query.job_id) {
      jobId.value = Number(route.query.job_id)
      fetchRecommend()
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '职位列表加载失败')
  }
}

const fetchRecommend = async () => {
  if (!jobId.value) return
  loading.value = true
  list.value = []
  try {
    const res: any = await matchApi.recommendResumes(jobId.value, 10)
    list.value = (res.data?.items || []).map((it: any) => ({ ...it, _checked: false }))
    hasFetched.value = true
  } catch (e: any) {
    ElMessage.error(e?.message || '候选人推荐失败, 请稍后重试')
  } finally {
    loading.value = false
  }
}

// 查看简历详情
const showResumeDetail = async (resume: any) => {
  drawerVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  // 记录投递信息 (从列表项中取)
  currentAppId.value = resume.application_id ?? null
  currentAppStatus.value = resume.application_status ?? 0
  try {
    const res: any = await resumeApi.detail(resume.id)
    currentDetail.value = res.data || null
  } catch (e: any) {
    ElMessage.error(e?.message || '加载简历详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 抽屉内更新投递状态
const updateDrawerStatus = async (status: number) => {
  if (currentAppId.value == null) return
  try {
    await applicationApi.updateStatus(currentAppId.value, status)
    currentAppStatus.value = status
    // 同步更新列表中的状态
    const item = list.value.find((it: any) => it.resume.id === currentDetail.value?.id)
    if (item) item.application_status = status
    ElMessage.success('投递状态已更新')
  } catch (e: any) {
    ElMessage.error(e?.message || '状态更新失败')
  }
}

// 查看原文件
const viewOriginalFile = async () => {
  if (!currentDetail.value?.id) return
  try {
    const res: any = await resumeApi.getFile(currentDetail.value.id)
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

const scoreColor = (s: number) => {
  if (s >= 80) return '#52c41a'
  if (s >= 60) return '#1677ff'
  if (s >= 40) return '#faad14'
  return '#ff4d4f'
}

const levelTag = (l?: string): any => {
  if (l === '精通') return 'danger'
  if (l === '熟练') return 'warning'
  if (l === '掌握') return 'success'
  return 'info'
}

// 投递状态文案与标签颜色 (0=已投递 1=已查看 2=面试邀请 3=不合适 4=已录用)
const statusText = (s: number) =>
  ({ 0: '已投递', 1: '已查看', 2: '面试邀请', 3: '不合适', 4: '已录用' }[s] || '未知')
const statusTagType = (s: number): any =>
  ({ 0: 'info', 1: '', 2: 'success', 3: 'danger', 4: 'success' }[s] || 'info')

// 更新某候选人的投递状态
const updateAppStatus = async (item: any, status: number) => {
  if (item.application_id == null) return
  try {
    await applicationApi.updateStatus(item.application_id, status)
    item.application_status = status
    ElMessage.success('投递状态已更新')
  } catch (e: any) {
    ElMessage.error(e?.message || '状态更新失败')
  }
}

onMounted(fetchJobs)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; align-items: center; gap: 12px; padding: 16px; }
.label { font-weight: 600; }
.hint-tag { margin-left: 8px; }
.rec-list { display: flex; flex-direction: column; gap: 12px; }

/* ===== 灵犀匹配动画 ===== */
.matching-animation {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 20px; background: #fff; border-radius: 10px;
}
.match-pulse {
  position: relative; width: 80px; height: 80px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 20px;
}
.pulse-ring {
  position: absolute; inset: 0; border-radius: 50%;
  border: 2px solid #1677ff; opacity: 0;
  animation: pulse 1.8s ease-out infinite;
}
.pulse-ring.delay { animation-delay: 0.6s; }
@keyframes pulse {
  0% { transform: scale(0.6); opacity: 0.8; }
  100% { transform: scale(1.6); opacity: 0; }
}
.match-title { font-size: 18px; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.match-sub { font-size: 13px; color: var(--text-secondary); margin-bottom: 28px; text-align: center; }
.match-steps { display: flex; align-items: center; gap: 4px; margin-bottom: 24px; }
.step-dot { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.step-dot span:last-child { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.dot { width: 10px; height: 10px; border-radius: 50%; background: #d9d9d9; }
.dot.active { background: #1677ff; box-shadow: 0 0 8px rgba(22,119,255,0.5); }
.dot.rotating { background: #1677ff; animation: dotPulse 1s ease-in-out infinite; }
@keyframes dotPulse {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.4); opacity: 0.6; }
}
.step-line { width: 40px; height: 2px; background: #d9d9d9; margin-bottom: 18px; }
.step-line.active { background: #1677ff; }
.match-bar-wrap { width: 280px; height: 4px; background: #f0f0f0; border-radius: 2px; overflow: hidden; margin-bottom: 12px; }
.match-bar {
  height: 100%; width: 40%; border-radius: 2px;
  background: linear-gradient(90deg, #1677ff, #4096ff);
  animation: barSlide 1.5s ease-in-out infinite;
}
@keyframes barSlide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}
.match-hint { font-size: 12px; color: var(--text-secondary); }
.rec-card { border-radius: 10px; }
.rec-card :deep(.el-card__body) { display: flex; gap: 16px; padding: 16px; }
.rec-rank {
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg, #52c41a, #95de64);
  color: #fff; font-weight: 700; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rec-body { flex: 1; min-width: 0; }
.rec-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px; gap: 16px; }
.rec-name { font-size: 16px; font-weight: 600; }
.rec-meta { color: var(--text-secondary); font-size: 13px; margin-top: 4px; }
.rec-score { width: 200px; flex-shrink: 0; }
.score-header { display: flex; align-items: center; gap: 4px; margin-bottom: 4px; }
.score-title { font-size: 12px; color: var(--text-secondary); font-weight: 500; }
.score-info-icon { font-size: 14px; color: #909399; cursor: pointer; }
.rec-skills { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.rec-dims { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.rec-reason {
  display: flex; gap: 6px; padding: 10px;
  background: #f5f7fa; border-radius: 6px;
  font-size: 13px; line-height: 1.5;
}
.rec-actions { margin-top: 8px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.app-status-tag { margin-left: 4px; }
.detail-wrap { padding: 0 4px; }
.section-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #1677ff;
}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.info-row { display: flex; padding: 6px 8px; border-bottom: 1px dashed #f0f0f0; font-size: 13px; }
.info-label { width: 64px; color: #999; flex-shrink: 0; }
.info-value { color: #333; }
.exp-card { padding: 8px 12px; background: #f9fafc; border-radius: 6px; }
.exp-company { font-size: 13px; font-weight: 600; color: #333; }
.exp-desc { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.6; white-space: pre-line; }
.skills-row { display: flex; flex-wrap: wrap; gap: 6px; }
.skills-title-row { display: flex; align-items: center; justify-content: space-between; }
.file-section { margin-top: 24px; text-align: center; padding-top: 16px; border-top: 1px solid #f0f0f0; }
.status-section { margin-top: 20px; }
.status-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* 候选人对比 */
.rec-name-row { display: flex; align-items: center; gap: 10px; }
.compare-cb { flex-shrink: 0; }

/* 对比浮动按钮 */
.compare-bar {
  position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%);
  display: flex; align-items: center; gap: 12px;
  background: #fff; box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  border-radius: 30px; padding: 10px 24px; z-index: 100;
}
.compare-info { font-size: 14px; color: #555; font-weight: 500; }
.slide-up-enter-active, .slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from, .slide-up-leave-to { opacity: 0; transform: translateX(-50%) translateY(20px); }

/* 对比弹窗 */
.best-val { color: #52c41a; font-weight: 700; }
.compare-skills { display: flex; flex-wrap: wrap; gap: 4px; justify-content: center; }
</style>
