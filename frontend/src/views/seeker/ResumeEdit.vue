<!--
  简历在线编辑页面
  - 支持编辑基本信息、教育背景、技能
  - 灵犀智能分析简历缺失项, 支持一键采纳建议
  - 从简历详情加载数据，保存后更新
-->
<template>
  <div class="edit-page">
    <el-card shadow="never" class="edit-card">
      <template #header>
        <div class="card-header">
          <span>编辑简历</span>
          <div class="header-actions">
            <el-button
              type="warning"
              plain
              @click="runGapAnalysis"
              :loading="analyzing"
              :icon="MagicStick"
            >
              灵犀智能分析
            </el-button>
            <el-button @click="$router.back()">返回</el-button>
          </div>
        </div>
      </template>

      <!-- 灵犀分析结果面板 -->
      <el-collapse-transition>
        <div v-if="gapResult" class="gap-panel">
          <div class="gap-header">
            <div class="gap-score">
              <div class="score-ring" :style="scoreRingStyle">
                <span class="score-num">{{ gapResult.overall_score }}</span>
              </div>
              <div class="score-info">
                <div class="score-label">简历完整度</div>
                <div class="score-summary">{{ gapResult.summary }}</div>
              </div>
            </div>
            <el-button text @click="gapResult = null" :icon="Close" />
          </div>

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
                  @click="applySuggestion(gap)"
                >
                  一键采纳
                </el-button>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-transition>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        v-loading="loading"
      >
        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="请选择性别" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="年龄" prop="age">
              <el-input-number v-model="form.age" :min="16" :max="80" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="工作年限" prop="work_years">
              <el-input-number v-model="form.work_years" :min="0" :max="50" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="form.email" placeholder="请输入邮箱" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="所在城市" prop="current_city">
              <el-input v-model="form.current_city" placeholder="如：北京" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="意向城市">
              <el-input v-model="intentionCitiesText" placeholder="多个城市用逗号分隔，如：北京,上海" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">教育背景</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="学历" prop="education">
              <el-select v-model="form.education" placeholder="请选择学历" style="width: 100%">
                <el-option label="高中" value="高中" />
                <el-option label="大专" value="大专" />
                <el-option label="本科" value="本科" />
                <el-option label="硕士" value="硕士" />
                <el-option label="博士" value="博士" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="学校" prop="school">
              <el-input v-model="form.school" placeholder="请输入学校名称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="专业" prop="major">
              <el-input v-model="form.major" placeholder="请输入专业" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">期望薪资</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最低薪资 (K)">
              <el-input-number v-model="form.expected_salary_min" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最高薪资 (K)">
              <el-input-number v-model="form.expected_salary_max" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">自我评价</el-divider>

        <el-form-item prop="self_evaluation">
          <el-input
            v-model="form.self_evaluation"
            type="textarea"
            :rows="4"
            placeholder="请简要介绍自己的优势和特长"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>

        <el-divider content-position="left">技能清单</el-divider>

        <div class="skills-section">
          <div v-for="(skill, index) in form.skills" :key="index" class="skill-item">
            <el-row :gutter="10" align="middle">
              <el-col :span="10">
                <el-input v-model="skill.skill_name" placeholder="技能名称" />
              </el-col>
              <el-col :span="8">
                <el-select v-model="skill.skill_level" placeholder="掌握程度" style="width: 100%">
                  <el-option label="精通" value="精通" />
                  <el-option label="熟练" value="熟练" />
                  <el-option label="掌握" value="掌握" />
                  <el-option label="了解" value="了解" />
                </el-select>
              </el-col>
              <el-col :span="4">
                <el-button type="danger" @click="removeSkill(index)" :icon="Delete" circle />
              </el-col>
            </el-row>
          </div>
          <el-button type="primary" plain @click="addSkill" :icon="Plus" style="margin-top: 10px">
            添加技能
          </el-button>
        </div>

        <el-divider />

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="saving" size="large">
            保存修改
          </el-button>
          <el-button @click="$router.back()" size="large">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { Plus, Delete, MagicStick, Close } from '@element-plus/icons-vue'
import { resumeApi } from '@/api/resume'

const route = useRoute()
const router = useRouter()

const resumeId = Number(route.params.id)
const formRef = ref<FormInstance>()
const loading = ref(false)
const saving = ref(false)
const analyzing = ref(false)

// 灵犀分析结果
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

