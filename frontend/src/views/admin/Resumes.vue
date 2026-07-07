<!--
  简历管理 (管理员)
-->
<template>
  <div class="resumes-page">
    <el-card shadow="never" class="filter-card">
      <el-input v-model="keyword" placeholder="搜索姓名/学校" clearable :prefix-icon="Search" style="width: 280px" @keyup.enter="fetchList" @clear="fetchList" />
      <el-select v-model="parseStatus" placeholder="解析状态" clearable style="width: 140px" @change="fetchList">
        <el-option label="待解析" :value="0" />
        <el-option label="解析中" :value="1" />
        <el-option label="成功" :value="2" />
        <el-option label="失败" :value="3" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
    </el-card>

    <el-card shadow="never" class="list-card">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="age" label="年龄" width="70" />
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column prop="school" label="学校" min-width="140" />
        <el-table-column prop="major" label="专业" min-width="120" />
        <el-table-column prop="work_years" label="工作年限" width="100">
          <template #default="{ row }">{{ row.work_years || 0 }} 年</template>
        </el-table-column>
        <el-table-column label="解析状态" width="100">
          <template #default="{ row }"><el-tag :type="statusTag(row.parse_status)">{{ statusText(row.parse_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" min-width="150">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
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
import { Search } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'

const list = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
const parseStatus = ref<number | ''>('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await adminApi.resumes({
      page: page.value, size: size.value,
      keyword: keyword.value,
      parse_status: parseStatus.value === '' ? undefined : parseStatus.value,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const statusText = (s: number) => ({ 0: '待解析', 1: '解析中', 2: '成功', 3: '失败' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }[s] || 'info')
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm(`确认删除简历 ${row.name || '#' + row.id}?`, '提示', { type: 'warning' })
  await adminApi.deleteResume(row.id)
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
