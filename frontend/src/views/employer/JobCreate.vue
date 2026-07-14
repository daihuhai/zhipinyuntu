<!--
  发布职位 (企业) - 支持 JD 文件上传 + 文本粘贴 + 灵犀解析
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

      <el-form :model="form" label-width="100px" size="large">
        <!-- JD 文件上传区 -->
        <el-divider content-position="left">JD 文件上传 (可选)</el-divider>

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
          <!-- 上传成功状态: 显示文件名 + 成功图标 -->
          <template v-if="jdFilename && !uploading">
            <el-icon class="el-icon--upload uploaded-icon"><DocumentChecked /></el-icon>
            <div class="el-upload__text">
              <span class="uploaded-filename">{{ jdFilename }}</span>
            </div>
            <div class="el-upload__sub-text">已上传并解析完成, 点击可重新上传</div>
          </template>
          <!-- 默认/上传中状态 -->
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

        <!-- 解析结果状态条 -->
        <div v-if="uploading" class="jd-status parsing">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>正在上传并调用灵犀大模型解析 JD, 请耐心等待 (灵犀大模型（推理）, 预计 1-3 分钟)...</span>
        </div>
        <div v-else-if="jdFilename" class="jd-status success">
          <el-icon><Check /></el-icon>
          <span>{{ jdFilename }} 解析完成, 表单已自动填充 (可编辑修改)</span>
          <el-button link type="danger" @click="clearJD">清除</el-button>
        </div>

        <!-- 灵犀解析结果摘要 -->
        <div v-if="parsedSummary" class="parsed-summary">
          <div class="summary-header">
            <el-icon><MagicStick /></el-icon>
            <span class="summary-title">灵犀智能解析结果</span>
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
          <div class="skills-title">灵犀解析出的技能要求 (发布时自动写入):</div>
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

        <el-divider content-position="left">JD 文本 (可选)</el-divider>

        <el-form-item label="JD 文本">
          <el-input
            v-model="form.parse_text"
            type="textarea"
            :rows="5"
            placeholder="粘贴职位描述文本, 点击下方按钮灵犀解析后自动填充表单; 也可直接点击立即发布自动解析"
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
            提示: 粘贴 JD 文本后点击"灵犀解析文本"可预览解析结果 (灵犀大模型（推理）, 约需 1-3 分钟); 也可直接点击"立即发布"自动解析
          </div>
        </el-form-item>

        <el-divider>职位基本信息</el-divider>

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
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled, Check, Loading, MagicStick, DocumentChecked } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'

const router = useRouter()
const submitting = ref(false)
const uploading = ref(false)
const parsingText = ref(false)
const jdFilename = ref('')
const parsedRequirements = ref<any[]>([])
const parsedSummary = ref<any>(null)
const uploadRef = ref<any>(null)

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

// 自定义上传: 调用 /jobs/upload-jd 接口
const handleUpload = async (options: any) => {
  const file = options.file as File
  if (!file) return

  // 前端校验文件类型
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
    applyParsed(parsed, true)  // overwrite=true, 强制覆盖确保表单与解析结果同步
    buildParsedSummary(parsed)  // 构建解析结果摘要
    // 填充 JD 文本
    if (data.raw_text) form.parse_text = data.raw_text
    jdFilename.value = data.filename || file.name
    // 检测解析结果是否为空
    const filledCount = countParsedFields(parsed)
    if (filledCount === 0) {
      ElMessage.warning('JD 文件已上传, 但灵犀未能解析出有效字段, 请手动填写或检查文件内容')
    } else {
      ElMessage.success(`灵犀解析完成, 已识别 ${filledCount} 个字段, ${parsedRequirements.value.length} 项技能要求`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || 'JD 文件上传解析失败')
  } finally {
    uploading.value = false
  }
}

// 统计解析结果中有效字段数 (用于判断灵犀是否返回了有意义的数据)
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

// 构建解析结果摘要 (展示灵犀解析了哪些字段)
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

// 将解析结果自动填充到表单 (灵犀解析返回的字段强制覆盖, 确保表单与解析结果同步)
const applyParsed = (parsed: any, overwrite: boolean = false) => {
  const fields = ['title', 'company', 'work_city', 'experience_required',
    'education_required', 'description', 'job_type']
  fields.forEach(f => {
    if (parsed[f]) {
      // overwrite=true 时强制覆盖; 否则仅填充空字段
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
  // 记录技能要求
  parsedRequirements.value = parsed.requirements || []
}

// 解析 JD 纯文本 (粘贴文本后点击按钮, 强制覆盖表单字段)
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
    applyParsed(parsed, true)  // overwrite=true, 强制回填
    buildParsedSummary(parsed)  // 构建解析结果摘要
    const filledCount = countParsedFields(parsed)
    if (filledCount === 0) {
      ElMessage.warning('灵犀未能从文本中解析出有效字段, 请手动填写或调整 JD 文本')
    } else {
      ElMessage.success(`灵犀解析完成, 已识别 ${filledCount} 个字段, ${parsedRequirements.value.length} 项技能要求`)
    }
  } catch (e: any) {
    ElMessage.error(e?.message || 'JD 文本解析失败')
  } finally {
    parsingText.value = false
  }
}

const clearJD = () => {
  jdFilename.value = ''
  parsedRequirements.value = []
  parsedSummary.value = null
  // 重置 el-upload 组件内部状态, 允许重新上传同一文件
  uploadRef.value?.clearFiles()
}

const submit = async () => {
  // 如果职位名称为空但 JD 文本有内容, 先自动解析填充表单
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
    // 关键优化: 已解析过的职位(有title)不传 parse_text, 避免后端重复调用灵犀解析(约160秒)
    if (payload.title?.trim()) {
      delete payload.parse_text
    }
    // 薪资从元转为 K 存储 (3000 元 → 3K)
    if (payload.salary_min != null) payload.salary_min = Math.round(payload.salary_min / 1000)
    if (payload.salary_max != null) payload.salary_max = Math.round(payload.salary_max / 1000)
    await jobApi.create(payload)
    ElMessage.success('职位已发布')
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
  clearJD()
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

/* 上传成功状态: 绿色边框 + 浅绿背景 + 弹入动画 */
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
.jd-status.parsing {
  background: #e6f4ff;
  color: #1677ff;
}
.jd-status.success {
  background: #f6ffed;
  color: #52c41a;
}
.jd-status .rotating {
  animation: rotate 1.2s linear infinite;
}
@keyframes rotate {
  to { transform: rotate(360deg); }
}

/* 灵犀解析结果摘要 */
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
.summary-title {
  font-size: 14px;
  flex: 1;
}
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
.field-label {
  font-size: 11px;
  color: #8c8c8c;
  font-weight: 500;
}
.field-value {
  font-size: 13px;
  color: #262626;
  font-weight: 500;
  word-break: break-all;
}
.field-missing {
  font-size: 12px;
  color: #bfbfbf;
  font-style: italic;
}

/* 解析出的技能要求 */
.parsed-skills {
  background: #fafafa;
  border: 1px dashed #d9d9d9;
  border-radius: 8px;
  padding: 12px 14px;
  margin-bottom: 16px;
}
.skills-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}
.skills-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.skill-tag {
  display: inline-flex;
  align-items: center;
}
.skill-level {
  opacity: 0.7;
  font-size: 11px;
  margin-left: 2px;
}
.field-hint {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
  line-height: 1.4;
}
.parse-text-btn {
  margin-top: 10px;
}
</style>