const form = reactive({
  name: '',
  gender: '',
  age: null as number | null,
  phone: '',
  email: '',
  current_city: '',
  intention_cities: '',
  education: '',
  school: '',
  major: '',
  work_years: null as number | null,
  expected_salary_min: null as number | null,
  expected_salary_max: null as number | null,
  self_evaluation: '',
  skills: [] as Array<{ skill_name: string; skill_level: string; weight: number }>,
})

// 意向城市：数组 ↔ 逗号分隔字符串
const intentionCitiesText = computed({
  get: () => {
    try {
      const arr = JSON.parse(form.intention_cities || '[]')
      return Array.isArray(arr) ? arr.join(',') : ''
    } catch {
      return form.intention_cities || ''
    }
  },
  set: (val: string) => {
    const arr = val.split(/[,，]/).map(s => s.trim()).filter(Boolean)
    form.intention_cities = JSON.stringify(arr)
  },
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
}

const addSkill = () => {
  form.skills.push({ skill_name: '', skill_level: '了解', weight: 0.5 })
}

const removeSkill = (index: number) => {
  form.skills.splice(index, 1)
}

const fetchDetail = async () => {
  loading.value = true
  try {
    const res: any = await resumeApi.detail(resumeId)
    const data = res.data || {}
    Object.assign(form, {
      name: data.name || '',
      gender: data.gender || '',
      age: data.age || null,
      phone: data.phone || '',
      email: data.email || '',
      current_city: data.current_city || '',
      intention_cities: data.intention_cities || '[]',
      education: data.education || '',
      school: data.school || '',
      major: data.major || '',
      work_years: data.work_years || null,
      expected_salary_min: data.expected_salary_min || null,
      expected_salary_max: data.expected_salary_max || null,
      self_evaluation: data.self_evaluation || '',
      skills: (data.skills || []).map((s: any) => ({
        skill_name: s.skill_name,
        skill_level: s.skill_level || '了解',
        weight: s.weight || 0.5,
      })),
    })

    // 检查是否有从上传页传递过来的灵犀建议
    await loadAcceptedGaps()
    // 检查是否有完整的灵犀分析结果 (从上传页跳转过来时展示)
    await loadGapResultFromCache()
  } catch (e: any) {
    ElMessage.error(e?.message || '加载简历详情失败')
    router.back()
  } finally {
    loading.value = false
  }
}

// 从 sessionStorage 加载从上传页采纳的建议, 自动应用到表单
const loadAcceptedGaps = async () => {
  try {
    const cached = sessionStorage.getItem('resume_accepted_gaps')
    if (!cached) return
    const gaps: GapItem[] = JSON.parse(cached)
    if (!gaps || !gaps.length) return

    let appliedCount = 0
    for (const gap of gaps) {
      if (gap.action_type === 'skill' && gap.suggested_value) {
        const sv = gap.suggested_value
        const exists = form.skills.some(s => s.skill_name === sv.skill_name)
        if (!exists) {
          form.skills.push({
            skill_name: sv.skill_name || '',
            skill_level: sv.skill_level || '掌握',
            weight: 0.6,
          })
          appliedCount++
        }
      } else if (gap.action_type === 'text' && gap.suggested_value) {
        const field = gap.suggested_value.field
        const value = gap.suggested_value.value
        if (field && field in form) {
          ;(form as any)[field] = value
          appliedCount++
        }
      } else if (gap.action_type === 'number' && gap.suggested_value) {
        const field = gap.suggested_value.field
        const value = gap.suggested_value.value
        if (field && field in form) {
          ;(form as any)[field] = value
          appliedCount++
        }
      }
    }

    if (appliedCount > 0) {
      ElMessage.success(`已自动应用 ${appliedCount} 条灵犀建议, 请确认后保存`)
    }
    // 清除缓存, 避免重复应用
    sessionStorage.removeItem('resume_accepted_gaps')
  } catch (e) {
    // 静默
  }
}

// 从 sessionStorage 加载完整的灵犀分析结果 (从上传页跳转过来时展示)
const loadGapResultFromCache = async () => {
  try {
    const cached = sessionStorage.getItem('resume_upload_gap_result')
    if (!cached) return
    const data = JSON.parse(cached)
    if (data && data.gaps && data.gaps.length > 0) {
      gapResult.value = data
    }
  } catch (e) {
    // 静默
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      await resumeApi.update(resumeId, form)
      ElMessage.success('简历更新成功')
      router.push('/seeker/resume/list')
    } catch (e: any) {
      ElMessage.error(e?.message || '更新失败')
    } finally {
      saving.value = false
    }
  })
}

