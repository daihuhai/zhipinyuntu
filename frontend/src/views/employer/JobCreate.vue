<!--
  发布职位 (企业) - Tab 切换: JD文档上传 / 文本粘贴解析 / 灵犀AI智能生成
-->
<template>
  <div class="job-create-page">
    <el-card shadow="never" class="form-card">
      <template #header>
        <div class="card-header">
          <span>发布新职位</span>
          <el-tag type="success" size="small" effect="plain">支持 PDF / DOC / DOCX</el-tag>
        </div>
      </template>

      <!-- ====== 方式选择 Tab ====== -->
      <el-tabs v-model="activeTab" class="source-tabs">
        <!-- ====== Tab 1: JD 文件上传 ====== -->
        <el-tab-pane label="JD 文件上传" name="upload">
          <el-upload
            ref="uploadRef"
            class="jd-upload"
            :class="{ 'jd-uploaded': !!jdFilename && !uploading }"
            drag
            :auto-upload="true"
            :show-file-list="false"
            :http-request="handleUpload"
            accept=".pdf,.doc,.docx"
            :disabled="uploading"
          >
            <template v-if="jdFilename && !uploading">
              <el-icon class="el-icon--upload uploaded-icon"><DocumentChecked /></el-icon>
              <div class="el-upload__text">
                <span class="uploaded-filename">{{ jdFilename }}</span>
              </div>
              <div class="el-upload__sub-text">已上传并解析完成, 点击可重新上传</div>
            </template>
            <template v-else>
              <el-icon class="el-icon--upload" :class="{ rotating: uploading }">
                <Loading v-if="uploading" />
                <UploadFilled v-else />
              </el-icon>
              <div class="el-upload__text">
                {{ uploading ? '正在上传并灵犀解析中...' : '拖拽 JD 文件到此处, 或' }}
                <em v-if="!uploading">点击上传</em>
              </div>
            </template>
            <template #tip>
              <div class="el-upload__tip">
                支持 .pdf / .doc / .docx 格式, 文件不超过 10MB, 上传后自动灵犀解析填充表单
              </div>
            </template>
          </el-upload>

          <div v-if="uploading" class="jd-status parsing">
            <el-icon class="rotating"><Loading /></el-icon>
            <span>正在上传并调用灵犀大模型解析 JD, 请耐心等待 (预计 1-3 分钟)...</span>
          </div>
          <div v-else-if="jdFilename" class="jd-status success">
            <el-icon><Check /></el-icon>
            <span>{{ jdFilename }} 解析完成, 表单已自动填充 (可编辑修改)</span>
            <el-button link type="danger" @click="clearJD">清除</el-button>
          </div>
        </el-tab-pane>

        <!-- ====== Tab 2: JD 文本粘贴 ====== -->
        <el-tab-pane label="JD 文本粘贴" name="text">
          <el-input
            v-model="form.parse_text"
            type="textarea"
            :rows="8"
            placeholder="粘贴职位描述文本, 点击下方按钮灵犀解析后自动填充表单"
          />
          <el-button
            type="primary"
            :icon="MagicStick"
            :loading="parsingText"
            :disabled="!form.parse_text?.trim()"
            class="parse-text-btn"
            @click="handleParseText"
          >
            {{ parsingText ? '灵犀推理中 (约1-3分钟)...' : '灵犀解析文本' }}
          </el-button>
          <div class="field-hint" style="margin-top: 6px">
            提示: 粘贴 JD 文本后点击"灵犀解析文本"可预览解析结果 (约需 1-3 分钟)
          </div>
        </el-tab-pane>

        <!-- ====== Tab 3: 灵犀AI智能生成 ====== -->
        <el-tab-pane label="灵犀AI智能生成" name="ai">
          <div class="ai-gen-form">
            <el-row :gutter="12">
              <el-col :span="8">
                <div class="gen-field">
                  <span class="gen-label"><span class="gen-required">*</span>岗位名称</span>
                  <el-input v-model="genForm.title" placeholder="如: 高级Java开发工程师" />
                </div>
              </el-col>
              <el-col :span="8">
                <div class="gen-field">
                  <span class="gen-label">级别</span>
                  <el-select v-model="genForm.level" placeholder="选择级别" style="width: 100%">
                    <el-option label="初级" value="初级" />
                    <el-option label="中级" value="中级" />
                    <el-option label="高级" value="高级" />
                    <el-option label="专家" value="专家" />
                  </el-select>
                </div>
              </el-col>
              <el-col :span="8">
                <div class="gen-field">
                  <span class="gen-label">核心技能</span>
                  <el-input v-model="genForm.skills" placeholder="如: Java, Spring Boot, MySQL" />
                </div>
              </el-col>
            </el-row>
            <el-row :gutter="12" style="margin-top: 10px">
              <el-col :span="16">
                <div class="gen-field">
                  <span class="gen-label">其他要求 (可选)</span>
                  <el-input v-model="genForm.extra" placeholder="如: 需要分布式系统经验" />
                </div>
              </el-col>
              <el-col :span="8" class="gen-btn-col">
                <el-button
                  type="primary"
                  :icon="MagicStick"
                  :loading="generating"
                  class="gen-btn"
                  @click="handleGenerate"
                >
                  {{ generating ? '灵犀AI生成中...' : '灵犀AI生成' }}
                </el-button>
              </el-col>
            </el-row>
            <div class="field-hint" style="margin-top: 6px">
              提示: 输入岗位名称 + 级别 + 核心技能, 由灵犀大模型智能生成岗位职责、技能要求和加分项 (约需 1-3 分钟)
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>

      <!-- ====== 解析/生成结果摘要 (三种方式共用) ====== -->
      <div v-if="parsedSummary" class="parsed-summary">
        <div class="summary-header">
          <el-icon><MagicStick /></el-icon>
          <span class="summary-title">{{ resultSourceLabel }}</span>
          <el-tag size="small" type="success" effect="plain">{{ parsedSummary.filledCount }} 个字段</el-tag>
        </div>
        <div class="summary-fields">
          <div v-for="field in parsedSummary.fields" :key="field.key" class="summary-field" :class="{ 'field-empty': !field.value }">
            <span class="field-label">{{ field.label }}</span>
            <span class="field-value" v-if="field.value">{{ field.value }}</span>
            <span class="field-missing" v-else>未识别</span>
          </div>
        </div>
      </div>

      <!-- 解析出的技能要求预览 -->
      <div v-if="parsedRequirements.length" class="parsed-skills">
        <div class="skills-title">技能要求 (发布时自动写入):</div>
        <div class="skills-tags">
          <el-tag
            v-for="(req, idx) in parsedRequirements"
            :key="idx"
            :type="req.req_type === '必须' ? 'danger' : 'warning'"
            effect="light"
            class="skill-tag"
          >
            {{ req.skill_name || req.name }}
            <span class="skill-level" v-if="req.skill_level"> · {{ req.skill_level }}</span>
          </el-tag>
        </div>
      </div>

      <!-- AI生成加分项 -->
      <div v-if="genResult?.bonus" class="gen-bonus-preview">
        <span class="gen-bonus-label">加分项:</span>
        <span class="gen-bonus-text">{{ genResult.bonus }}</span>
      </div>

      <!-- ====== 职位基本信息表单 ====== -->
      <el-divider>职位基本信息</el-divider>

      <el-form :model="form" label-width="100px" size="large">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="职位名称" required>
              <el-input v-model="form.title" placeholder="如: 高级 Java 开发工程师" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="公司名称">
              <el-input v-model="form.company" placeholder="可选" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="工作城市">
              <el-input v-model="form.work_city" placeholder="如: 北京" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="经验要求">
              <el-input v-model="form.experience_required" placeholder="如: 3-5年" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="学历要求">
              <el-select v-model="form.education_required" placeholder="选择学历要求" style="width: 100%">
                <el-option label="不限" value="不限" />
                <el-option label="专科及以上" value="专科及以上" />
                <el-option label="本科及以上" value="本科及以上" />
                <el-option label="硕士及以上" value="硕士及以上" />
                <el-option label="博士及以上" value="博士及以上" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="8">
            <el-form-item label="薪资下限">
              <el-input-number
                v-model="form.salary_min"
                :min="0"
                :max="99999"
                :step="500"
                controls-position="right"
                style="width: 100%"
              >
                <template #suffix>元</template>
              </el-input-number>
              <div class="field-hint">月薪 3000 元填 3000, 展示为 3K</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="薪资上限">
              <el-input-number
                v-model="form.salary_max"
                :min="0"
                :max="99999"
                :step="500"
                controls-position="right"
                style="width: 100%"
              >
                <template #suffix>元</template>
              </el-input-number>
              <div class="field-hint">月薪 5000 元填 5000, 展示为 5K</div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="招聘人数">
              <el-input-number v-model="form.headcount" :min="1" :max="999" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="职位描述">
          <el-input v-model="form.description" type="textarea" :rows="5" placeholder="详细职位描述" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="submitting" :icon="Check" @click="submit">立即发布</el-button>
          <el-button @click="reset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled, Check, Loading, MagicStick, DocumentChecked } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { useDraft } from '@/composables/useDraft'

