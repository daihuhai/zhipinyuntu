<!--
  投递记录 (求职者) - 查看已投递职位与状态
-->
<template>
  <div class="app-page">
    <el-card shadow="never" class="filter-card">
      <div class="filter-bar">
        <span class="label">我的投递记录</span>
        <el-tag v-if="!loading" type="info" size="small">共 {{ total }} 条</el-tag>
        <el-button :icon="Refresh" :loading="loading" @click="fetchList">刷新</el-button>
      </div>
    </el-card>

    <el-card shadow="never" class="list-card" v-loading="loading">
      <el-empty v-if="!loading && !list.length" description="暂无投递记录, 去看看推荐职位吧">
        <el-button type="primary" plain @click="$router.push('/seeker/recommend')">查看推荐</el-button>
      </el-empty>
      <el-table v-else :data="list" stripe>
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
        <el-table-column label="求职信" min-width="180">
          <template #default="{ row }">
            <span v-if="row.cover_letter" class="cover-letter" :title="row.cover_letter">
              {{ row.cover_letter }}
            </span>
            <span v-else class="muted">-</span>
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { applicationApi } from '@/api/application'
import { formatSalary } from '@/utils/format'

const route = useRoute()
const list = ref<any[]>([])
const loading = ref(false)
const page = ref(Number(route.query.page) || 1)
const pageSize = ref(20)
const total = ref(0)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await applicationApi.myList({ page: page.value, size: pageSize.value })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch (e: any) {
    ElMessage.error(e?.message || '加载投递记录失败')
    list.value = []
  } finally {
    loading.value = false
  }
}

const statusText = (s: number) =>
  ({ 0: '已投递', 1: '已查看', 2: '面试邀请', 3: '不合适', 4: '已录用' }[s] || '未知')
const statusTagType = (s: number): any =>
  ({ 0: 'info', 1: '', 2: 'success', 3: 'danger', 4: 'success' }[s] || 'info')
const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
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
.cover-letter {
  display: inline-block; max-width: 180px;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  color: var(--text-secondary); font-size: 13px;
}
.muted { color: var(--text-secondary); }
.pager { margin-top: 16px; display: flex; justify-content: flex-end; }
</style>
