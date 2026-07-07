<!--
  管理后台仪表盘 - 运营监控
-->
<template>
  <div class="admin-dashboard" v-loading="loading">
    <!-- KPI 总览 -->
    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="kpi in kpiCards" :key="kpi.label">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon" :style="{ background: kpi.bg, color: kpi.color }">
            <el-icon :size="24"><component :is="kpi.icon" /></el-icon>
          </div>
          <div class="kpi-meta">
            <div class="kpi-value">{{ kpi.value }}</div>
            <div class="kpi-label">{{ kpi.label }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 数据明细 -->
    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">用户分布</div></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="总用户数">{{ stats.users?.total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="个人用户">{{ stats.users?.seeker || 0 }}</el-descriptions-item>
            <el-descriptions-item label="企业用户">{{ stats.users?.employer || 0 }}</el-descriptions-item>
            <el-descriptions-item label="管理员">{{ stats.users?.admin || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">简历与职位</div></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="简历总数">{{ stats.resumes?.total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="已解析">{{ stats.resumes?.parsed || 0 }}</el-descriptions-item>
            <el-descriptions-item label="职位总数">{{ stats.jobs?.total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="招聘中">{{ stats.jobs?.active || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16">
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">匹配统计</div></template>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="匹配记录数">{{ stats.matches?.total || 0 }}</el-descriptions-item>
            <el-descriptions-item label="平均匹配分">{{ stats.matches?.avg_score || 0 }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-col>
      <el-col :xs="24" :md="12">
        <el-card shadow="never" class="section-card">
          <template #header><div class="card-header">最近新增用户</div></template>
          <el-table :data="stats.recent_users || []" size="small" :max-height="220">
            <el-table-column prop="username" label="用户名" min-width="100" />
            <el-table-column prop="role" label="角色" width="120">
              <template #default="{ row }">{{ roleText(row.role) }}</template>
            </el-table-column>
            <el-table-column prop="created_at" label="注册时间" min-width="140">
              <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { User, Document, Briefcase, Connection } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'

const stats = ref<any>({})
const loading = ref(false)

const kpiCards = computed(() => [
  { label: '用户总数', value: stats.value.users?.total || 0, icon: User, color: '#1677ff', bg: '#e6f4ff' },
  { label: '简历总数', value: stats.value.resumes?.total || 0, icon: Document, color: '#52c41a', bg: '#f6ffed' },
  { label: '职位总数', value: stats.value.jobs?.total || 0, icon: Briefcase, color: '#faad14', bg: '#fffbe6' },
  { label: '匹配记录', value: stats.value.matches?.total || 0, icon: Connection, color: '#722ed1', bg: '#f9f0ff' },
])

const roleText = (r: string) => ({ ROLE_SEEKER: '个人', ROLE_EMPLOYER: '企业', ROLE_ADMIN: '管理员' }[r] || r)
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const fetch = async () => {
  loading.value = true
  try {
    const res: any = await adminApi.dashboard()
    stats.value = res.data || {}
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>

<style scoped>
.kpi-row { margin-bottom: 16px; }
.kpi-card { border-radius: 10px; }
.kpi-card :deep(.el-card__body) { display: flex; align-items: center; gap: 14px; padding: 16px; }
.kpi-icon { width: 52px; height: 52px; border-radius: 10px; display: flex; align-items: center; justify-content: center; }
.kpi-value { font-size: 24px; font-weight: 700; line-height: 1.2; }
.kpi-label { color: var(--text-secondary); font-size: 13px; margin-top: 2px; }
.section-card { border-radius: 10px; margin-bottom: 16px; }
.card-header { font-weight: 600; }
</style>