const router = useRouter()

const submitting = ref(false)
const uploading = ref(false)
const parsingText = ref(false)
const generating = ref(false)
const jdFilename = ref('')
const parsedRequirements = ref<any[]>([])
const parsedSummary = ref<any>(null)
const genResult = ref<any>(null)
const uploadRef = ref<any>(null)
const activeTab = ref('upload')

const form = reactive<any>({
  parse_text: '',
  title: '',
  company: '',
  work_city: '',
  experience_required: '',
  education_required: '',
  salary_min: undefined,
  salary_max: undefined,
  headcount: 1,
  description: '',
  job_type: '全职',
})

// 灵犀AI智能生成表单
const genForm = reactive({
  title: '',
  level: '中级',
  skills: '',
  extra: '',
})

// 草稿是否包含有效内容 (避免空表单也触发草稿恢复)
const hasDraftContent = () => {
  return !!(
    form.title?.trim() || form.company?.trim() || form.work_city?.trim() ||
    form.experience_required?.trim() || form.education_required?.trim() ||
    form.description?.trim() || form.parse_text?.trim() ||
    (form.salary_min != null && form.salary_min > 0) ||
    (form.salary_max != null && form.salary_max > 0) ||
    parsedRequirements.value.length || parsedSummary.value ||
    genForm.title?.trim() || genForm.skills?.trim() || genForm.extra?.trim()
  )
}

