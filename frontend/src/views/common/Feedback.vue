<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { ChatLineSquare, Promotion } from '@element-plus/icons-vue'
import { feedbackApi } from '@/api/feedback'

const formRef = ref<FormInstance>()
const submitting = ref(false)
const loading = ref(false)
const list = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const showForm = ref(false)

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
  { label: '功能建议', value: 'feature' },
  { label: 'Bug 报告', value: 'bug' },
  { label: '其他', value: 'other' },
]

const statusTag = (s: string) => {
  const m: Record<string, string> = { pending: 'warning', processing: 'primary', resolved: 'success' }
  return m[s] || 'info'
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

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  submitting.value = true
  try {
    await feedbackApi.create({ ...form })
    ElMessage.success('反馈提交成功，感谢您的意见！')
    form.title = ''
    form.content = ''
    showForm.value = false
    page.value = 1
    await fetchList()
  } finally {
    submitting.value = false
  }
}

onMounted(fetchList)
</script>

<template>
  <div class="feedback-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#1677ff"><ChatLineSquare /></el-icon>
        <span class="page-title">意见反馈</span>
      </div>
      <el-button type="primary" :icon="Promotion" @click="showForm = true" v-if="!showForm">
        提交反馈
      </el-button>
    </div>

    <!-- 提交表单 -->
    <el-card v-if="showForm" class="form-card" shadow="never">
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
          <el-button @click="showForm = false">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 反馈列表 -->
    <el-card class="list-card" shadow="never" v-loading="loading">
      <template #header>
        <span>我的反馈 ({{ total }})</span>
      </template>
      <el-empty v-if="!loading && !list.length" description="暂无反馈记录" />
      <div v-else class="feedback-list">
        <div v-for="item in list" :key="item.id" class="feedback-item">
          <div class="item-header">
            <div class="item-title-row">
              <span class="item-title">{{ item.title }}</span>
              <el-tag :type="statusTag(item.status)" size="small">{{ item.status_label }}</el-tag>
            </div>
            <span class="item-time">{{ item.created_at?.split('T')[0] }}</span>
          </div>
          <div class="item-content">{{ item.content }}</div>
          <div v-if="item.admin_reply" class="item-reply">
            <el-icon :size="14" color="#1677ff"><Promotion /></el-icon>
            <span class="reply-label">管理员回复：</span>
            <span>{{ item.admin_reply }}</span>
          </div>
        </div>
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
.feedback-page { max-width: 860px; margin: 0 auto; }
.page-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;
}
.header-left { display: flex; align-items: center; gap: 8px; }
.page-title { font-size: 18px; font-weight: 600; }
.form-card { margin-bottom: 16px; }
.list-card { margin-bottom: 16px; }
.feedback-list { display: flex; flex-direction: column; gap: 12px; }
.feedback-item {
  padding: 12px; border: 1px solid var(--border-color); border-radius: 8px;
  transition: border-color 0.2s;
}
.feedback-item:hover { border-color: #1677ff; }
.item-header {
  display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;
}
.item-title-row { display: flex; align-items: center; gap: 8px; }
.item-title { font-weight: 600; font-size: 14px; }
.item-time { font-size: 12px; color: var(--text-secondary); }
.item-content { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; line-height: 1.6; }
.item-reply {
  display: flex; align-items: flex-start; gap: 4px; padding: 8px 12px;
  background: #f0f5ff; border-radius: 6px; font-size: 13px; color: #1677ff;
}
.reply-label { font-weight: 500; white-space: nowrap; }
.list-pagination { margin-top: 16px; display: flex; justify-content: center; }
</style>