<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, type FormInstance } from 'element-plus'
import { ChatLineSquare, Search } from '@element-plus/icons-vue'
import { feedbackApi } from '@/api/feedback'

const list = ref<any[]>([])
const loading = ref(false)
const statusFilter = ref('')
const typeFilter = ref('')
const keyword = ref('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

const stats = ref({ total: 0, pending: 0, processing: 0, resolved: 0 })

const dialogVisible = ref(false)
const currentFeedback = ref<any>(null)
const replyFormRef = ref<FormInstance>()
const replyForm = ref({ status: '', reply: '', notify: false })
const submitting = ref(false)

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '处理中', value: 'processing' },
  { label: '已解决', value: 'resolved' },
]

const typeOptions = [
  { label: '全部类型', value: '' },
  { label: 'Bug 报告', value: 'bug' },
  { label: '功能建议', value: 'feature' },
  { label: '其他', value: 'other' },
]

const typeMap: Record<string, string> = { feature: '功能建议', bug: 'Bug 报告', other: '其他' }
const roleMap: Record<string, string> = { ROLE_SEEKER: '求职者', ROLE_EMPLOYER: '企业', ROLE_ADMIN: '管理员' }

const statusTag = (s: string) => {
  const m: Record<string, string> = { pending: 'warning', processing: '', resolved: 'success' }
  return m[s] || 'info'
}

const statusLabel = (s: string) => {
  const m: Record<string, string> = { pending: '待处理', processing: '处理中', resolved: '已解决' }
  return m[s] || s
}

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await feedbackApi.adminList({
      page: page.value,
      size: size.value,
      status: statusFilter.value || undefined,
      type: typeFilter.value || undefined,
      keyword: keyword.value || undefined,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const fetchStats = async () => {
  try {
    const res: any = await feedbackApi.adminStats()
    stats.value = res.data || { total: 0, pending: 0, processing: 0, resolved: 0 }
  } catch {}
}

const handleSearch = () => {
  page.value = 1
  fetchList()
}

const openDialog = (row: any) => {
  currentFeedback.value = row
  replyForm.value = { status: row.status || '', reply: '', notify: false }
  dialogVisible.value = true
}

const handleReply = async () => {
  if (!replyForm.value.status) {
    ElMessage.warning('请选择处理状态')
    return
  }
  submitting.value = true
  try {
    await feedbackApi.adminReply(currentFeedback.value.id, {
      status: replyForm.value.status,
      reply: replyForm.value.reply || undefined,
      notify: replyForm.value.notify,
    })
    ElMessage.success('回复成功')
    dialogVisible.value = false
    await Promise.all([fetchList(), fetchStats()])
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
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
  <div class="feedbacks-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#1677ff"><ChatLineSquare /></el-icon>
        <span class="page-title">反馈管理</span>
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

    <!-- 筛选栏 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="keyword"
          placeholder="搜索标题或内容..."
          clearable
          style="width: 240px"
          @clear="handleSearch"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="typeFilter" placeholder="反馈类型" clearable style="width: 140px" @change="handleSearch">
          <el-option v-for="o in typeOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-select v-model="statusFilter" placeholder="处理状态" clearable style="width: 140px" @change="handleSearch">
          <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-button type="primary" @click="handleSearch">搜索</el-button>
        <el-button @click="keyword = ''; typeFilter = ''; statusFilter = ''; handleSearch()">重置</el-button>
      </div>
    </el-card>

    <!-- 反馈列表 -->
    <el-card shadow="never" class="list-card">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="用户" width="140">
          <template #default="{ row }">
            <span>{{ row.username }}</span>
            <el-tag size="small" type="info" style="margin-left: 4px">{{ roleMap[row.role] || row.role }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="类型" width="110">
          <template #default="{ row }">{{ typeMap[row.type] || row.type }}</template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)" size="small" effect="plain">{{ statusLabel(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="提交时间" width="160">
          <template #default="{ row }">{{ row.created_at?.split('T')[0] }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link size="small" @click="openDialog(row)">处理</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > size"
        v-model:current-page="page"
        :page-size="size"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="fetchList"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 处理弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="反馈详情"
      width="560px"
      :destroy-on-close="true"
      :close-on-click-modal="false"
    >
      <template v-if="currentFeedback">
        <div class="detail-section">
          <div class="detail-row">
            <span class="detail-label">提交用户</span>
            <span class="detail-value">
              {{ currentFeedback.username }}
              <el-tag size="small" type="info" style="margin-left: 6px">{{ roleMap[currentFeedback.role] || currentFeedback.role }}</el-tag>
            </span>
          </div>
          <div class="detail-row">
            <span class="detail-label">反馈类型</span>
            <span class="detail-value">{{ typeMap[currentFeedback.type] || currentFeedback.type }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">标题</span>
            <span class="detail-value">{{ currentFeedback.title }}</span>
          </div>
          <div class="detail-row">
            <span class="detail-label">当前状态</span>
            <el-tag :type="statusTag(currentFeedback.status)" size="small" effect="plain">{{ statusLabel(currentFeedback.status) }}</el-tag>
          </div>
          <div class="detail-row">
            <span class="detail-label">提交时间</span>
            <span class="detail-value">{{ currentFeedback.created_at }}</span>
          </div>
        </div>

        <div class="content-block">
          <div class="block-title">反馈内容</div>
          <div class="content-text">{{ currentFeedback.content }}</div>
        </div>

        <div v-if="currentFeedback.admin_reply" class="content-block reply-block">
          <div class="block-title">历史回复</div>
          <div class="content-text">{{ currentFeedback.admin_reply }}</div>
        </div>

        <el-divider />

        <div class="reply-form">
          <div class="block-title" style="margin-bottom: 12px">处理回复</div>
          <el-form ref="replyFormRef" :model="replyForm" label-width="80px">
            <el-form-item label="处理状态" required>
              <el-select v-model="replyForm.status" style="width: 100%">
                <el-option v-for="o in statusOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="回复内容">
              <el-input
                v-model="replyForm.reply"
                type="textarea"
                :rows="4"
                placeholder="输入回复内容（可选）"
                maxlength="2000"
                show-word-limit
              />
            </el-form-item>
            <el-form-item label="通知用户">
              <el-switch v-model="replyForm.notify" active-text="发送站内消息通知" />
            </el-form-item>
          </el-form>
        </div>
      </template>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleReply">确认处理</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.feedbacks-page { max-width: 1200px; margin: 0 auto; }
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

/* 筛选栏 */
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { padding: 16px; }
.filter-row { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }

/* 列表 */
.list-card { border-radius: 12px; }

/* 弹窗 */
.detail-section { margin-bottom: 16px; }
.detail-row { display: flex; align-items: center; gap: 12px; padding: 6px 0; font-size: 14px; }
.detail-label { width: 72px; color: #999; flex-shrink: 0; }
.detail-value { color: #333; }
.content-block { margin-bottom: 16px; }
.block-title { font-size: 14px; font-weight: 600; color: #333; margin-bottom: 8px; padding-left: 8px; border-left: 3px solid #1677ff; }
.content-text { font-size: 14px; color: #555; line-height: 1.7; background: #fafafa; padding: 12px; border-radius: 6px; white-space: pre-wrap; }
.reply-block { background: #f0f5ff; padding: 12px; border-radius: 8px; }
.reply-block .content-text { background: #fff; }
</style>
