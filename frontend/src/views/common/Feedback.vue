<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ChatLineSquare, Promotion, Warning, MagicStick, MoreFilled } from '@element-plus/icons-vue'
import { feedbackApi } from '@/api/feedback'

const formRef = ref<FormInstance>()
const submitting = ref(false)
const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)

const stats = ref({ total: 0, pending: 0, processing: 0, resolved: 0 })

const form = reactive({
  type: 'feature',
  title: '',
  content: '',
})

const rules: FormRules = {
  title: [{ required: true, message: '请输入反馈标题', trigger: 'blur' }],
  content: [{ required: true, message: '请输入反馈内容', trigger: 'blur' }],
}

const typeOptions = [
  { label: '功能建议', value: 'feature', icon: MagicStick, color: '#1677ff' },
  { label: 'Bug 报告', value: 'bug', icon: Warning, color: '#f56c6c' },
  { label: '其他', value: 'other', icon: MoreFilled, color: '#909399' },
]

const statusTag = (s: string) => {
  const m: Record<string, string> = { pending: 'warning', processing: 'primary', resolved: 'success' }
  return m[s] || 'info'
}

const typeIcon = (t: string) => {
  const m: Record<string, any> = { bug: Warning, feature: MagicStick, other: MoreFilled }
  return m[t] || MoreFilled
}

const typeColor = (t: string) => {
  const m: Record<string, string> = { bug: '#f56c6c', feature: '#1677ff', other: '#909399' }
  return m[t] || '#909399'
}

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await feedbackApi.my({ page: page.value, size: 10 })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res: any = await feedbackApi.myStats()
    stats.value = res.data || { total: 0, pending: 0, processing: 0, resolved: 0 }
  } catch {}
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await feedbackApi.create({ ...form })
    ElMessage.success('反馈提交成功，感谢您的意见！')
    form.title = ''
    form.content = ''
    page.value = 1
    await Promise.all([fetchList(), fetchStats()])
  } finally {
    submitting.value = false
  }
}

onMounted(() => {
  fetchList()
  fetchStats()
})
</script>

<template>
  <div class="feedback-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#1677ff"><ChatLineSquare /></el-icon>
        <span class="page-title">意见反馈</span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="16" class="stats-row">
      <el-col :span="6">
        <div class="stat-card stat-total">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">总反馈数</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-pending">
          <div class="stat-value">{{ stats.pending }}</div>
          <div class="stat-label">待处理</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-processing">
          <div class="stat-value">{{ stats.processing }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </el-col>
      <el-col :span="6">
        <div class="stat-card stat-resolved">
          <div class="stat-value">{{ stats.resolved }}</div>
          <div class="stat-label">已解决</div>
        </div>
      </el-col>
    </el-row>

    <!-- 提交表单 -->
    <el-card class="form-card" shadow="never">
      <template #header>
        <span>提交新反馈</span>
      </template>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="反馈类型">
          <el-radio-group v-model="form.type">
            <el-radio-button v-for="o in typeOptions" :key="o.value" :value="o.value">
              {{ o.label }}
            </el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标题" prop="title">
          <el-input v-model="form.title" placeholder="请简要描述您的问题或建议" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="详细内容" prop="content">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="4"
            placeholder="请详细描述您的反馈内容"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">提交</el-button>
          <el-button @click="form.title = ''; form.content = ''">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 反馈列表 -->
    <el-card class="list-card" shadow="never" v-loading="loading">
      <template #header>
        <span>我的反馈历史 ({{ total }})</span>
      </template>
      <el-empty v-if="!loading && !list.length" description="暂无反馈记录" />
      <div v-else class="feedback-list">
        <el-card
          v-for="item in list"
          :key="item.id"
          class="feedback-item"
          shadow="hover"
          :body-style="{ padding: '16px' }"
        >
          <div class="item-header">
            <div class="item-title-row">
              <el-icon :size="16" :color="typeColor(item.type)"><component :is="typeIcon(item.type)" /></el-icon>
              <span class="item-type">{{ item.type_label }}</span>
              <span class="item-title">{{ item.title }}</span>
              <el-tag :type="statusTag(item.status)" size="small" effect="plain">{{ item.status_label }}</el-tag>
            </div>
            <span class="item-time">{{ item.created_at?.split('T')[0] }}</span>
          </div>
          <div class="item-content">{{ item.content }}</div>
          <div v-if="item.admin_reply" class="item-reply">
            <el-icon :size="14" color="#1677ff"><Promotion /></el-icon>
            <span class="reply-label">管理员回复：</span>
            <span>{{ item.admin_reply }}</span>
          </div>
        </el-card>
      </div>
      <el-pagination
        v-if="total > 10"
        class="list-pagination"
        v-model:current-page="page"
        :page-size="10"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchList"
      />
    </el-card>
  </div>
</template>

<style scoped>
.feedback-page { max-width: 960px; margin: 0 auto; }
.page-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.header-left { display: flex; align-items: center; gap: 8px; }
.page-title { font-size: 18px; font-weight: 600; }

/* 统计卡片 */
.stats-row { margin-bottom: 16px; }
.stat-card {
  padding: 20px 16px; border-radius: 12px; text-align: center;
  background: #fff; border: 1px solid var(--border-color);
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.stat-value { font-size: 28px; font-weight: 700; line-height: 1.2; }
.stat-label { font-size: 13px; color: #909399; margin-top: 4px; }
.stat-total .stat-value { color: #303133; }
.stat-pending .stat-value { color: #e6a23c; }
.stat-processing .stat-value { color: #1677ff; }
.stat-resolved .stat-value { color: #67c23a; }

/* 表单 */
.form-card { margin-bottom: 16px; }

/* 反馈列表 */
.list-card { margin-bottom: 16px; }
.feedback-list { display: flex; flex-direction: column; gap: 12px; }
.feedback-item { border-radius: 10px; transition: border-color 0.2s; }
.feedback-item:hover { border-color: #1677ff; }
.item-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
}
.item-title-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.item-type { font-size: 12px; font-weight: 500; }
.item-title { font-weight: 600; font-size: 14px; }
.item-time { font-size: 12px; color: var(--text-secondary); white-space: nowrap; }
.item-content { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; line-height: 1.6; }
.item-reply {
  display: flex; align-items: flex-start; gap: 4px; padding: 10px 12px;
  background: #f0f5ff; border-radius: 8px; font-size: 13px; color: #1677ff;
}
.reply-label { font-weight: 500; white-space: nowrap; }
.list-pagination { margin-top: 16px; display: flex; justify-content: center; }
</style>