const { draftKey, loadDraft, startAutoSave, clearDraft } = useDraft(
  'job-create:new',
  () => ({
    form: { ...form },
    parsedRequirements: parsedRequirements.value,
    parsedSummary: parsedSummary.value,
    genForm: { ...genForm },
  }),
  { shouldSave: hasDraftContent }
)

// 恢复草稿提示 (仅当草稿含有效内容时)
const draft = loadDraft()
const draftTextFields = ['title', 'company', 'work_city', 'experience_required', 'education_required', 'description', 'parse_text']
const draftHasContent = !!draft && (
  (draft.form && draftTextFields.some((k) => String(draft.form[k] ?? '').trim())) ||
  (draft.form && ((draft.form.salary_min != null && draft.form.salary_min > 0) || (draft.form.salary_max != null && draft.form.salary_max > 0))) ||
  (Array.isArray(draft.parsedRequirements) && draft.parsedRequirements.length) ||
  !!draft.parsedSummary || (draft.genForm && (String(draft.genForm.title ?? '').trim() || String(draft.genForm.skills ?? '').trim() || String(draft.genForm.extra ?? '').trim()))
)
if (draftHasContent) {
  ElMessageBox.confirm(
    '检测到未发布的职位草稿，是否恢复上次填写内容？',
    '草稿恢复',
    { confirmButtonText: '恢复', cancelButtonText: '清空' }
  ).then(() => {
    // 恢复草稿数据
    Object.assign(form, draft.form || {})
    if (Array.isArray(draft.parsedRequirements)) {
      parsedRequirements.value = draft.parsedRequirements
    }
    if (draft.parsedSummary) {
      parsedSummary.value = draft.parsedSummary
    }
    if (draft.genForm) {
      Object.assign(genForm, draft.genForm)
    }
    ElMessage.success('草稿已恢复')
  }).catch(() => {
    clearDraft()
  })
}

