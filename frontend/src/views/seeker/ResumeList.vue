<!--
  我的简历列表 - 含详情抽屉 (工作经历/项目经历) + 查看原文件
-->
<template>
  <div class="resume-list">
    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>我的简历</span>
          <el-button type="primary" :icon="Plus" @click="$router.push('/seeker/resume/upload')">上传新简历</el-button>
        </div>
      </template>
      <SkeletonTable v-if="loading && !list.length" :count="6" :cols="4" />
      <el-table v-if="!(loading && !list.length)" :data="list" stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column prop="school" label="学校" width="160" />
        <el-table-column prop="major" label="专业" width="140" />
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
        <el-table-column label="操作" width="380" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">查看详情</el-button>
            <el-button link type="primary" @click="previewFile(row)">预览</el-button>
            <el-button link type="success" @click="$router.push(`/seeker/resume/${row.id}/edit`)">编辑</el-button>
            <el-button link type="info" @click="$router.push(`/seeker/graph?resume_id=${row.id}`)">能力图谱</el-button>
            <el-button link type="warning" @click="$router.push(`/seeker/recommend?resume_id=${row.id}`)">推荐职位</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 简历详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="简历详情"
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
            <div class="info-row"><span class="info-label">电话</span><span class="info-value">{{ currentDetail.phone || '-' }}</span></div>
            <div class="info-row"><span class="info-label">邮箱</span><span class="info-value">{{ currentDetail.email || '-' }}</span></div>
          </div>

          <!-- 竞争力分析 (紧跟基本信息, 突出展示) -->
          <div class="compete-card">
            <div class="compete-card-header">
              <span class="compete-card-title">
                <el-icon><TrendCharts /></el-icon>
                竞争力分析
              </span>
              <el-button
                type="primary"
                size="small"
                :icon="TrendCharts"
                :loading="competeLoading"
                @click="handleCompete"
              >
                {{ competeLoading ? '分析中...' : '开始分析' }}
              </el-button>
            </div>

            <div v-if="competeResult" class="compete-result">
              <!-- 雷达图 + 概要 -->
              <div class="compete-top">
                <div ref="radarChartRef" class="radar-chart"></div>
                <div class="compete-summary">
                  <div v-if="competeResult.peer_count" class="peer-badge">
                    <el-tag type="info" size="small" effect="plain">参考样本: {{ competeResult.peer_count }} 位同岗位候选人</el-tag>
                  </div>
                  <div class="dim-list">
                    <div v-for="dim in competeResult.dimensions" :key="dim.name" class="dim-item">
                      <div class="dim-header">
                        <span class="dim-name">{{ dim.name }}</span>
                        <span class="dim-pct" :style="{ color: pctColor(dim.percentile) }">
                          {{ dim.percentile > 0 ? 'TOP ' + (100 - dim.percentile).toFixed(0) + '%' : '暂无' }}
                        </span>
                      </div>
                      <el-progress
                        :percentage="dim.percentile"
                        :color="pctColor(dim.percentile)"
                        :stroke-width="6"
                        :show-text="false"
                      />
                      <div class="dim-desc">{{ dim.desc }}</div>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 提升建议 -->
              <div v-if="competeResult.suggestions?.length" class="suggestion-list">
                <div class="suggestion-title">
                  <el-icon><Promotion /></el-icon>
                  提升建议
                </div>
                <div v-for="(s, i) in competeResult.suggestions" :key="i" class="suggestion-card">
                  <span class="suggestion-dot">{{ Number(i) + 1 }}</span>
                  <span>{{ s }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 工作经历 -->
          <div v-if="currentDetail.work_experience?.length" class="section-title" style="margin-top:20px">工作经历</div>
          <el-timeline v-if="currentDetail.work_experience?.length">
            <el-timeline-item
              v-for="(w, i) in currentDetail.work_experience"
              :key="i"
              :timestamp="w.duration || w.start_date || ''"
              placement="top"
              type="primary"
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
              placement="top"
              type="success"
            >
              <div class="exp-card">
                <div class="exp-company">{{ p.name || p.title || '-' }} · {{ p.role || '-' }}</div>
                <div v-if="p.description" class="exp-desc">{{ splitDesc(p.description) }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <!-- 自我评价 -->
          <div v-if="currentDetail.self_evaluation" class="section-title" style="margin-top:20px">自我评价</div>
          <div v-if="currentDetail.self_evaluation" class="eval-text">{{ currentDetail.self_evaluation }}</div>

          <!-- 技能列表 -->
          <div v-if="currentDetail.skills?.length" class="section-title skills-title-row" style="margin-top:20px">
            <span>技能列表</span>
            <el-radio-group v-model="skillViewMode" size="small">
              <el-radio-button value="list">列表</el-radio-button>
              <el-radio-button value="cloud">词云</el-radio-button>
            </el-radio-group>
          </div>
          <div v-if="currentDetail.skills?.length && skillViewMode === 'list'" class="skills-row">
            <el-tag
              v-for="sk in currentDetail.skills"
              :key="sk.id"
              :type="levelTagType(sk.skill_level)"
              size="small"
            >{{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}</el-tag>
          </div>
          <SkillWordCloud v-if="currentDetail.skills?.length && skillViewMode === 'cloud'" :skills="currentDetail.skills" />

          <!-- 查看原文件 -->
          <div class="file-section">
            <el-button type="primary" :icon="Document" plain @click="viewOriginalFile">
              查看原文件 (PDF/DOC)
            </el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, TrendCharts, Promotion } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { resumeApi } from '@/api/resume'
import SkeletonTable from '@/components/SkeletonTable.vue'
import SkillWordCloud from '@/components/SkillWordCloud.vue'

// 技能展示模式: list=标签列表, cloud=词云
const skillViewMode = ref<'list' | 'cloud'>('list')

// 经历描述按序号 (1. 2. 3. ...) 自动换行展示
const splitDesc = (desc?: string) => {
  if (!desc) return ''
  return desc.replace(/(\d+[\.、])(?!\d)/g, '\n$1').replace(/^\n/, '').trim()
}

const list = ref<any[]>([])
const loading = ref(false)

// 详情抽屉
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<any>(null)

// 竞争力分析
const competeLoading = ref(false)
const competeResult = ref<any>(null)
const radarChartRef = ref<HTMLElement | null>(null)
let radarChart: echarts.ECharts | null = null

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await resumeApi.list()
    list.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

const showDetail = async (row: any) => {
  drawerVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  competeResult.value = null
  if (radarChart) { radarChart.dispose(); radarChart = null }
  try {
    const res: any = await resumeApi.detail(row.id)
    currentDetail.value = res.data || null
  } catch (e: any) {
    ElMessage.error(e?.message || '加载简历详情失败')
  } finally {
    detailLoading.value = false
  }
}

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

// 竞争力分析
const handleCompete = async () => {
  if (!currentDetail.value?.id) return
  competeLoading.value = true
  competeResult.value = null
  try {
    const res: any = await resumeApi.competitiveness(currentDetail.value.id)
    competeResult.value = res.data || null
    // 渲染雷达图
    nextTick(() => renderRadar())
  } catch (e: any) {
    ElMessage.error(e?.message || '竞争力分析失败')
  } finally {
    competeLoading.value = false
  }
}

const renderRadar = () => {
  if (!radarChartRef.value || !competeResult.value) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(radarChartRef.value)
  const { indicators, values } = competeResult.value.radar
  radarChart.setOption({
    radar: {
      indicator: indicators,
      shape: 'polygon',
      radius: '52%',
      center: ['50%', '52%'],
      axisName: { color: '#666', fontSize: 11 },
      splitArea: { areaStyle: { color: ['#fafafa', '#f0f5ff'] } },
      splitLine: { lineStyle: { color: '#e0e0e0' } },
      axisLine: { lineStyle: { color: '#d9d9d9' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: values,
        name: '我的竞争力',
        areaStyle: { color: 'rgba(22, 119, 255, 0.2)' },
        lineStyle: { color: '#1677ff', width: 2 },
        itemStyle: { color: '#1677ff' },
        symbolSize: 5,
      }],
    }],
  })
}

// 百分位颜色
const pctColor = (pct: number) => {
  if (pct >= 80) return '#52c41a'
  if (pct >= 60) return '#1677ff'
  if (pct >= 40) return '#faad14'
  return '#ff4d4f'
}

const previewFile = async (row: any) => {
  const res: any = await resumeApi.getFile(row.id)
  const url = res.data?.doc_url || ''
  if (!url) { ElMessage.warning('文件不存在'); return }
  const fullUrl = url.startsWith('http') ? url : window.location.origin + url
  if (fullUrl.endsWith('.pdf')) {
    window.open(fullUrl, '_blank')
  } else {
    window.open(`https://docs.google.com/viewer?url=${encodeURIComponent(fullUrl)}&embedded=true`, '_blank')
  }
}

const statusText = (s: number) => ({ 0: '待解析', 1: '解析中', 2: '成功', 3: '失败' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }[s] || 'info')
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

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确认删除该简历?', '提示', { type: 'warning' })
  } catch {
    return // 用户点击取消, 不报错
  }
  try {
    await resumeApi.remove(id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.list-card { border-radius: 12px; }
.card-header { display: flex; align-items: center; justify-content: space-between; font-weight: 600; }
.detail-wrap { padding: 0 4px; }
.section-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #1677ff;
}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.info-row {
  display: flex; padding: 6px 8px; border-bottom: 1px dashed #f0f0f0; font-size: 13px;
}
.info-label { width: 64px; color: #999; flex-shrink: 0; }
.info-value { color: #333; }

.exp-card { padding: 8px 12px; background: #f9fafc; border-radius: 6px; }
.exp-company { font-size: 14px; font-weight: 600; color: #333; }
.exp-desc { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.6; white-space: pre-line; }

.eval-text {
  font-size: 13px; color: #666; line-height: 1.6;
  padding: 10px; background: #fafafa; border-radius: 6px;
}
.skills-row { display: flex; flex-wrap: wrap; gap: 6px; }
.skills-title-row { display: flex; align-items: center; justify-content: space-between; }
.file-section { margin-top: 24px; text-align: center; padding-top: 16px; border-top: 1px solid #f0f0f0; }

/* 竞争力分析面板 */
.compete-card {
  margin-top: 20px;
  background: linear-gradient(135deg, #f0f5ff 0%, #fafafa 100%);
  border: 1px solid #d6e4ff;
  border-radius: 12px;
  padding: 16px;
  overflow: hidden;
}
.compete-card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.compete-card-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 15px; font-weight: 600; color: #1677ff;
}
.compete-card-title .el-icon { font-size: 18px; }
.compete-result { text-align: left; }
.compete-top {
  display: flex; gap: 12px; align-items: center;
}
.radar-chart { width: 280px; height: 230px; flex-shrink: 0; }
.compete-summary { flex: 1; min-width: 0; }
.peer-badge { margin-bottom: 8px; }
.dim-list { display: flex; flex-direction: column; gap: 8px; }
.dim-item { background: #fff; border-radius: 6px; padding: 8px 12px; }
.dim-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px; }
.dim-name { font-size: 12px; font-weight: 600; color: #555; }
.dim-pct { font-size: 13px; font-weight: 700; }
.dim-desc { font-size: 11px; color: #999; margin-top: 4px; line-height: 1.3; }

.suggestion-list { margin-top: 16px; padding-top: 14px; border-top: 1px dashed #d6e4ff; }
.suggestion-title {
  display: flex; align-items: center; gap: 6px;
  font-size: 14px; font-weight: 600; color: #333; margin-bottom: 10px;
}
.suggestion-title .el-icon { color: #1677ff; }
.suggestion-card {
  display: flex; align-items: flex-start; gap: 10px;
  background: #fff; border-radius: 8px; padding: 10px 12px;
  margin-bottom: 8px; font-size: 13px; color: #333; line-height: 1.5;
}
.suggestion-dot {
  flex-shrink: 0; width: 20px; height: 20px; border-radius: 50%;
  background: #1677ff; color: #fff; font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
}
</style>
