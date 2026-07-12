<!--
  能力关系图谱 (高保真UI) - 深色科技风 / 力导向图 / 霓虹发光
  - 中心节点: 求职者
  - 环绕节点: 技能 (已匹配绿色 / 缺失红色)
  - 右侧节点: 目标岗位
  - 底部: 匹配度 + 能力缺失警告
  - 适合大屏展示与毕业设计答辩
-->
<template>
  <div class="graph-page">
    <!-- 顶部控制栏 (玻璃拟态) -->
    <div class="glass-toolbar">
      <div class="toolbar-left">
        <span class="label">选择简历:</span>
        <el-select
          v-model="resumeId"
          placeholder="请选择简历"
          style="width: 240px"
          :loading="resumesLoading"
          @change="fetchGraph"
        >
          <el-option
            v-for="r in resumes"
            :key="r.id"
            :label="`${r.name || '简历#' + r.id}${r.education ? ' - ' + r.education : ''}`"
            :value="r.id"
          />
        </el-select>
        <span class="label" style="margin-left: 16px">目标岗位:</span>
        <el-select
          v-model="jobId"
          placeholder="选择岗位查看匹配"
          style="width: 220px"
          filterable
          @change="renderGraph"
        >
          <el-option
            v-for="j in jobOptions"
            :key="j.id"
            :label="`${j.title} · ${j.company || ''}`"
            :value="j.id"
          />
        </el-select>
      </div>
      <div class="toolbar-right">
        <div class="status-pill" :class="{ active: nodes.length }">
          <span class="dot"></span>
          {{ nodes.length ? `节点 ${nodes.length} · 关系 ${edges.length}` : '待加载' }}
        </div>
        <el-button :icon="Refresh" circle @click="fetchGraph" :loading="loading" />
      </div>
    </div>

    <!-- 主图谱区 -->
    <div class="graph-container" v-loading="loading" element-loading-background="rgba(15,12,41,0.7)">
      <!-- 加载错误提示 -->
      <div v-if="errorMsg && !loading" class="error-panel glass">
        <el-icon :size="48" color="#ff6b6b"><WarningFilled /></el-icon>
        <div class="error-title">图谱加载失败</div>
        <div class="error-msg">{{ errorMsg }}</div>
        <el-button type="primary" @click="fetchGraph">重试</el-button>
      </div>

      <!-- 空状态 -->
      <div v-else-if="!resumes.length && !resumesLoading" class="error-panel glass">
        <el-icon :size="48" color="#a78bfa"><DataAnalysis /></el-icon>
        <div class="error-title">暂无可用于构建图谱的简历</div>
        <div class="error-msg">请先上传简历并完成 AI 解析</div>
        <el-button type="primary" @click="$router.push('/seeker/resume/upload')">去上传简历</el-button>
      </div>

      <div v-else-if="!resumeId && !loading" class="error-panel glass">
        <el-icon :size="48" color="#a78bfa"><DataAnalysis /></el-icon>
        <div class="error-title">请选择一份简历</div>
        <div class="error-msg">选择已解析的简历以构建能力关系图谱</div>
      </div>

      <!-- 图谱 + 侧边面板 -->
      <div v-else class="graph-layout">
        <!-- 左侧: 能力概览面板 -->
        <div class="side-panel glass">
          <div class="panel-title">能力概览</div>
          <div class="panel-body">
            <div class="stat-row" v-for="s in skillStats" :key="s.label">
              <span class="stat-dot" :style="{ background: s.color }"></span>
              <span class="stat-label">{{ s.label }}</span>
              <span class="stat-value">{{ s.value }}</span>
            </div>
          </div>
          <div class="panel-divider"></div>
          <div class="panel-title">技能雷达</div>
          <div ref="radarRef" class="radar-box"></div>
        </div>

        <!-- 中央: 力导向图谱 -->
        <div class="center-graph">
          <div ref="graphRef" class="echarts-box"></div>
          <!-- 底部: 匹配度 + 缺失警告 -->
          <div class="bottom-panel glass" v-if="matchScore !== null">
            <div class="match-score">
              <div class="score-circle" :style="scoreStyle">
                <span class="score-num">{{ matchScore }}</span>
                <span class="score-unit">%</span>
              </div>
              <div class="score-label">岗位匹配度</div>
            </div>
            <div class="match-detail">
              <div class="detail-row">
                <span class="detail-label">已匹配技能</span>
                <div class="tag-list">
                  <span v-for="s in matchedSkills" :key="s" class="neon-tag green">{{ s }}</span>
                  <span v-if="!matchedSkills.length" class="muted-text">暂无</span>
                </div>
              </div>
              <div class="detail-row" v-if="missingSkills.length">
                <span class="detail-label">能力缺失</span>
                <div class="tag-list">
                  <span v-for="s in missingSkills" :key="s" class="neon-tag red">
                    <el-icon><WarningFilled /></el-icon>
                    {{ s }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, WarningFilled, DataAnalysis } from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { resumeApi } from '@/api/resume'