// 表单变化自动保存草稿 (空表单不保存并清除旧草稿)
watch([() => form, () => parsedRequirements, () => parsedSummary, () => genForm], () => {
  if (hasDraftContent()) {
    startAutoSave()
  } else {
    clearDraft()
  }
}, { deep: true })

const resultSourceLabel = computed(() => {
  if (activeTab.value === 'ai') return '灵犀AI生成结果'
  return '灵犀智能解析结果'
})

// 自定义上传: 调用 /jobs/upload-jd 接口
const handleUpload = async (options: any) => {
  const file = options.file as File
  if (!file) return

  const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (!['.pdf', '.doc', '.docx'].includes(ext)) {
    ElMessage.error('仅支持 PDF / DOC / DOCX 格式')
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('文件大小不能超过 10MB')
    return
  }

  uploading.value = true
  try {
    const res: any = await jobApi.uploadJD(file)
    const data = res.data || {}
    const parsed = data.parsed || {}
    applyParsed(parsed, true)
    buildParsedSummary(parsed)
    if (data.raw_text) form.parse_text = data.raw_text
    jdFilename.value = data.filename || file.name
    const filledCount = countParsedFields(parsed)
    if (filledCount === 0) {
      ElMessage.warning('JD 文件已上传, 但灵犀未能解析出有效字段, 请手动填写')
    } else {
      ElMessage.success(`灵犀解析完成, 已识别 ${filledCount} 个字段, ${parsedRequirements.value.length} 项技能要求`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || 'JD 文件上传解析失败')
  } finally {
    uploading.value = false
  }
}

const countParsedFields = (parsed: any): number => {
  let count = 0
  const fields = ['title', 'company', 'work_city', 'experience_required',
    'education_required', 'description', 'job_type']
  fields.forEach(f => { if (parsed[f]) count++ })
  if (parsed.salary_min != null) count++
  if (parsed.salary_max != null) count++
  if (parsed.headcount != null) count++
  if (parsed.requirements?.length) count++
  return count
}

const buildParsedSummary = (parsed: any) => {
  const fields = [
    { key: 'title', label: '职位名称', value: parsed.title || '' },
    { key: 'company', label: '公司', value: parsed.company || '' },
    { key: 'work_city', label: '城市', value: parsed.work_city || '' },
    { key: 'experience_required', label: '经验', value: parsed.experience_required || '' },
    { key: 'education_required', label: '学历', value: parsed.education_required || '' },
    { key: 'salary', label: '薪资', value: parsed.salary_min != null ? `${parsed.salary_min}-${parsed.salary_max}K` : '' },
    { key: 'headcount', label: '人数', value: parsed.headcount != null ? `${parsed.headcount}人` : '' },
    { key: 'job_type', label: '性质', value: parsed.job_type || '' },
    { key: 'description', label: '描述', value: parsed.description ? `${parsed.description.slice(0, 30)}...` : '' },
  ]
  const filledCount = fields.filter(f => f.value).length
  parsedSummary.value = { fields, filledCount }
}

const applyParsed = (parsed: any, overwrite: boolean = false) => {
  const fields = ['title', 'company', 'work_city', 'experience_required',
    'education_required', 'description', 'job_type']
  fields.forEach(f => {
    if (parsed[f]) {
      if (overwrite || !form[f]) form[f] = parsed[f]
    }
  })
  if (parsed.salary_min != null && (overwrite || form.salary_min == null)) {
    form.salary_min = parsed.salary_min * 1000
  }
  if (parsed.salary_max != null && (overwrite || form.salary_max == null)) {
    form.salary_max = parsed.salary_max * 1000
  }
  if (parsed.headcount != null && (overwrite || form.headcount === 1)) {
    form.headcount = parsed.headcount
  }
  parsedRequirements.value = parsed.requirements || []
}

// 解析 JD 纯文本
const handleParseText = async () => {
  const text = (form.parse_text || '').trim()
  if (!text) {
    ElMessage.warning('请先粘贴 JD 文本')
    return
  }
  parsingText.value = true
  try {
    const res: any = await jobApi.parseJDText(text)
    const data = res.data || {}
    const parsed = data.parsed || {}
    applyParsed(parsed, true)
    buildParsedSummary(parsed)
    const filledCount = countParsedFields(parsed)
    if (filledCount === 0) {
      ElMessage.warning('灵犀未能从文本中解析出有效字段, 请手动填写')
    } else {
      ElMessage.success(`灵犀解析完成, 已识别 ${filledCount} 个字段, ${parsedRequirements.value.length} 项技能要求`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || 'JD 文本解析失败')
  } finally {
    parsingText.value = false
  }
}

// 灵犀AI智能生成 — 自动填充所有基本信息
const handleGenerate = async () => {
  if (!genForm.title.trim()) {
    ElMessage.warning('请输入岗位名称')
    return
  }
  generating.value = true
  try {
    const res: any = await jobApi.generateDescription({
      title: genForm.title.trim(),
      level: genForm.level,
      skills: genForm.skills.trim(),
      extra: genForm.extra.trim(),
    })
    const data = res.data || {}

    // 1. 填充职位基本信息 (与文件上传/文本解析一致, 自动回填表单)
    if (data.title) form.title = data.title
    if (data.company) form.company = data.company
    if (data.work_city) form.work_city = data.work_city
    if (data.experience_required) form.experience_required = data.experience_required
    if (data.education_required) form.education_required = data.education_required
    if (data.job_type) form.job_type = data.job_type
    if (data.salary_min != null) form.salary_min = data.salary_min * 1000
    if (data.salary_max != null) form.salary_max = data.salary_max * 1000
    if (data.headcount != null) form.headcount = data.headcount
    // 2. 填充职位描述
    if (data.description) form.description = data.description
    // 3. 填充技能要求
    if (data.requirements?.length) parsedRequirements.value = data.requirements
    // 4. 存储生成结果 (含加分项)
    genResult.value = {
      description: data.description || '',
      requirements: data.requirements || [],
      bonus: data.bonus || '',
    }
    // 5. 构建摘要展示
    buildParsedSummary({
      title: data.title,
      company: data.company,
      work_city: data.work_city,
      experience_required: data.experience_required,
      education_required: data.education_required,
      salary_min: data.salary_min,
      salary_max: data.salary_max,
      headcount: data.headcount,
      job_type: data.job_type,
      description: data.description,
      requirements: data.requirements,
    })
    ElMessage.success('灵犀AI生成完成，已自动填充职位基本信息和技能要求')
  } catch (e: any) {
    ElMessage.error(e?.message || '灵犀AI生成失败')
  } finally {
    generating.value = false
  }
}

const clearJD = () => {
  jdFilename.value = ''
  parsedRequirements.value = []
  parsedSummary.value = null
  uploadRef.value?.clearFiles()
}

const submit = async () => {
  if (!form.title?.trim() && form.parse_text?.trim()) {
    ElMessage.info('检测到 JD 文本未解析, 正在自动解析...')
    parsingText.value = true
    try {
      const res: any = await jobApi.parseJDText(form.parse_text)
      const data = res.data || {}
      applyParsed(data.parsed || {}, true)
    } catch (e: any) {
      ElMessage.error(e?.message || 'JD 文本解析失败, 请手动填写或重试')
      parsingText.value = false
      return
    } finally {
      parsingText.value = false
    }
  }
  if (!form.title?.trim()) {
    ElMessage.warning('请输入职位名称, 或粘贴 JD 文本后自动解析')
    return
  }
  if (form.salary_min != null && form.salary_max != null && form.salary_min > form.salary_max) {
    ElMessage.warning('薪资上限不能低于薪资下限')
    return
  }
  submitting.value = true
  try {
    const payload = { ...form }
    if (payload.title?.trim()) {
      delete payload.parse_text
    }
    if (payload.salary_min != null) payload.salary_min = Math.round(payload.salary_min / 1000)
    if (payload.salary_max != null) payload.salary_max = Math.round(payload.salary_max / 1000)
    await jobApi.create(payload)
    ElMessage.success('职位已发布')
    clearDraft()
    router.push('/employer/job/list')
  } finally {
    submitting.value = false
  }
}

const reset = () => {
  Object.assign(form, {
    parse_text: '', title: '', company: '', work_city: '',
    experience_required: '', education_required: '',
    salary_min: undefined, salary_max: undefined,
    headcount: 1, description: '', job_type: '全职',
  })
  Object.assign(genForm, { title: '', level: '中级', skills: '', extra: '' })
  clearJD()
  genResult.value = null
  parsedSummary.value = null
  parsedRequirements.value = []
}
</script>

<style scoped>
.job-create-page { max-width: 900px; margin: 0 auto; }
.form-card { border-radius: 12px; }
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}

/* Tab 样式 */
.source-tabs {
  margin-bottom: 16px;
}
.source-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}
.source-tabs :deep(.el-tabs__item) {
  font-size: 15px;
  font-weight: 500;
}

