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
    </el-card>

    <el-card shadow="never" class="list-card">
      <el-table :data="list" v-loading="loading" stripe>
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
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
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
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, ArrowDown } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import { formatSalary } from '@/utils/format'

const list = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
const statusFilter = ref<number | ''>('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

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

const statusText = (s: number) => ({ 0: '下架', 1: '招聘中', 2: '草稿' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'success', 2: 'warning' }[s] || 'info')
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

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

onMounted(fetchList)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; gap: 8px; padding: 16px; flex-wrap: wrap; }
.list-card { border-radius: 12px; }
</style>