// ===== 灵犀智能分析 =====
const runGapAnalysis = async () => {
  analyzing.value = true
  gapResult.value = null
  try {
    const res: any = await resumeApi.gapAnalysis(resumeId)
    const data = res.data || {}
    if (data.gaps && data.gaps.length > 0) {
      gapResult.value = data
      ElMessage.success(`灵犀分析完成, 发现 ${data.gaps.length} 条改进建议`)
    } else {
      ElMessage.success('灵犀分析完成, 您的简历已经很完善了!')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '灵犀分析失败, 请稍后重试')
  } finally {
    analyzing.value = false
  }
}

const priorityLabel = (p: string) => {
  const map: Record<string, string> = { high: '重要', medium: '建议', low: '可选' }
  return map[p] || p
}

const priorityTagType = (p: string) => {
  const map: Record<string, string> = { high: 'danger', medium: 'warning', low: 'info' }
  return (map[p] || 'info') as any
}

const scoreRingStyle = computed(() => {
  const score = gapResult.value?.overall_score ?? 0
  const color = score >= 80 ? '#52c41a' : score >= 60 ? '#1677ff' : score >= 40 ? '#faad14' : '#ff4d4f'
  const deg = (score / 100) * 360
  return {
    background: `conic-gradient(${color} ${deg}deg, rgba(0,0,0,0.06) ${deg}deg)`,
  }
})

// 一键采纳建议
const applySuggestion = (gap: GapItem) => {
  if (gap.action_type === 'skill' && gap.suggested_value) {
    const sv = gap.suggested_value
    // 检查是否已存在该技能
    const exists = form.skills.some(s => s.skill_name === sv.skill_name)
    if (exists) {
      ElMessage.info(`技能 "${sv.skill_name}" 已存在`)
      return
    }
    form.skills.push({
      skill_name: sv.skill_name || '',
      skill_level: sv.skill_level || '掌握',
      weight: 0.6,
    })
    ElMessage.success(`已添加技能: ${sv.skill_name}`)
  } else if (gap.action_type === 'text' && gap.suggested_value) {
    const field = gap.suggested_value.field
    const value = gap.suggested_value.value
    if (field && field in form) {
      ;(form as any)[field] = value
      ElMessage.success(`已填充: ${field}`)
    }
  } else if (gap.action_type === 'number' && gap.suggested_value) {
    const field = gap.suggested_value.field
    const value = gap.suggested_value.value
    if (field && field in form) {
      ;(form as any)[field] = value
      ElMessage.success(`已设置: ${field}`)
    }
  } else {
    ElMessage.info('该建议需要手动修改')
  }
}

onMounted(fetchDetail)
</script>

<style scoped>
.edit-page {
  max-width: 900px;
  margin: 0 auto;
}
.edit-card {
  border-radius: 12px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.skills-section {
  padding: 10px 0;
}
.skill-item {
  margin-bottom: 10px;
  padding: 10px;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
}

/* ===== 灵犀分析面板 ===== */
.gap-panel {
  margin-bottom: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
  background: linear-gradient(135deg, #fafbff 0%, #f5f3ff 100%);
}
.gap-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 20px 24px 12px;
}
.gap-score {
  display: flex;
  align-items: center;
  gap: 16px;
}
.score-ring {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.score-ring::before {
  content: '';
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: #fff;
  position: absolute;
}
.score-ring {
  position: relative;
}
.score-num {
  position: relative;
  z-index: 1;
  font-size: 20px;
  font-weight: 700;
  color: #333;
}
.score-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.score-label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}
.score-summary {
  font-size: 13px;
  color: #666;
  max-width: 400px;
}

.gap-list {
  padding: 0 24px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.gap-item {
  padding: 14px 16px;
  border-radius: 10px;
  background: #fff;
  border-left: 4px solid #d9d9d9;
  transition: box-shadow 0.2s;
}
.gap-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}
.gap-item.priority-high {
  border-left-color: #ff4d4f;
}
.gap-item.priority-medium {
  border-left-color: #faad14;
}
.gap-item.priority-low {
  border-left-color: #1677ff;
}
.gap-item-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.gap-category {
  font-size: 12px;
  color: #999;
}
.gap-title {
  font-size: 14px;
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}
.gap-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.6;
  margin-bottom: 8px;
}
.gap-actions {
  display: flex;
  gap: 8px;
}
</style>