import { graphApi } from '@/api/graph'
import { jobApi } from '@/api/job'
import { matchApi } from '@/api/match'

const route = useRoute()
const resumes = ref<any[]>([])
const resumeId = ref<number | null>(null)
const jobId = ref<number | null>(null)
const jobOptions = ref<any[]>([])
const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const loading = ref(false)
const resumesLoading = ref(false)
const errorMsg = ref('')

// 匹配数据
const matchScore = ref<number | null>(null)
const matchedSkills = ref<string[]>([])
const missingSkills = ref<string[]>([])
const allSkills = ref<{ name: string; level: string }[]>([])

// 六维度匹配分 (后端统一数据源, 0-1 区间)
const dimensionScores = ref({
  skill: 0,
  experience: 0,
  education: 0,
  city: 0,
  salary: 0,
  project: 0,
})

// ECharts 实例
const graphRef = ref<HTMLElement>()
const radarRef = ref<HTMLElement>()
let graphChart: echarts.ECharts | null = null
let radarChart: echarts.ECharts | null = null

// 技能统计 (匹配度统一由底部"岗位匹配度"展示, 此处不再重复)
const skillStats = computed(() => {
  const total = allSkills.value.length
  const matched = matchedSkills.value.length
  const missing = missingSkills.value.length
  return [
    { label: '技能总数', value: total, color: '#a78bfa' },
    { label: '已匹配', value: matched, color: '#52c41a' },
    { label: '能力缺失', value: missing, color: '#ff4d4f' },
  ]
})

// 匹配度环形样式
const scoreStyle = computed(() => {
  const score = matchScore.value ?? 0
  const color = score >= 80 ? '#52c41a' : score >= 60 ? '#1677ff' : score >= 40 ? '#faad14' : '#ff4d4f'
  const deg = (score / 100) * 360
  return {
    background: `conic-gradient(${color} ${deg}deg, rgba(255,255,255,0.08) ${deg}deg)`,
    color,
  }
})

const fetchResumes = async () => {
  resumesLoading.value = true
  errorMsg.value = ''
  try {
    const res: any = await resumeApi.list()
    const all = res.data?.items || []
    resumes.value = all.filter((r: any) => r.parse_status === 2)
    if (!resumes.value.length) {
      ElMessage.warning('暂无已解析成功的简历, 无法构建图谱')
    }
    if (route.query.resume_id) {
      const id = Number(route.query.resume_id)
      if (resumes.value.some(r => r.id === id)) {
        resumeId.value = id
        fetchGraph()
      } else {
        ElMessage.warning('该简历尚未解析完成, 暂不可视化')
      }
    }
  } catch (e: any) {
    resumes.value = []
    ElMessage.error(e?.message || '简历列表加载失败')
  } finally {
    resumesLoading.value = false
  }
}

const fetchJobs = async () => {
  try {
    const res: any = await jobApi.list({ page: 1, size: 100 })
    jobOptions.value = res.data?.items || []
  } catch (e) {
    jobOptions.value = []
  }
}

