<!--
  上传简历页面
  - 支持 .doc/.docx/.pdf, 最大 10MB
  - 上传后调用 AI 解析, 展示结构化结果
  - 解析完成后自动调用 AI 智能分析, 展示改进建议
  - 用户可一键采纳建议, 跳转编辑页进行修改
  - 解析结果持久化到 sessionStorage, 切页后回来不丢失
-->
<template>
  <div class="upload-page">
    <el-card shadow="never" class="upload-card">
      <el-upload
        ref="uploadRef"
        class="upload-dragger"
        drag
        :auto-upload="false"
        :limit="1"
        :on-change="handleChange"
        :on-exceed="handleExceed"
        accept=".doc,.docx,.pdf"
        :disabled="uploading"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽简历到此处, 或<em>点击选择文件</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .doc / .docx / .pdf 格式, 文件大小不超过 10MB
          </div>
        </template>
      </el-upload>

      <div class="actions" v-if="currentFile">
        <el-tag type="info" size="large">{{ currentFile.name }}</el-tag>
        <el-tag size="large">{{ (currentFile.size / 1024).toFixed(1) }} KB</el-tag>
        <el-button
          type="primary"
          :icon="Upload"
          :loading="uploading"
          @click="doUpload"
        >
          {{ uploading ? 'AI 解析中...' : '开始上传并解析' }}
        </el-button>
      </div>
    </el-card>

    <!-- 解析进度动画 -->
    <el-card v-if="uploading" shadow="never" class="parsing-card">
      <div class="parsing-animation">
        <div class="parsing-icon">
          <div class="pulse-ring"></div>
          <div class="pulse-ring delay"></div>
          <el-icon :size="40" color="#1677ff"><MagicStick /></el-icon>
        </div>
        <div class="parsing-title">AI 正在解析您的简历</div>
        <div class="parsing-subtitle">{{ currentFile?.name || '简历文档' }}</div>

        <!-- 步骤进度 -->
        <div class="step-list">
          <div
            v-for="(step, idx) in parseSteps"
            :key="idx"
            class="step-item"
            :class="stepState(idx)"
          >
            <div class="step-icon">
              <el-icon v-if="stepState(idx) === 'done'" :size="16"><Check /></el-icon>
              <el-icon v-else-if="stepState(idx) === 'active'" :size="16" class="rotating"><Loading /></el-icon>
              <span v-else class="step-index">{{ idx + 1 }}</span>
            </div>
            <div class="step-text">
              <div class="step-label">{{ step.label }}</div>
              <div class="step-desc">{{ step.desc }}</div>
            </div>
          </div>
        </div>

        <!-- 进度条 -->
        <el-progress
          :percentage="progressPercent"
          :stroke-width="6"
          :show-text="false"
          color="#1677ff"
          class="parsing-progress"
        />
        <div class="parsing-hint">预计 10-30 秒 (含 AI 智能分析), 请勿离开页面</div>
      </div>
    </el-card>

    <!-- 解析结果 -->
    <el-card v-if="parseResult" shadow="never" class="result-card">
      <template #header>
        <div class="card-header">
          <span>解析结果</span>
          <div class="header-tags">
            <el-tag type="success">解析成功</el-tag>
            <el-button
              type="primary"
              size="small"
              :icon="Edit"
              @click="goEdit"
            >
              去编辑简历
            </el-button>
            <el-button text size="small" :icon="Refresh" @click="resetResult">重新解析</el-button>
          </div>
        </div>
      </template>
      <el-descriptions :column="3" border>
        <el-descriptions-item label="姓名">{{ parseResult.name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="性别">{{ parseResult.gender || '-' }}</el-descriptions-item>
        <el-descriptions-item label="年龄">{{ parseResult.age || '-' }}</el-descriptions-item>
        <el-descriptions-item label="学历">{{ parseResult.education || '-' }}</el-descriptions-item>
        <el-descriptions-item label="学校">{{ parseResult.school || '-' }}</el-descriptions-item>
        <el-descriptions-item label="专业">{{ parseResult.major || '-' }}</el-descriptions-item>
        <el-descriptions-item label="工作年限">{{ parseResult.work_years || 0 }} 年</el-descriptions-item>
        <el-descriptions-item label="当前城市">{{ parseResult.current_city || '-' }}</el-descriptions-item>
        <el-descriptions-item label="期望薪资">{{ parseResult.expected_salary_min || '-' }} - {{ parseResult.expected_salary_max || '-' }} K</el-descriptions-item>
      </el-descriptions>
      <div v-if="parseResult.skills?.length" class="skills-block">
        <h4>技能标签</h4>
        <div class="skill-tags">
          <el-tag
            v-for="sk in parseResult.skills"
            :key="sk.skill_name"
            :type="levelTagType(sk.skill_level)"
            effect="light"
          >
            {{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}
          </el-tag>
        </div>
      </div>
    </el-card>

    <!-- AI 智能分析建议 -->
    <el-card v-if="gapResult" shadow="never" class="gap-card">
      <template #header>
        <div class="card-header">
          <div class="gap-title-row">
            <el-icon :size="18" color="#faad14"><MagicStick /></el-icon>
            <span>AI 智能分析建议</span>
            <div class="score-badge" :style="scoreBadgeStyle">
              完整度 {{ gapResult.overall_score }}%
            </div>
          </div>
          <el-button text size="small" :icon="Close" @click="gapResult = null" />
        </div>
      </template>

      <div class="gap-summary">{{ gapResult.summary }}</div>

      <div class="gap-list">
        <div
          v-for="(gap, idx) in gapResult.gaps"
          :key="idx"
          class="gap-item"
          :class="`priority-${gap.priority}`"
        >
          <div class="gap-item-header">
            <el-tag size="small" :type="priorityTagType(gap.priority)">
              {{ priorityLabel(gap.priority) }}
            </el-tag>
            <span class="gap-category">{{ gap.category }}</span>
          </div>
          <div class="gap-title">{{ gap.title }}</div>
          <div class="gap-desc">{{ gap.description }}</div>
          <div class="gap-actions" v-if="gap.action_type !== 'info'">
            <el-button
              size="small"
              type="primary"
              plain
              @click="acceptAndEdit(gap)"
            >
              采纳并编辑
            </el-button>
          </div>
        </div>
      </div>

      <div class="gap-footer">
        <el-button type="primary" :icon="Edit" @click="goEdit">
          去编辑简历, 完善所有建议
        </el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type UploadInstance, type UploadProps, type UploadRawFile } from 'element-plus'
import { UploadFilled, Upload, MagicStick, Check, Loading, Refresh, Edit, Close } from '@element-plus/icons-vue'
import { resumeApi } from '@/api/resume'

const router = useRouter()
const CACHE_KEY = 'resume_upload_parse_result'
const GAP_CACHE_KEY = 'resume_upload_gap_result'
const RESUME_ID_KEY = 'resume_upload_id'

const uploadRef = ref<UploadInstance>()
const currentFile = ref<UploadRawFile | null>(null)
const uploading = ref(false)
const parseResult = ref<any>(null)
const currentStep = ref(0)
const progressPercent = ref(0)
const resumeIdRef = ref<number | null>(null)

// AI 分析结果
interface GapItem {
  category: string
  title: string
  description: string
  priority: 'high' | 'medium' | 'low'
  action_type: 'skill' | 'text' | 'number' | 'info'
  suggested_value?: any
}
interface GapResult {
  overall_score: number
  summary: string
  gaps: GapItem[]
}
const gapResult = ref<GapResult | null>(null)

// 解析步骤定义 (新增 AI 智能分析步骤)
const parseSteps = [
  { label: '文件上传', desc: '正在上传简历文档' },
  { label: '文本提取', desc: '从文档中提取文字内容' },
  { label: 'AI 结构化', desc: '豆包大模型识别字段与技能' },
  { label: 'AI 智能分析', desc: '分析简历缺失项并给出建议' },
  { label: '完成', desc: '生成解析结果与改进建议' },
]

// 步骤状态: pending / active / done
const stepState = (idx: number) => {
  if (idx < currentStep.value) return 'done'
  if (idx === currentStep.value) return 'active'
  return 'pending'
}

const handleChange: UploadProps['onChange'] = (file) => {
  if (file.raw) {
    if (file.size && file.size > 10 * 1024 * 1024) {
      ElMessage.error('文件不能超过 10MB')
      uploadRef.value?.clearFiles()
      return
    }
    currentFile.value = file.raw
  }
}

const handleExceed: UploadProps['onExceed'] = () => {
  ElMessage.warning('一次只能上传 1 个文件, 请先移除当前文件')
}

// 进度模拟 (视觉反馈, 真实解析耗时由后端决定)
let progressTimer: any = null
const startProgressAnimation = () => {
  currentStep.value = 0
  progressPercent.value = 0
  if (progressTimer) clearInterval(progressTimer)
  progressTimer = setInterval(() => {
    // 缓慢推进, 最多到 90% (真实完成后再到 100%)
    if (progressPercent.value < 90) {
      progressPercent.value += Math.random() * 3 + 0.5
      // 根据进度切换步骤
      if (progressPercent.value < 15) currentStep.value = 0
      else if (progressPercent.value < 40) currentStep.value = 1
      else if (progressPercent.value < 70) currentStep.value = 2
      else if (progressPercent.value < 88) currentStep.value = 3
      else currentStep.value = 4
    }
  }, 400)
}

const stopProgressAnimation = (success: boolean) => {
  if (progressTimer) {
    clearInterval(progressTimer)
    progressTimer = null
  }
  if (success) {
    progressPercent.value = 100
    currentStep.value = 5
  }
}

const doUpload = async () => {
  if (!currentFile.value) {
    ElMessage.warning('请先选择文件')
    return
  }
  uploading.value = true
  gapResult.value = null
  startProgressAnimation()
  try {
    const res: any = await resumeApi.upload(currentFile.value)
    // 进入 AI 结构化阶段
    currentStep.value = 2
    progressPercent.value = Math.max(progressPercent.value, 50)
    // 拉取详情展示 (拦截器返回 {code, message, data}, 取 data 字段)
    const resumeId = res?.data?.resume_id
    if (!resumeId) {
      throw new Error('上传成功但未返回简历ID')
    }
    resumeIdRef.value = resumeId
    sessionStorage.setItem(RESUME_ID_KEY, String(resumeId))

    const detail: any = await resumeApi.detail(resumeId)
    // 创建新对象确保响应式触发, 避免表格不更新
    const detailData = detail?.data || {}
    parseResult.value = { ...detailData }
    // 持久化到 sessionStorage, 切页后可恢复
    try {
      sessionStorage.setItem(CACHE_KEY, JSON.stringify(parseResult.value))
    } catch (e) {
      // 存储满或禁用时静默
    }
    stopProgressAnimation(true)
    ElMessage.success('简历解析成功, 正在进行 AI 智能分析...')

    // 自动调用 AI 智能分析
    await runGapAnalysis(resumeId)
  } catch (e) {
    stopProgressAnimation(false)
    // 已由 axios 拦截器提示
  } finally {
    uploading.value = false
  }
}

// AI 智能分析
const runGapAnalysis = async (resumeId: number) => {
  try {
    const res: any = await resumeApi.gapAnalysis(resumeId)
    const data = res.data || {}
    if (data.gaps && data.gaps.length > 0) {
      gapResult.value = data
      // 持久化分析结果
      try {
        sessionStorage.setItem(GAP_CACHE_KEY, JSON.stringify(data))
      } catch (e) {
        // 静默
      }
      ElMessage.success(`AI 分析完成, 发现 ${data.gaps.length} 条改进建议`)
    } else {
      ElMessage.success('AI 分析完成, 您的简历已经很完善了!')
    }
  } catch (e: any) {
    ElMessage.warning('AI 智能分析失败, 您可以稍后在编辑页面重试')
  }
}

// 采纳建议并跳转到编辑页
const acceptAndEdit = (gap: GapItem) => {
  // 把建议存入 sessionStorage, 编辑页读取后自动填充
  const accepted = sessionStorage.getItem('resume_accepted_gaps')
  let list: any[] = []
  try {
    list = accepted ? JSON.parse(accepted) : []
  } catch {
    list = []
  }
  list.push(gap)
  sessionStorage.setItem('resume_accepted_gaps', JSON.stringify(list))
  ElMessage.success(`已采纳建议: ${gap.title}, 即将跳转编辑页`)
  setTimeout(() => {
    if (resumeIdRef.value) {
      router.push(`/seeker/resume/${resumeIdRef.value}/edit`)
    }
  }, 600)
}

// 跳转到编辑页
const goEdit = () => {
  if (resumeIdRef.value) {
    router.push(`/seeker/resume/${resumeIdRef.value}/edit`)
  } else {
    ElMessage.warning('未找到简历ID, 请先上传简历')
  }
}

// 重新解析: 清除缓存与结果
const resetResult = () => {
  parseResult.value = null
  gapResult.value = null
  sessionStorage.removeItem(CACHE_KEY)
  sessionStorage.removeItem(GAP_CACHE_KEY)
  sessionStorage.removeItem(RESUME_ID_KEY)
  sessionStorage.removeItem('resume_accepted_gaps')
  currentFile.value = null
  resumeIdRef.value = null
  uploadRef.value?.clearFiles()
  ElMessage.info('已清空解析结果, 请重新上传')
}

const levelTagType = (level?: string) => {
  if (level === '精通') return 'danger'
  if (level === '熟练') return 'warning'
  if (level === '掌握') return 'success'
  return 'info'
}

// ===== AI 建议相关 =====
const priorityLabel = (p: string) => {
  const map: Record<string, string> = { high: '重要', medium: '建议', low: '可选' }
  return map[p] || p
}

const priorityTagType = (p: string) => {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return (map[p] || 'info') as any
}

const scoreBadgeStyle = computed(() => {
  const score = gapResult.value?.overall_score ?? 0
  const color = score >= 80 ? '#52c41a' : score >= 60 ? '#1677ff' : score >= 40 ? '#faad14' : '#ff4d4f'
  return {
    background: `${color}15`,
    color,
    border: `1px solid ${color}40`,
  }
})

// 挂载时尝试从 sessionStorage 恢复解析结果
onMounted(() => {
  try {
    const cached = sessionStorage.getItem(CACHE_KEY)
    if (cached) {
      parseResult.value = JSON.parse(cached)
    }
    const gapCached = sessionStorage.getItem(GAP_CACHE_KEY)
    if (gapCached) {
      gapResult.value = JSON.parse(gapCached)
    }
    const rid = sessionStorage.getItem(RESUME_ID_KEY)
    if (rid) {
      resumeIdRef.value = Number(rid)
    }
  } catch (e) {
    // 解析失败则忽略
  }
})
</script>

<style scoped>
.upload-page { max-width: 900px; margin: 0 auto; }
.upload-card { border-radius: 12px; margin-bottom: 16px; }
.upload-dragger { width: 100%; }
.actions {
  display: flex; align-items: center; gap: 12px;
  margin-top: 16px; padding: 12px; background: #f5f7fa;
  border-radius: 8px;
}

/* ===== 解析动画卡片 ===== */
.parsing-card { border-radius: 12px; margin-bottom: 16px; }
.parsing-animation {
  display: flex; flex-direction: column; align-items: center;
  padding: 24px 16px;
}
.parsing-icon {
  position: relative; width: 80px; height: 80px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 16px;
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
.parsing-title {
  font-size: 16px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 4px;
}
.parsing-subtitle {
  font-size: 13px; color: var(--text-secondary); margin-bottom: 20px;
}

/* 步骤列表 */
.step-list {
  width: 100%; max-width: 420px; margin-bottom: 20px;
  display: flex; flex-direction: column; gap: 10px;
}
.step-item {
  display: flex; align-items: center; gap: 12px;
  padding: 8px 12px; border-radius: 8px;
  transition: all 0.3s; opacity: 0.5;
}
.step-item.active { opacity: 1; background: #e6f4ff; }
.step-item.done { opacity: 0.85; }
.step-icon {
  width: 26px; height: 26px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: #f0f0f0; color: var(--text-secondary); flex-shrink: 0;
  font-size: 12px;
}
.step-item.active .step-icon { background: #1677ff; color: #fff; }
.step-item.done .step-icon { background: #52c41a; color: #fff; }
.step-index { font-weight: 600; }
.step-text { flex: 1; }
.step-label { font-size: 13px; font-weight: 500; color: var(--text-primary); }
.step-desc { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.rotating { animation: rotate 1s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }

.parsing-progress { width: 100%; max-width: 420px; }
.parsing-hint {
  margin-top: 10px; font-size: 12px; color: var(--text-secondary);
}

/* ===== 解析结果 ===== */
.result-card { border-radius: 12px; margin-bottom: 16px; }
.card-header {
  display: flex; align-items: center; justify-content: space-between; font-weight: 600;
}
.header-tags { display: flex; align-items: center; gap: 8px; }
.skills-block { margin-top: 20px; }
.skills-block h4 { margin-bottom: 12px; color: var(--text-primary); }
.skill-tags { display: flex; flex-wrap: wrap; gap: 8px; }

/* ===== AI 分析建议卡片 ===== */
.gap-card { border-radius: 12px; }
.gap-title-row {
  display: flex; align-items: center; gap: 8px;
}
.score-badge {
  padding: 2px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 600;
}
.gap-summary {
  padding: 12px 16px; margin-bottom: 12px;
  background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  border-radius: 8px; font-size: 14px; color: #614700;
  line-height: 1.6;
}
.gap-list {
  display: flex; flex-direction: column; gap: 10px;
}
.gap-item {
  padding: 14px 16px; border-radius: 10px;
  background: #fafafa; border-left: 4px solid #d9d9d9;
  transition: box-shadow 0.2s;
}
.gap-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.gap-item.priority-high { border-left-color: #ff4d4f; }
.gap-item.priority-medium { border-left-color: #faad14; }
.gap-item.priority-low { border-left-color: #1677ff; }
.gap-item-header {
  display: flex; align-items: center; gap: 8px; margin-bottom: 6px;
}
.gap-category { font-size: 12px; color: #999; }
.gap-title {
  font-size: 14px; font-weight: 600; color: #333; margin-bottom: 4px;
}
.gap-desc {
  font-size: 13px; color: #666; line-height: 1.6; margin-bottom: 8px;
}
.gap-actions { display: flex; gap: 8px; }
.gap-footer {
  margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0;
  display: flex; justify-content: center;
}
</style>
