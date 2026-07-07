<!--
  发布职位 (企业) - 支持 JD 文件上传 + 文本粘贴 + 豆包 AI 解析
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
          drag
          :auto-upload="true"
          :show-file-list="false"
          :http-request="handleUpload"
          accept=".pdf,.doc,.docx"
          :disabled="uploading"
        >
          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
          <div class="el-upload__text">
            拖拽 JD 文件到此处, 或<em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 .pdf / .doc / .docx 格式, 文件不超过 10MB, 上传后自动 AI 解析填充表单
            </div>
          </template>
        </el-upload>

        <!-- 上传/解析状态 -->
        <div v-if="uploading" class="jd-status parsing">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>正在上传并调用 AI 解析 JD, 请稍候 (预计 5-15 秒)...</span>
        </div>
        <div v-else-if="jdFilename" class="jd-status success">
          <el-icon><Check /></el-icon>
          <span>{{ jdFilename }} 解析完成, 表单已自动填充 (可编辑修改)</span>
          <el-button link type="danger" @click="clearJD">清除</el-button>
        </div>

        <!-- 解析出的技能要求预览 -->
        <div v-if="parsedRequirements.length" class="parsed-skills">
          <div class="skills-title">AI 解析出的技能要求 (发布时自动写入):</div>
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
            placeholder="粘贴职位描述文本, 或上传文件后自动填充 (可选)"
          />
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
import { UploadFilled, Check, Loading } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'

const router = useRouter()
const submitting = ref(false)
const uploading = ref(false)
const jdFilename = ref('')
const parsedRequirements = ref<any[]>([])

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

    // 自动填充表单 (仅填充非空字段, 保留用户已输入的值)
    const fields = ['title', 'company', 'work_city', 'experience_required',
      'education_required', 'description', 'job_type']
    fields.forEach(f => {
      if (parsed[f] && !form[f]) form[f] = parsed[f]
    })
    if (parsed.salary_min != null && form.salary_min == null) form.salary_min = parsed.salary_min * 1000
    if (parsed.salary_max != null && form.salary_max == null) form.salary_max = parsed.salary_max * 1000
    if (parsed.headcount != null && form.headcount === 1) form.headcount = parsed.headcount

    // 填充 JD 文本
    if (data.raw_text) form.parse_text = data.raw_text

    // 记录技能要求
    parsedRequirements.value = parsed.requirements || []
    jdFilename.value = data.filename || file.name

    ElMessage.success(`JD 解析成功, 已填充 ${parsedRequirements.value.length} 项技能要求`)
  } catch (e: any) {
    ElMessage.error(e?.message || 'JD 文件上传解析失败')
  } finally {
    uploading.value = false
  }
}

const clearJD = () => {
  jdFilename.value = ''
  parsedRequirements.value = []
}

const submit = async () => {
  if (!form.title?.trim()) {
    ElMessage.warning('请输入职位名称')
    return
  }
  submitting.value = true
  try {
    // 薪资从元转为 K 存储 (3000 元 → 3K)
    const payload = { ...form }
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
}
.jd-upload :deep(.el-upload) {
  width: 100%;
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
</style>
