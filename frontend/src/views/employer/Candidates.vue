<!--
  候选人推荐 (企业) - 基于 AI 匹配引擎, 仅从已投递该职位的求职者中选取
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

    <div v-loading="loading" class="rec-list" element-loading-text="AI 正在评估候选人...">
      <el-card v-for="(item, idx) in list" :key="item.resume.id" shadow="hover" class="rec-card">
        <div class="rec-rank">#{{ idx + 1 }}</div>
        <div class="rec-body">
          <div class="rec-header">
            <div>
              <div class="rec-name">{{ item.resume.name || '匿名候选人' }}</div>
              <div class="rec-meta">
                {{ item.resume.education || '-' }} · {{ item.resume.school || '-' }} · {{ item.resume.major || '-' }} · {{ item.resume.work_years || 0 }} 年经验
              </div>
            </div>
            <div class="rec-score">
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
            <span>{{ item.match_reason || 'AI 评估中...' }}</span>
          </div>
        </div>
      </el-card>
      <el-empty v-if="!loading && !list.length && hasFetched" description="该职位暂无投递, 无法推荐候选人">
        <el-button type="primary" @click="$router.push('/employer/job/list')">返回职位列表</el-button>
      </el-empty>
      <el-empty v-if="!loading && !list.length && !hasFetched" description="请先选择职位并点击匹配" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, ChatLineRound } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { matchApi } from '@/api/match'

const route = useRoute()
const jobs = ref<any[]>([])
const jobId = ref<number | null>(null)
const list = ref<any[]>([])
const loading = ref(false)
const hasFetched = ref(false)

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
    list.value = res.data?.items || []
    hasFetched.value = true
  } catch (e: any) {
    ElMessage.error(e?.message || '候选人推荐失败, 请稍后重试')
  } finally {
    loading.value = false
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

onMounted(fetchJobs)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; align-items: center; gap: 12px; padding: 16px; }
.label { font-weight: 600; }
.hint-tag { margin-left: 8px; }
.rec-list { display: flex; flex-direction: column; gap: 12px; }
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
.rec-skills { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.rec-dims { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.rec-reason {
  display: flex; gap: 6px; padding: 10px;
  background: #f5f7fa; border-radius: 6px;
  font-size: 13px; line-height: 1.5;
}
</style>