const fetchGraph = async () => {
  if (!resumeId.value) {
    ElMessage.warning('请先选择简历')
    return
  }
  loading.value = true
  errorMsg.value = ''
  nodes.value = []
  edges.value = []
  matchScore.value = null
  matchedSkills.value = []
  missingSkills.value = []
  allSkills.value = []
  try {
    const res: any = await graphApi.resumeGraph(resumeId.value)
    const rawNodes = res.data?.nodes || []
    const rawEdges = res.data?.edges || []

    // 提取技能节点和分类节点
    const skillNodes = rawNodes.filter((n: any) => n.type === 'Skill')
    const categoryNodes = rawNodes.filter((n: any) => n.type === 'Category')
    allSkills.value = skillNodes.map((n: any) => ({ name: n.label, level: n.properties?.level || '掌握' }))

    // 构建图谱节点 (求职者在中心, 分类节点中层, 技能节点外层)
    const personNode = rawNodes.find((n: any) => n.type === 'Person')
    const personName = personNode?.label || '求职者'

    const graphNodes: any[] = [
      {
        id: 'person',
        name: personName,
        category: 0,
        symbolSize: 70,
        itemStyle: { color: '#a78bfa', shadowBlur: 30, shadowColor: 'rgba(167,139,250,0.8)' },
        label: { show: true, color: '#fff', fontSize: 15, fontWeight: 'bold' },
      },
    ]

    // 分类节点 (中层)
    categoryNodes.forEach((c: any) => {
      graphNodes.push({
        id: c.id,
        name: c.label,
        category: 1,
        symbolSize: 55,
        itemStyle: {
          color: '#40a9ff',
          shadowBlur: 20,
          shadowColor: 'rgba(64,169,255,0.6)',
          borderColor: '#91d5ff',
          borderWidth: 2,
        },
        label: { show: true, color: '#e0f0ff', fontSize: 13, fontWeight: 'bold' },
      })
    })

    // 技能节点 (外层)
    skillNodes.forEach((s: any) => {
      graphNodes.push({
        id: s.id,
        name: s.label,
        category: 2,
        symbolSize: 48,
        itemStyle: {
          color: '#95de64',
          shadowBlur: 28,
          shadowColor: 'rgba(149,222,100,0.95)',
          borderColor: '#b7eb8f',
          borderWidth: 2,
        },
        label: { show: true, color: '#fff', fontSize: 13, fontWeight: 'bold' },
      })
    })

    // 边: 求职者 -> 分类 -> 技能
    const graphEdges: any[] = []
    rawEdges.forEach((e: any) => {
      if (e.label === 'HAS_CATEGORY') {
        graphEdges.push({
          source: 'person',
          target: e.target,
          lineStyle: { color: 'rgba(64,169,255,0.5)', width: 2.5, curveness: 0.1 },
        })
      } else if (e.label === 'INCLUDES') {
        graphEdges.push({
          source: e.source,
          target: e.target,
          lineStyle: { color: 'rgba(149,222,100,0.4)', width: 1.5, curveness: 0.1 },
        })
      }
    })

    // 如果选了岗位, 添加岗位节点和匹配边
    if (jobId.value) {
      const job = jobOptions.value.find(j => j.id === jobId.value)
      if (job) {
        // 获取岗位技能要求 (从职位详情)
      const detail: any = await jobApi.detail(jobId.value)
      const reqSkills = (detail.data?.requirements || []).map((r: any) => r.skill_name)
      const mySkillNames = skillNodes.map((s: any) => s.label)

      // 技能别名归一化映射 (与后端 match_service.py 保持一致)
      const skillAliasMap: Record<string, string[]> = {
        'office': ['office办公软件', 'office套件', 'office', 'msoffice', 'ms office'],
        'python': ['python', 'python3', 'py'],
        'java': ['java', 'java语言', 'jdk'],
        'mysql': ['mysql', 'sql', '数据库'],
        'linux': ['linux', 'linux系统', 'unix'],
        'vue': ['vue', 'vue.js', 'vuejs'],
        'react': ['react', 'react.js', 'reactjs'],
        'docker': ['docker', '容器', '容器化'],
        'kubernetes': ['kubernetes', 'k8s'],
      }

      // 构建反向索引: 技能名 -> 标准名
      const normalizeMap: Record<string, string> = {}
      for (const [std, aliases] of Object.entries(skillAliasMap)) {
        for (const alias of aliases) {
          normalizeMap[alias.toLowerCase()] = std
        }
      }

      // 归一化函数
      const normalize = (name: string): string => {
        const n = (name || '').toLowerCase().trim()
        return normalizeMap[n] || n
      }

      // 模糊匹配函数
      const isSkillMatch = (reqSkill: string, mySkills: string[]): boolean => {
        // 1. 精确匹配
        if (mySkills.includes(reqSkill)) return true
        // 2. 归一化匹配
        const reqNorm = normalize(reqSkill)
        for (const mySkill of mySkills) {
          if (normalize(mySkill) === reqNorm) return true
        }
        // 3. 包含关系匹配
        const reqLower = reqSkill.toLowerCase()
        for (const mySkill of mySkills) {
          const myLower = mySkill.toLowerCase()
          if (reqLower.includes(myLower) || myLower.includes(reqLower)) return true
        }
        return false
      }

      // 匹配/缺失 (仅用于图谱节点展示, 匹配度由后端六维度引擎计算)
      matchedSkills.value = reqSkills.filter((s: string) => isSkillMatch(s, mySkillNames))
      missingSkills.value = reqSkills.filter((s: string) => !isSkillMatch(s, mySkillNames))

        // 调用后端统一匹配度引擎 (六维度加权评分, 与投递管理/推荐列表同源)
        try {
          const scoreRes: any = await matchApi.getScore(resumeId.value, jobId.value)
          const sd = scoreRes.data
          matchScore.value = Math.round(sd.total_score)
          dimensionScores.value = {
            skill: sd.skill_score,
            experience: sd.experience_score,
            education: sd.education_score,
            city: sd.city_score,
            salary: sd.salary_score,
            project: sd.project_score,
          }
        } catch (err: any) {
          // 后端匹配引擎不可用时, 降级到技能匹配率
          matchScore.value = reqSkills.length > 0
            ? Math.round((matchedSkills.value.length / reqSkills.length) * 100)
            : 0
          dimensionScores.value = { skill: 0, experience: 0, education: 0, city: 0, salary: 0, project: 0 }
        }

        // 岗位节点 (始终使用 job.title, 避免显示 "job_56" 等内部 ID)
        graphNodes.push({
          id: 'job',
          name: job.title || `职位#${job.id}`,
          category: 2,
          symbolSize: 60,
          itemStyle: { color: '#ff6b35', shadowBlur: 30, shadowColor: 'rgba(255,107,53,0.8)' },
          label: { show: true, color: '#fff', fontSize: 14, fontWeight: 'bold' },
          x: 500, y: 0, fixed: true,
        })

        // 岗位 -> 已匹配技能 (绿色发光线)
        matchedSkills.value.forEach((skillName: string) => {
          const skillNode = skillNodes.find((s: any) => s.label === skillName)
          if (skillNode) {
            graphEdges.push({
              source: 'job',
              target: skillNode.id,
              lineStyle: {
                color: '#52c41a', width: 3, curveness: 0.2,
                shadowBlur: 15, shadowColor: 'rgba(82,196,26,0.8)',
              },
            })
          }
        })
        // 岗位 -> 缺失技能 (红色虚线, 新增虚拟节点)
        missingSkills.value.forEach((skillName: string) => {
          const missId = 'miss_' + skillName
          graphNodes.push({
            id: missId,
            name: skillName,
            category: 3,
            symbolSize: 38,
            itemStyle: {
              color: '#ff4d4f', shadowBlur: 20, shadowColor: 'rgba(255,77,79,0.7)',
              borderColor: '#ff4d4f', borderWidth: 2, borderType: 'dashed',
            },
            label: { show: true, color: '#ffb3b3', fontSize: 11 },
          })
          graphEdges.push({
            source: 'job',
            target: missId,
            lineStyle: {
              color: '#ff4d4f', width: 2, curveness: 0.2, type: 'dashed',
              shadowBlur: 10, shadowColor: 'rgba(255,77,79,0.6)',
            },
          })
        })
      }
    } else {
      // 未选岗位时清空匹配度
      matchScore.value = null
      dimensionScores.value = { skill: 0, experience: 0, education: 0, city: 0, salary: 0, project: 0 }
    }

    nodes.value = graphNodes
    edges.value = graphEdges
    await nextTick()
    renderGraph()
    renderRadar()
  } catch (e: any) {
    errorMsg.value = e?.message || '图谱构建失败, 请稍后重试'
    ElMessage.error(errorMsg.value)
  } finally {
    loading.value = false
  }
}

