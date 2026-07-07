<!--
  职位推荐 (求职者) - 基于 AI 匹配引擎 + 简历投递
-->
<template>
  <div class="recommend-page">
    <el-card shadow="never" class="filter-card">
      <span class="label">选择简历:</span>
      <el-select v-model="resumeId" placeholder="请选择简历" style="width: 280px" @change="fetchRecommend">
        <el-option v-for="r in resumes" :key="r.id" :label="`${r.name || '简历#' + r.id} - ${r.education || ''}`" :value="r.id" />
      </el-select>
      <el-button type="primary" :icon="Refresh" :loading="loading" @click="fetchRecommend">智能匹配</el-button>
      <el-button :icon="Document" @click="$router.push('/seeker/applications')">投递记录</el-button>
    </el-card>

    <div v-loading="loading" class="rec-list">
      <el-card v-for="(item, idx) in list" :key="item.job.id" shadow="hover" class="rec-card">
        <div class="rec-rank">#{{ idx + 1 }}</div>
        <div class="rec-body">
          <div class="rec-header">
            <div class="rec-title" @click="$router.push(`/seeker/jobs/${item.job.id}`)">{{ item.job.title }}</div>
            <div class="rec-score">
              <el-progress
                :percentage="item.total_score"
                :color="scoreColor(item.total_score)"
                :stroke-width="14"
                :format="(p: number) => p.toFixed(1)"
              />
            </div>
          </div>
          <div class="rec-company">{{ item.job.company || '匿名企业' }} · {{ item.job.work_city || '不限' }} · {{ formatSalary(item.job.salary_min, item.job.salary_max) }}</div>
          <div class="rec-dims">
            <el-tag size="small">技能 {{ (item.skill_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="success">经验 {{ (item.exp_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="warning">学历 {{ (item.edu_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="info">城市 {{ (item.city_score * 100).toFixed(0) }}</el-tag>
            <el-tag size="small" type="info">薪资 {{ (item.salary_score * 100).toFixed(0) }}</el-tag>
          </div>
          <div class="rec-reason">
            <el-icon><ChatLineRound /></el-icon>
            <span>{{ item.match_reason || 'AI 评估中...' }}</span>
          </div>
          <div class="rec-actions">
            <el-button
              type="primary"
              size="small"
              :icon="Position"
              :loading="applyingId === item.job.id"
              :disabled="appliedJobIds.has(item.job.id)"
              @click="applyJob(item.job)"
            >
              {{ appliedJobIds.has(item.job.id) ? '已投递' : '立即投递' }}
            </el-button>
            <el-button size="small" @click="$router.push(`/seeker/jobs/${item.job.id}`)">查看详情</el-button>
          </div>
        </div>
      </el-card>
      <el-empty v-if="!loading && !list.length" :description="emptyText" />
    </div>

    <!-- 投递对话框 -->
    <el-dialog v-model="dialogVisible" title="投递简历" width="520px">
      <el-descriptions :column="1" border v-if="currentJob">
        <el-descriptions-item label="职位">{{ currentJob.title }}</el-descriptions-item>
        <el-descriptions-item label="公司">{{ currentJob.company || '匿名企业' }}</el-descriptions-item>
        <el-descriptions-item label="薪资">{{ formatSalary(currentJob.salary_min, currentJob.salary_max) }}</el-descriptions-item>
        <el-descriptions-item label="简历">{{ selectedResumeLabel }}</el-descriptions-item>
      </el-descriptions>
      <el-input
        v-model="coverLetter"
        type="textarea"
        :rows="4"
        placeholder="求职信 (选填, 向 HR 展示你的诚意)"
        style="margin-top: 16px"
      />
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitApply">确认投递</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ChatLineRound, Position, Document } from '@element-plus/icons-vue'
import { resumeApi } from '@/api/resume'
import { matchApi } from '@/api/match'
import { applicationApi } from '@/api/application'
import { formatSalary } from '@/utils/format'

// 状态持久化: 切页(如查看职位详情)返回后恢复推荐结果, 避免重新选择简历匹配
const CACHE_KEY = 'recommend_state_cache'

interface CacheState {
  resumeId: number | null
  list: any[]
  timestamp: number
}

const route = useRoute()
const resumes = ref<any[]>([])
const resumeId = ref<number | null>(null)
const list = ref<any[]>([])
const loading = ref(false)
const emptyText = ref('请先选择简历并点击匹配')

// 投递相关
const dialogVisible = ref(false)
const currentJob = ref<any>(null)
const coverLetter = ref('')
const submitting = ref(false)
const applyingId = ref<number | null>(null)
const appliedJobIds = ref<Set<number>>(new Set())

const selectedResumeLabel = computed(() => {
  const r = resumes.value.find(x => x.id === resumeId.value)
  return r ? `${r.name || '简历#' + r.id} - ${r.education || ''}` : ''
})

// 保存状态到 sessionStorage
const saveCache = () => {
  if (resumeId.value && list.value.length) {
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify({
        resumeId: resumeId.value,
        list: list.value,
        timestamp: Date.now(),
      } as CacheState))
    } catch (e) {
      // 存储满时静默
    }
  }
}

// 从 sessionStorage 恢复状态
const restoreCache = (): boolean => {
  try {
    const cached = sessionStorage.getItem(CACHE_KEY)
    if (!cached) return false
    const state = JSON.parse(cached) as CacheState
    // 缓存 30 分钟内有效
    if (Date.now() - state.timestamp > 30 * 60 * 1000) {
      sessionStorage.removeItem(CACHE_KEY)
      return false
    }
    resumeId.value = state.resumeId
    list.value = state.list
    return true
  } catch (e) {
    return false
  }
}

const fetchResumes = async () => {
  try {
    const res: any = await resumeApi.list()
    resumes.value = (res.data?.items || []).filter((r: any) => r.parse_status === 2)
    // 优先级 1: 路由 query 携带 resume_id (从仪表盘跳转)
    if (route.query.resume_id) {
      resumeId.value = Number(route.query.resume_id)
      fetchRecommend()
      return
    }
    // 优先级 2: 从 sessionStorage 恢复上次匹配结果 (切页返回场景)
    if (restoreCache()) {
      emptyText.value = list.value.length ? '' : '暂无匹配职位, 试试其他简历'
      // 静默加载已投递集合, 不触发匹配
      fetchAppliedJobs()
    }
  } catch (e) {
    resumes.value = []
  }
}

const fetchRecommend = async () => {
  if (!resumeId.value) return
  loading.value = true
  list.value = []
  emptyText.value = 'AI 匹配中, 请稍候 (精排涉及大模型, 约 10-30 秒)...'
  try {
    const res: any = await matchApi.recommendJobs(resumeId.value, 10)
    list.value = res.data?.items || []
    if (!list.value.length) emptyText.value = '暂无匹配职位, 试试其他简历'
    // 加载已投递职位集合
    fetchAppliedJobs()
    // 持久化匹配结果
    saveCache()
  } catch (e: any) {
    emptyText.value = '匹配请求失败, 请稍后重试'
    ElMessage.error(e?.message || '匹配请求失败, 请稍后重试')
  } finally {
    loading.value = false
  }
}

const fetchAppliedJobs = async () => {
  try {
    const res: any = await applicationApi.myList({ page: 1, size: 100 })
    const items = res.data?.items || []
    appliedJobIds.value = new Set(items.map((a: any) => a.job_id))
  } catch (e) {
    // 忽略
  }
}

const applyJob = (job: any) => {
  if (!resumeId.value) {
    ElMessage.warning('请先选择简历')
    return
  }
  currentJob.value = job
  coverLetter.value = ''
  dialogVisible.value = true
}

const submitApply = async () => {
  if (!resumeId.value || !currentJob.value) return
  submitting.value = true
  try {
    await applicationApi.apply({
      resume_id: resumeId.value,
      job_id: currentJob.value.id,
      cover_letter: coverLetter.value || undefined,
    })
    ElMessage.success('投递成功!')
    appliedJobIds.value.add(currentJob.value.id)
    dialogVisible.value = false
    // 投递状态变更后更新缓存
    saveCache()
  } catch (e: any) {
    // axios 拦截器已提示
  } finally {
    submitting.value = false
  }
}

const scoreColor = (s: number) => {
  if (s >= 80) return '#52c41a'
  if (s >= 60) return '#1677ff'
  if (s >= 40) return '#faad14'
  return '#ff4d4f'
}

onMounted(fetchResumes)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px; }
.filter-card :deep(.el-card__body) { display: flex; align-items: center; gap: 12px; padding: 16px; width: 100%; }
.label { font-weight: 600; color: var(--text-primary); }
.rec-list { display: flex; flex-direction: column; gap: 12px; }
.rec-card { border-radius: 10px; }
.rec-card :deep(.el-card__body) { display: flex; gap: 16px; padding: 16px; }
.rec-rank {
  width: 40px; height: 40px; border-radius: 50%;
  background: linear-gradient(135deg, #1677ff, #4096ff);
  color: #fff; font-weight: 700; font-size: 16px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.rec-body { flex: 1; min-width: 0; }
.rec-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; gap: 16px; }
.rec-title { font-size: 16px; font-weight: 600; cursor: pointer; }
.rec-title:hover { color: #1677ff; }
.rec-score { width: 200px; }
.rec-company { color: var(--text-secondary); font-size: 13px; margin-bottom: 10px; }
.rec-dims { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.rec-reason {
  display: flex; gap: 6px; padding: 10px;
  background: #f5f7fa; border-radius: 6px;
  font-size: 13px; color: var(--text-primary); line-height: 1.5;
  margin-bottom: 10px;
}
.rec-actions { display: flex; gap: 8px; }
</style>
