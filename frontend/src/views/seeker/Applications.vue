<!--
  投递记录 (求职者) - 查看已投递职位与状态, 可展开时间轴
-->
<template>
  <div class="app-page">
    <el-card shadow="never" class="filter-card">
      <div class="filter-bar">
        <span class="label">我的投递记录</span>
        <el-select
          v-model="statusFilter"
          placeholder="全部状态"
          clearable
          style="width: 140px"
          @change="onStatusChange"
        >
          <el-option label="已投递" :value="0" />
          <el-option label="已查看" :value="1" />
          <el-option label="面试邀请" :value="2" />
          <el-option label="不合适" :value="3" />
          <el-option label="已录用" :value="4" />
        </el-select>
        <el-tag v-if="!loading" type="info" size="small">共 {{ total }} 条</el-tag>
        <el-button :icon="Refresh" :loading="loading" @click="fetchList">刷新</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card">
      <SkeletonList v-if="loading && !list.length" :count="4" />
      <EmptyState
        v-else-if="!loading && !list.length"
        icon="tickets"
        title="暂无投递记录"
        description="你还没有投递任何职位, 去职位广场看看有没有中意的机会吧"
        action-text="去浏览职位"
        @action="$router.push('/seeker/jobs')"
      />
      <el-table v-else :data="list" stripe row-key="id" @expand-change="handleExpandChange">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="timeline-expand">
              <div v-if="timelineLoading" class="timeline-loading">
                <el-icon class="rotating"><Loading /></el-icon>
                <span>加载时间轴...</span>
              </div>
              <div v-else-if="timelineData[row.id]" class="timeline-content">
                <el-timeline>
                  <el-timeline-item
                    v-for="(node, i) in timelineData[row.id]"
                    :key="i"
                    :type="node.status === 'done' ? 'success' : node.status === 'rejected' ? 'danger' : 'info'"
                    :hollow="node.status === 'pending'"
                    :timestamp="node.time ? formatTimelineDate(node.time) : '待定'"
                    placement="top"
                  >
                    <div class="tl-title" :class="{ 'tl-done': node.status === 'done', 'tl-rejected': node.status === 'rejected', 'tl-pending': node.status === 'pending' }">
                      {{ node.title }}
                    </div>
                    <div class="tl-desc">{{ node.desc }}</div>
                    <div class="tl-actor">操作方: {{ node.actor }}</div>
                  </el-timeline-item>
                </el-timeline>
              </div>
              <div v-else class="timeline-empty">点击展开查看投递进度</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="职位" min-width="220">
          <template #default="{ row }">
            <div class="job-title" @click="$router.push(`/seeker/jobs/${row.job_id}`)">
              {{ row.job?.title || '-' }}
            </div>
            <div class="job-sub">
              {{ row.job?.company || '匿名企业' }} · {{ row.job?.work_city || '不限' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="薪资" width="120">
          <template #default="{ row }">
            {{ formatSalary(row.job?.salary_min, row.job?.salary_max) }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="投递时间" width="170">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="最近更新" width="170">
          <template #default="{ row }">{{ formatDate(row.updated_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button
                v-if="row.status === 0"
                type="danger"
                size="small"
                plain
                @click="handleWithdraw(row)"
              >撤回</el-button>
              <el-button
                v-else-if="[3, 4].includes(row.status) && !row.reviewed"
                type="warning"
                size="small"
                plain
                @click="openReviewDialog(row)"
              >评价企业</el-button>
              <el-tag v-else-if="[3, 4].includes(row.status) && row.reviewed" type="success" size="small">已评价</el-tag>
              <span v-else class="muted">-</span>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div v-if="total > pageSize" class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="fetchList"
        />
      </div>
    </el-card>

    <!-- 企业评价弹窗 -->
    <el-dialog v-model="reviewVisible" title="评价企业" width="520px" :close-on-click-modal="false">
      <div v-if="reviewTarget" class="review-dialog">
        <div class="review-company">
          <el-icon><OfficeBuilding /></el-icon>
          <span>{{ reviewTarget.job?.company || '匿名企业' }}</span>
          <el-divider direction="vertical" />
          <span class="review-job">{{ reviewTarget.job?.title }}</span>
        </div>
        <div class="review-tip">面试已结束, 请对企业本次合作体验进行评分 (匿名)</div>

        <div class="review-item">
          <div class="review-label">面试体验</div>
          <el-rate v-model="reviewForm.interview_score" :max="5" show-score />
        </div>
        <div class="review-item">
          <div class="review-label">HR 响应速度</div>
          <el-rate v-model="reviewForm.hr_score" :max="5" show-score />
        </div>
        <div class="review-item">
          <div class="review-label">职位描述准确度</div>
          <el-rate v-model="reviewForm.accuracy_score" :max="5" show-score />
        </div>
        <div class="review-item">
          <div class="review-label">文字评价 (选填)</div>
          <el-input
            v-model="reviewForm.comment"
            type="textarea"
            :rows="3"
            :maxlength="500"
            show-word-limit
            placeholder="分享您的面试体验, 帮助其他求职者参考"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="reviewVisible = false">取消</el-button>
        <el-button type="primary" :loading="reviewSubmitting" @click="submitReview">提交评价</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Loading, OfficeBuilding } from '@element-plus/icons-vue'
import { applicationApi } from '@/api/application'
import { reviewApi } from '@/api/review'
import SkeletonList from '@/components/SkeletonList.vue'
import EmptyState from '@/components/EmptyState.vue'
import { formatSalary } from '@/utils/format'

const route = useRoute()
const list = ref<any[]>([])
const loading = ref(false)
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(20)
const total = ref(0)
const statusFilter = ref<number | null>(null)

// 时间轴数据 (按 application_id 索引)
const timelineData = ref<Record<number, any[]>>({})
const timelineLoading = ref(false)

const emptyText = computed(() => {
  if (statusFilter.value !== null) {
    return `暂无「${statusText(statusFilter.value)}」记录`
  }
  return '暂无投递记录, 去看看推荐职位吧'
})

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await applicationApi.myList({
      page: page.value,
      size: pageSize.value,
      status: statusFilter.value ?? undefined,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
    timelineData.value = {}
  } catch (e: any) {
    ElMessage.error(e?.message || '加载投递记录失败')
    list.value = []
  } finally {
    loading.value = false
  }
}

// 展开行时加载时间轴
const handleExpandChange = async (row: any, expanded: any[]) => {
  if (expanded.length && !timelineData.value[row.id]) {
    timelineLoading.value = true
    try {
      const res: any = await applicationApi.timeline(row.id)
      timelineData.value[row.id] = res.data?.timeline || []
    } catch (e: any) {
      ElMessage.error(e?.message || '加载时间轴失败')
    } finally {
      timelineLoading.value = false
    }
  }
}

// 撤回投递
const handleWithdraw = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确定撤回对「${row.job?.title || '该职位'}」的投递吗?`,
      '撤回确认',
      { type: 'warning' }
    )
    await applicationApi.withdraw(row.id)
    ElMessage.success('投递已撤回')
    fetchList()
  } catch {
    // 用户取消
  }
}

// 切换状态筛选: 重置到第 1 页
const onStatusChange = () => {
  page.value = 1
  fetchList()
}

const statusText = (s: number) =>
  ({ 0: '已投递', 1: '已查看', 2: '面试邀请', 3: '不合适', 4: '已录用', 5: '已撤回' }[s] || '未知')
const statusTagType = (s: number): any =>
  ({ 0: 'info', 1: '', 2: 'success', 3: 'danger', 4: 'success', 5: 'warning' }[s] || 'info')
const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}
const formatTimelineDate = (iso?: string) => {
  if (!iso) return '待定'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

// ===== 企业评价 =====
const reviewVisible = ref(false)
const reviewTarget = ref<any>(null)
const reviewSubmitting = ref(false)
const reviewForm = ref({
  interview_score: 5,
  hr_score: 5,
  accuracy_score: 5,
  comment: '',
})

const openReviewDialog = (row: any) => {
  reviewTarget.value = row
  reviewForm.value = { interview_score: 5, hr_score: 5, accuracy_score: 5, comment: '' }
  reviewVisible.value = true
}

const submitReview = async () => {
  const target = reviewTarget.value
  if (!target || !target.job?.company_id) {
    ElMessage.warning('缺少企业信息, 无法评价')
    return
  }
  reviewSubmitting.value = true
  try {
    await reviewApi.create({
      company_id: target.job.company_id,
      application_id: target.id,
      interview_score: reviewForm.value.interview_score,
      hr_score: reviewForm.value.hr_score,
      accuracy_score: reviewForm.value.accuracy_score,
      comment: (reviewForm.value.comment || '').trim() || undefined,
    })
    ElMessage.success('评价成功, 感谢您的反馈')
    reviewVisible.value = false
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '评价失败, 请重试')
  } finally {
    reviewSubmitting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.app-page { display: flex; flex-direction: column; gap: 16px; }
.filter-card { border-radius: 12px; }
.filter-card :deep(.el-card__body) { padding: 14px 16px; }
.filter-bar { display: flex; align-items: center; gap: 12px; }
.filter-bar .label { font-weight: 600; flex: 1; }
.list-card { border-radius: 12px; }
.job-title { font-weight: 600; color: var(--text-primary); cursor: pointer; }
.job-title:hover { color: #1677ff; }
.job-sub { font-size: 12px; color: var(--text-secondary); margin-top: 2px; }
.muted { color: var(--text-secondary); font-size: 12px; }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }

/* 时间轴展开区 */
.timeline-expand { padding: 16px 24px; background: #fafbfc; border-radius: 8px; }
.timeline-loading { display: flex; align-items: center; gap: 8px; color: #1677ff; padding: 12px 0; }
.rotating { animation: rotate 1.2s linear infinite; }
@keyframes rotate { to { transform: rotate(360deg); } }
.timeline-content { max-width: 500px; }
.tl-title { font-size: 14px; font-weight: 600; }
.tl-done { color: #52c41a; }
.tl-rejected { color: #ff4d4f; }
.tl-pending { color: #bfbfbf; }
.tl-desc { font-size: 12px; color: #888; margin-top: 4px; line-height: 1.4; }
.tl-actor { font-size: 11px; color: #ccc; margin-top: 2px; }
.timeline-empty { color: #ccc; font-size: 13px; padding: 8px 0; }

/* 企业评价弹窗 */
.action-cell { display: flex; align-items: center; gap: 4px; }
.review-company { display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 600; color: var(--text-primary); }
.review-job { color: var(--text-secondary); font-weight: 400; font-size: 13px; }
.review-tip { font-size: 12px; color: #999; margin: 8px 0 16px; }
.review-item { margin-bottom: 16px; }
.review-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 6px; }
.review-item :deep(.el-rate) { font-size: 22px; }
</style>
