<!--
  企业职位列表 - 支持搜索 + 投递数统计
-->
<template>
  <div class="job-list-page">
    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>我发布的职位</span>
          <div class="header-right">
            <el-input
              v-model="keyword"
              placeholder="搜索职位名称"
              :prefix-icon="Search"
              clearable
              style="width: 220px"
              @input="onSearch"
              @clear="onSearch"
            />
            <el-button type="primary" :icon="Plus" @click="$router.push('/employer/job/create')">发布新职位</el-button>
          </div>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="title" label="职位名称" min-width="180" />
        <el-table-column prop="company" label="公司" width="140" />
        <el-table-column prop="work_city" label="城市" width="80" />
        <el-table-column label="薪资" width="120">
          <template #default="{ row }">{{ formatSalary(row.salary_min, row.salary_max) }}</template>
        </el-table-column>
        <el-table-column label="学历要求" width="120">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.education_required || '不限' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="headcount" label="招聘人数" width="90" />
        <el-table-column label="投递数" width="90">
          <template #default="{ row }">
            <el-badge :value="row.application_count" :hidden="!row.application_count" type="primary">
              <el-button link type="warning" size="small" @click="$router.push(`/employer/applications?job_id=${row.id}`)">
                {{ row.application_count || 0 }}
              </el-button>
            </el-badge>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" min-width="150">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button link type="warning" @click="$router.push(`/employer/applications?job_id=${row.id}`)">投递{{ row.application_count ? `(${row.application_count})` : '' }}</el-button>
            <el-button link type="success" @click="$router.push(`/employer/candidates?job_id=${row.id}`)">推荐</el-button>
            <el-dropdown @command="(c: string) => handleCommand(c, row)">
              <el-button link type="primary">更多<el-icon><ArrowDown /></el-icon></el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="status_1">上架</el-dropdown-item>
                  <el-dropdown-item command="status_0">下架</el-dropdown-item>
                  <el-dropdown-item command="status_2">转为草稿</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ArrowDown, Search } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { formatSalary } from '@/utils/format'

const list = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
let searchTimer: any = null

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await jobApi.myList(keyword.value.trim() || undefined)
    list.value = res.data?.items || []
  } catch (e: any) {
    ElMessage.error(e?.message || '职位列表加载失败')
    list.value = []
  } finally {
    loading.value = false
  }
}

const onSearch = () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(fetchList, 300)
}

const statusText = (s: number) => ({ 0: '下架', 1: '招聘中', 2: '草稿' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'success', 2: 'warning' }[s] || 'info')

const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const handleCommand = async (cmd: string, row: any) => {
  if (cmd === 'delete') {
    await ElMessageBox.confirm('确认删除该职位?', '提示', { type: 'warning' })
    await jobApi.remove(row.id)
    ElMessage.success('已删除')
  } else if (cmd.startsWith('status_')) {
    const status = Number(cmd.split('_')[1])
    await jobApi.updateStatus(row.id, status)
    ElMessage.success('状态已更新')
  }
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped>
.list-card { border-radius: 12px; }
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 600;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
