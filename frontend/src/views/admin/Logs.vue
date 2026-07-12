<!--
  操作日志 (管理员) - 含 AI 调用、数据导出、管理员操作
-->
<template>
  <div class="logs-page">
    <el-card shadow="never" class="filter-card">
      <el-select v-model="actionFilter" placeholder="操作类型" clearable style="width: 220px" @change="fetchList">
        <el-option label="全部" value="" />
        <el-option-group label="AI 大模型操作">
          <el-option label="简历解析" value="AI_RESUME_PARSE" />
          <el-option label="简历解析失败" value="AI_RESUME_PARSE_FAILED" />
          <el-option label="缺失项分析" value="AI_GAP_ANALYSIS" />
          <el-option label="智能匹配推荐" value="AI_MATCH_RECOMMEND" />
        </el-option-group>
        <el-option-group label="管理员操作">
          <el-option label="数据导出" value="EXPORT_DATA" />
          <el-option label="用户状态修改" value="UPDATE_USER_STATUS" />
          <el-option label="用户角色修改" value="UPDATE_USER_ROLE" />
          <el-option label="删除用户" value="DELETE_USER" />
          <el-option label="职位状态修改" value="UPDATE_JOB_STATUS" />
          <el-option label="删除职位" value="DELETE_JOB" />
          <el-option label="删除简历" value="DELETE_RESUME" />
          <el-option label="批量操作" value="BATCH_UPDATE_USER_STATUS" />
        </el-option-group>
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button :icon="Refresh" @click="actionFilter = ''; fetchList()">重置</el-button>
      <el-tag v-if="total > 0" type="info" size="large" class="total-tag">共 {{ total }} 条</el-tag>
    </el-card>

    <el-card shadow="never" class="list-card">
      <el-table :data="list" v-loading="loading" stripe row-key="id">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column label="操作类型" width="180">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">{{ actionText(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="target_type" label="目标类型" width="100">
          <template #default="{ row }">
            <span v-if="row.target_type">{{ row.target_type }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="target_id" label="目标 ID" width="100">
          <template #default="{ row }">{{ row.target_id || '-' }}</template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" min-width="280" show-overflow-tooltip />
        <el-table-column label="操作者" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.ip === 'system'" type="warning" size="small">系统</el-tag>
            <span v-else-if="row.admin_id">管理员 #{{ row.admin_id }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="120">
          <template #default="{ row }">{{ row.ip || '-' }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
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
import { Search, Refresh } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'

const list = ref<any[]>([])
const loading = ref(false)
const actionFilter = ref('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await adminApi.logs({
      page: page.value, size: size.value,
      action: actionFilter.value || undefined,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const actionText = (a: string) => {
  const map: Record<string, string> = {
    AI_RESUME_PARSE: 'AI 简历解析',
    AI_RESUME_PARSE_FAILED: 'AI 解析失败',
    AI_GAP_ANALYSIS: 'AI 缺失分析',
    AI_MATCH_RECOMMEND: 'AI 智能匹配',
    EXPORT_DATA: '数据导出',
    UPDATE_USER_STATUS: '用户状态修改',
    UPDATE_USER_ROLE: '用户角色修改',
    DELETE_USER: '删除用户',
    UPDATE_JOB_STATUS: '职位状态修改',
    DELETE_JOB: '删除职位',
    DELETE_RESUME: '删除简历',
    BATCH_UPDATE_USER_STATUS: '批量更新用户',
    BATCH_UPDATE_JOB_STATUS: '批量更新职位',
    BATCH_DELETE_RESUMES: '批量删除简历',
  }
  return map[a] || a || '-'
}

const actionTagType = (a: string): any => {
  if (a?.startsWith('AI_')) return 'warning'
  if (a === 'EXPORT_DATA') return 'success'
  if (a?.startsWith('DELETE') || a?.startsWith('BATCH_DELETE')) return 'danger'
  if (a?.startsWith('BATCH_UPDATE')) return 'info'
  return ''
}

const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

onMounted(fetchList)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; gap: 8px; padding: 16px; flex-wrap: wrap; align-items: center; }
.list-card { border-radius: 12px; }
.total-tag { margin-left: auto; }
</style>
