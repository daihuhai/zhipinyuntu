<!--
  我的简历列表
-->
<template>
  <div class="resume-list">
    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>我的简历</span>
          <el-button type="primary" :icon="Plus" @click="$router.push('/seeker/resume/upload')">上传新简历</el-button>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column prop="school" label="学校" width="160" />
        <el-table-column prop="major" label="专业" width="140" />
        <el-table-column prop="work_years" label="工作年限" width="100">
          <template #default="{ row }">{{ row.work_years || 0 }} 年</template>
        </el-table-column>
        <el-table-column label="解析状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.parse_status)">{{ statusText(row.parse_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/seeker/graph?resume_id=${row.id}`)">能力图谱</el-button>
            <el-button link type="success" @click="$router.push(`/seeker/recommend?resume_id=${row.id}`)">推荐职位</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { resumeApi } from '@/api/resume'

const list = ref<any[]>([])
const loading = ref(false)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await resumeApi.list()
    list.value = res.data?.items || []
  } finally {
    loading.value = false
  }
}

const statusText = (s: number) => ({ 0: '待解析', 1: '解析中', 2: '成功', 3: '失败' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }[s] || 'info')

const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

const handleDelete = async (id: number) => {
  await ElMessageBox.confirm('确认删除该简历?', '提示', { type: 'warning' })
  await resumeApi.remove(id)
  ElMessage.success('已删除')
  fetchList()
}

onMounted(fetchList)
</script>

<style scoped>
.list-card { border-radius: 12px; }
.card-header { display: flex; align-items: center; justify-content: space-between; font-weight: 600; }
</style>