/* JD 上传区 */
.jd-upload {
  width: 100%;
  margin-bottom: 12px;
}
.jd-upload :deep(.el-upload-dragger) {
  width: 100%;
  padding: 20px;
  transition: all 0.3s ease;
}
.jd-upload :deep(.el-upload) {
  width: 100%;
}
.jd-upload.jd-uploaded :deep(.el-upload-dragger) {
  border-color: #52c41a;
  background: #f6ffed;
  animation: uploadPop 0.4s ease;
}
.jd-upload .uploaded-icon {
  color: #52c41a;
  font-size: 48px;
  animation: iconBounce 0.5s ease;
}
.jd-upload .uploaded-filename {
  font-weight: 600;
  color: #389e0d;
  font-size: 15px;
  word-break: break-all;
}
.jd-upload .el-upload__sub-text {
  font-size: 12px;
  color: #999;
  margin-top: 6px;
}
@keyframes uploadPop {
  0% { transform: scale(0.98); }
  50% { transform: scale(1.01); }
  100% { transform: scale(1); }
}
@keyframes iconBounce {
  0% { transform: translateY(0); opacity: 0; }
  50% { transform: translateY(-6px); opacity: 1; }
  100% { transform: translateY(0); }
}

/* 上传状态 */
.jd-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 13px;
  margin-bottom: 12px;
}
.jd-status.parsing { background: #e6f4ff; color: #1677ff; }
.jd-status.success { background: #f6ffed; color: #52c41a; }
.jd-status .rotating { animation: rotate 1.2s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }

/* 解析/生成结果摘要 */
.parsed-summary {
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
  border: 1px solid #adc6ff;
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 16px;
  animation: summaryFadeIn 0.4s ease;
}
@keyframes summaryFadeIn {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}
.summary-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #1677ff;
}
.summary-title { font-size: 14px; flex: 1; }
.summary-fields {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}
.summary-field {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
  border: 1px solid #d6e4ff;
}
.summary-field.field-empty {
  background: rgba(255, 255, 255, 0.4);
  border-color: #e8e8e8;
}
.field-label { font-size: 11px; color: #8c8c8c; font-weight: 500; }
.field-value { font-size: 13px; color: #262626; font-weight: 500; word-break: break-all; }
.field-missing { font-size: 12px; color: #bfbfbf; font-style: italic; }

/* 技能要求 */
.parsed-skills {
  background: #fafafa;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}
.skills-title { font-size: 13px; color: #666; margin-bottom: 8px; font-weight: 500; }
.skills-tags { display: flex; flex-wrap: wrap; gap: 8px; }
.skill-tag { display: inline-flex; align-items: center; }
.skill-level { opacity: 0.7; font-size: 11px; margin-left: 2px; }

.field-hint { font-size: 11px; color: #999; margin-top: 2px; line-height: 1.4; }
.parse-text-btn { margin-top: 10px; }

/* 灵犀AI智能生成表单 */
.ai-gen-form {
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
  border: 1px solid #adc6ff;
  border-radius: 10px;
  padding: 16px;
}
.gen-field { display: flex; flex-direction: column; gap: 4px; }
.gen-label { font-size: 12px; color: #595959; font-weight: 500; }
.gen-required { color: #f5222d; margin-right: 2px; }
.gen-btn-col { display: flex; align-items: flex-end; }
.gen-btn { width: 100%; }

/* AI生成加分项 */
.gen-bonus-preview {
  margin-bottom: 16px;
  padding: 10px 14px;
  background: #f0f5ff;
  border: 1px dashed #adc6ff;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.5;
}
.gen-bonus-label { color: #1677ff; font-weight: 600; margin-right: 4px; }
.gen-bonus-text { color: #595959; word-break: break-all; }
</style>