const renderGraph = () => {
  if (!graphRef.value || !nodes.value.length) return
  if (graphChart) graphChart.dispose()
  graphChart = echarts.init(graphRef.value, 'dark')

  const categories = [
    { name: '求职者' },
    { name: '已掌握技能' },
    { name: '目标岗位' },
    { name: '缺失技能' },
  ]

  graphChart.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      backgroundColor: 'rgba(48,43,99,0.9)',
      borderColor: '#a78bfa',
      borderWidth: 1,
      textStyle: { color: '#e0e7ff', fontSize: 13 },
      formatter: (p: any) => {
        if (p.dataType === 'node') return `<b>${p.data.name}</b><br/>类型: ${categories[p.data.category]?.name || ''}`
        return `${p.data.source} → ${p.data.target}`
      },
    },
    legend: {
      data: categories.map(c => c.name),
      textStyle: { color: '#c4b5fd', fontSize: 12 },
      top: 10, left: 'center',
      itemGap: 20,
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes.value,
      links: edges.value,
      categories,
      roam: true,
      draggable: true,
      force: {
        repulsion: 400,
        edgeLength: [80, 160],
        gravity: 0.08,
        layoutAnimation: true,
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: { width: 4 },
        label: { fontSize: 16 },
      },
      lineStyle: { curveness: 0.15 },
    }],
  })
}

