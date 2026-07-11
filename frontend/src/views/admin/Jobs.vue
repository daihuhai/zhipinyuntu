<!--
  职位管理 (管理员)
-->
<template>
  <div class="jobs-page">
    <el-card shadow="never" class="filter-card">
      <el-input v-model="keyword" placeholder="搜索职位/公司" clearable :prefix-icon="Search" style="width: 280px" @keyup.enter="fetchList" @clear="fetchList" />
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 140px" @change="fetchList">
        <el-option label="下架" :value="0" />
        <el-option label="招聘中" :value="1" />
        <el-option label="草稿" :value="2" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button :icon="Download" :loading="exporting" @click="handleExport">导出CSV</el-button>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div v-if="selectedRows.length" class="batch-bar">
        <span class="batch-info">已选 {{ selectedRows.length }} 项</span>
        <el-button type="success" @click="handleBatchStatus(1)">批量上架</el-button>
        <el-button type="warning" @click="handleBatchStatus(0)">批量下架</el-button>
      </div>
      <el-table :data="list" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="title" label="职位名称" min-width="180" />
        <el-table-column prop="company" label="公司" min-width="140" />
        <el-table-column prop="work_city" label="城市" width="80" />
        <el-table-column label="薪资" width="120">
          <template #default="{ row }">{{ formatSalary(row.salary_min, row.salary_max) }}</template>
        </el-table-column>
        <el-table-column prop="headcount" label="招聘人数" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }"><el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="150">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="260" fixed="right">
          <template #default="{ row }">
            <div class="action-cell">
              <el-button link type="primary" @click="showDetail(row)">查看详情</el-button>
              <el-dropdown @command="(c: string) => handleStatus(c, row.id)">
                <el-button link type="primary">修改状态<el-icon><ArrowDown /></el-icon></el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="1">招聘中</el-dropdown-item>
                    <el-dropdown-item command="0">下架</el-dropdown-item>
                    <el-dropdown-item command="2">草稿</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </div>
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

    <!-- 职位详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="职位详情"
      direction="rtl"
      size="560px"
      :destroy-on-close="true"
    >
      <div v-loading="detailLoading">
        <template v-if="currentDetail">
          <!-- 基本信息 -->
          <div class="section-title">基本信息</div>
          <div class="info-grid">
            <div class="info-row"><span class="info-label">职位名称</span><span class="info-value">{{ currentDetail.title }}</span></div>
            <div class="info-row"><span class="info-label">公司</span><span class="info-value">{{ currentDetail.company || '-' }}</span></div>
            <div class="info-row"><span class="info-label">城市</span><span class="info-value">{{ currentDetail.work_city || '-' }}</span></div>
            <div class="info-row"><span class="info-label">薪资</span><span class="info-value">{{ formatSalary(currentDetail.salary_min, currentDetail.salary_max) }}</span></div>
            <div class="info-row"><span class="info-label">经验</span><span class="info-value">{{ currentDetail.experience_required || '不限' }}</span></div>
            <div class="info-row"><span class="info-label">学历</span><span class="info-value">{{ currentDetail.education_required || '不限' }}</span></div>
            <div class="info-row"><span class="info-label">招聘人数</span><span class="info-value">{{ currentDetail.headcount || '-' }}</span></div>
            <div class="info-row"><span class="info-label">状态</span><span class="info-value">{{ statusText(currentDetail.status) }}</span></div>
          </div>

          <!-- 职位描述 -->
          <div class="section-title" style="margin-top:20px">职位描述</div>
          <div class="desc-text">{{ currentDetail.description || '暂无描述' }}</div>

          <!-- 技能要求 -->
          <div v-if="currentDetail.requirements?.length" class="section-title" style="margin-top:20px">技能要求</div>
          <div v-if="currentDetail.requirements?.length" class="skills-row">
            <el-tag
              v-for="r in currentDetail.requirements"
              :key="r.id"
              :type="r.req_type === '必须' || r.req_type === 'required' ? 'danger' : 'warning'"
              size="small" effect="light"
            >
              {{ r.skill_name }}
              <span v-if="r.skill_level"> · {{ r.skill_level }}</span>
              <span v-if="r.req_type"> ({{ r.req_type }})</span>
            </el-tag>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown, Download } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import { jobApi } from '@/api/job'
import { formatSalary } from '@/utils/format'

const list = ref<any[]>([])
const loading = ref(false)
const exporting = ref(false)
const keyword = ref('')
const statusFilter = ref<number | ''>('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

// 详情抽屉
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<any>(null)

// 批量操作 - 选中的行
const selectedRows = ref<any[]>([])
const handleSelectionChange = (rows: any[]) => selectedRows.value = rows

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await adminApi.jobs({
      page: page.value, size: size.value,
      keyword: keyword.value,
      status: statusFilter.value === '' ? undefined : statusFilter.value,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const showDetail = async (row: any) => {
  drawerVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  try {
    const res: any = await jobApi.detail(row.id)
    currentDetail.value = res.data || null
  } catch (e: any) {
    ElMessage.error(e?.message || '加载职位详情失败')
  } finally {
    detailLoading.value = false
  }
}

const statusText = (s: number) => ({ 0: '下架', 1: '招聘中', 2: '草稿' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'success', 2: 'warning' }[s] || 'info')
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const handleBatchStatus = async (status: number) => {
  const ids = selectedRows.value.map(r => r.id)
  const action = status === 1 ? '上架' : '下架'
  await ElMessageBox.confirm(`确认批量${action}选中的 ${ids.length} 条职位?`, '提示', { type: 'warning' })
  const res: any = await adminApi.batchUpdateJobStatus(ids, status)
  ElMessage.success(`已${action} ${res.data?.updated ?? ids.length} 条`)
  fetchList()
}

const handleStatus = async (cmd: string, id: number) => {
  await adminApi.updateJobStatus(id, Number(cmd))
  ElMessage.success('状态已更新')
  fetchList()
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm(`确认删除职位 ${row.title}?`, '提示', { type: 'warning' })
  await adminApi.deleteJob(row.id)
  ElMessage.success('已删除')
  fetchList()
}

// 导出职位数据为 CSV
const handleExport = async () => {
  exporting.value = true
  try {
    const res: any = await adminApi.exportData('jobs')
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `jobs_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; gap: 8px; padding: 16px; flex-wrap: wrap; }
.list-card { border-radius: 12px; }
.batch-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding: 8px 12px; background: #fdf6ec; border-radius: 6px; }
.batch-info { color: #e6a23c; font-weight: 600; font-size: 13px; }
.section-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #1677ff;
}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.info-row { display: flex; padding: 6px 8px; border-bottom: 1px dashed #f0f0f0; font-size: 13px; }
.info-label { width: 72px; color: #999; flex-shrink: 0; }
.info-value { color: #333; }
.desc-text { font-size: 13px; color: #666; line-height: 1.6; padding: 10px; background: #fafafa; border-radius: 6px; }
.skills-row { display: flex; flex-wrap: wrap; gap: 6px; }
.action-cell { display: flex; align-items: center; gap: 4px; }
</style>