const renderRadar = () => {
  if (!radarRef.value) return
  if (radarChart) radarChart.dispose()
  radarChart = echarts.init(radarRef.value, 'dark')

  // 六维度能力雷达 (数据来自后端 match_service.coarse_rank)
  const dims = [
    { key: 'skill', label: '技能' },
    { key: 'experience', label: '经验' },
    { key: 'education', label: '学历' },
    { key: 'city', label: '城市' },
    { key: 'salary', label: '薪资' },
    { key: 'project', label: '项目' },
  ] as const

  // 我的能力: 后端六维度评分 (0-1 → 0-100)
  const myValues = dims.map(d => Math.round((dimensionScores.value[d.key] || 0) * 100))

  const series: any[] = [{
    value: myValues,
    name: '我的能力',
    areaStyle: { color: 'rgba(167,139,250,0.3)' },
    lineStyle: { color: '#a78bfa', width: 2 },
    itemStyle: { color: '#a78bfa' },
  }]

  // 岗位要求: 选中岗位时叠加 90 分基准线
  const hasJob = jobId.value && matchScore.value !== null
  if (hasJob) {
    series.push({
      value: dims.map(() => 90),
      name: '岗位要求',
      areaStyle: { color: 'rgba(255,107,53,0.12)' },
      lineStyle: { color: '#ff6b35', width: 2, type: 'dashed' },
      itemStyle: { color: '#ff6b35' },
    })
  }

  radarChart.setOption({
    backgroundColor: 'transparent',
    legend: hasJob ? {
      data: ['我的能力', '岗位要求'],
      textStyle: { color: '#e0e7ff', fontSize: 12, fontWeight: 500 },
      top: 8, left: 'center', itemGap: 30,
      icon: 'roundRect',
      itemWidth: 14,
      itemHeight: 10,
    } : { show: false },
    radar: {
      indicator: dims.map(d => ({ name: d.label, max: 100, nameGap: 12 })),
      shape: 'polygon',
      radius: '55%',
      center: ['50%', '55%'],
      axisName: { color: '#e0e7ff', fontSize: 12, fontWeight: 500 },
      splitArea: { areaStyle: { color: ['rgba(167,139,250,0.03)', 'rgba(167,139,250,0.08)'] } },
      splitLine: { lineStyle: { color: 'rgba(167,139,250,0.15)' } },
      axisLine: { lineStyle: { color: 'rgba(167,139,250,0.15)' } },
    },
    series: [{
      type: 'radar',
      data: series,
      symbolSize: 6,
    }],
  })
}

const handleResize = () => {
  graphChart?.resize()
  radarChart?.resize()
}

onMounted(() => {
  fetchResumes()
  fetchJobs()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  graphChart?.dispose()
  radarChart?.dispose()
})

// 选择岗位时重新构建图谱
watch(jobId, () => {
  if (resumeId.value) fetchGraph()
})
</script>

<style scoped>
.graph-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: calc(100vh - 120px);
}

/* 玻璃拟态工具栏 */
.glass-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  background: rgba(48, 43, 99, 0.35);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 12px;
}
.toolbar-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.toolbar-right { display: flex; align-items: center; gap: 12px; }
.label { color: #c4b5fd; font-size: 13px; font-weight: 500; }

/* 状态指示器 */
.status-pill {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 20px;
  background: rgba(255,255,255,0.06);
  color: #94a3b8; font-size: 12px;
}
.status-pill.active { color: #2d8a1a; }
.status-pill .dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: #64748b;
}
.status-pill.active .dot {
  background: #2d8a1a;
  box-shadow: 0 0 8px #2d8a1a;
  animation: pulse-dot 1.5s ease-in-out infinite;
}
@keyframes pulse-dot { 0%,100%{opacity:1} 50%{opacity:0.5} }

/* 主容器: 深色科技风背景 */
.graph-container {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
  border-radius: 16px;
  overflow: hidden;
  min-height: 600px;
}
/* 背景装饰: 星点 */
.graph-container::before {
  content: '';
  position: absolute; inset: 0;
  background-image:
    radial-gradient(2px 2px at 20% 30%, rgba(167,139,250,0.4), transparent),
    radial-gradient(1px 1px at 60% 70%, rgba(96,165,250,0.4), transparent),
    radial-gradient(2px 2px at 80% 20%, rgba(167,139,250,0.3), transparent),
    radial-gradient(1px 1px at 40% 80%, rgba(96,165,250,0.3), transparent);
  background-size: 200px 200px;
  pointer-events: none;
}

/* 图谱布局 */
.graph-layout {
  display: flex;
  height: 100%;
  min-height: 600px;
  position: relative;
  z-index: 1;
}

/* 左侧面板 */
.side-panel {
  width: 280px;
  flex-shrink: 0;
  padding: 18px;
  background: rgba(15, 12, 41, 0.5);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-right: 1px solid rgba(167, 139, 250, 0.2);
  overflow-y: auto;
}
.panel-title {
  font-size: 14px; font-weight: 600; color: #a78bfa;
  margin-bottom: 12px; letter-spacing: 1px;
}
.panel-body { display: flex; flex-direction: column; gap: 10px; }
.stat-row {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: #e0e7ff;
}
.stat-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.stat-label { flex: 1; }
.stat-value { font-weight: 600; color: #fff; }
.panel-divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(167,139,250,0.3), transparent);
  margin: 20px 0;
}
.radar-box { width: 100%; height: 220px; }

/* 中央图谱区 */
.center-graph {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
}
.echarts-box { flex: 1; width: 100%; min-height: 480px; }

/* 底部匹配度面板 */
.bottom-panel {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 24px;
  margin: 0 20px 20px;
  background: rgba(15, 12, 41, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
}

/* 匹配度环形 */
.match-score { display: flex; flex-direction: column; align-items: center; gap: 4px; flex-shrink: 0; }
.score-circle {
  width: 80px; height: 80px; border-radius: 50%;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  position: relative;
}
.score-circle::before {
  content: '';
  position: absolute; inset: 6px;
  border-radius: 50%;
  background: rgba(15, 12, 41, 0.85);
}
.score-num { font-size: 28px; font-weight: 700; position: relative; z-index: 1; }
.score-unit { font-size: 12px; position: relative; z-index: 1; opacity: 0.8; }
.score-label { font-size: 12px; color: #c4b5fd; }

.match-detail { flex: 1; display: flex; flex-direction: column; gap: 8px; }
.detail-row { display: flex; align-items: flex-start; gap: 10px; }
.detail-label {
  font-size: 12px; color: #94a3b8; width: 70px; flex-shrink: 0;
  padding-top: 2px;
}
.tag-list { display: flex; flex-wrap: wrap; gap: 6px; flex: 1; }

/* 霓虹发光标签 */
.neon-tag {
  display: inline-flex; align-items: center; gap: 3px;
  padding: 2px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 500;
}
.neon-tag.green {
  color: #52c41a;
  background: rgba(82, 196, 26, 0.12);
  border: 1px solid rgba(82, 196, 26, 0.4);
  box-shadow: 0 0 8px rgba(82, 196, 26, 0.3);
}
.neon-tag.red {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.12);
  border: 1px solid rgba(255, 77, 79, 0.5);
  box-shadow: 0 0 10px rgba(255, 77, 79, 0.4);
  animation: warn-pulse 2s ease-in-out infinite;
}
@keyframes warn-pulse {
  0%, 100% { box-shadow: 0 0 6px rgba(255, 77, 79, 0.3); }
  50% { box-shadow: 0 0 14px rgba(255, 77, 79, 0.6); }
}
.muted-text { color: #64748b; font-size: 12px; }

/* 错误/空状态面板 */
.error-panel {
  position: absolute; inset: 0;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px;
}
.error-title { font-size: 18px; font-weight: 600; color: #e0e7ff; }
.error-msg { font-size: 14px; color: #94a3b8; text-align: center; max-width: 400px; }

/* 玻璃拟态通用 */
.glass {
  background: rgba(48, 43, 99, 0.25);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
}
</style>
