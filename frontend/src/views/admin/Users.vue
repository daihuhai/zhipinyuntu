<!--
  用户管理 (管理员)
-->
<template>
  <div class="users-page">
    <el-card shadow="never" class="filter-card">
      <el-input v-model="keyword" placeholder="搜索用户名/昵称/手机号" clearable :prefix-icon="Search" style="width: 280px" @keyup.enter="fetchList" @clear="fetchList" />
      <el-select v-model="roleFilter" placeholder="角色" clearable style="width: 140px" @change="fetchList">
        <el-option label="个人用户" value="ROLE_SEEKER" />
        <el-option label="企业用户" value="ROLE_EMPLOYER" />
        <el-option label="管理员" value="ROLE_ADMIN" />
      </el-select>
      <el-select v-model="statusFilter" placeholder="状态" clearable style="width: 120px" @change="fetchList">
        <el-option label="启用" :value="1" />
        <el-option label="禁用" :value="0" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
    </el-card>

    <el-card shadow="never" class="list-card">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="120" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }"><el-tag>{{ roleText(row.role) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="phone" label="手机号" width="140" />
        <el-table-column prop="company_name" label="企业名称" min-width="160">
          <template #default="{ row }">{{ row.company_name || '-' }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">{{ row.status === 1 ? '启用' : '禁用' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="注册时间" min-width="150">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link :type="row.status === 1 ? 'warning' : 'success'" @click="toggleStatus(row)">
              {{ row.status === 1 ? '禁用' : '启用' }}
            </el-button>
            <el-button v-if="row.role !== 'ROLE_ADMIN'" link type="primary" @click="toggleRole(row)">切换角色</el-button>
            <el-button v-if="row.role !== 'ROLE_ADMIN'" link type="danger" @click="handleDelete(row)">删除</el-button>
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
const roleFilter = ref('')
const statusFilter = ref<number | ''>('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await adminApi.users({
      page: page.value, size: size.value,
      keyword: keyword.value,
      role: roleFilter.value || undefined,
      status: statusFilter.value === '' ? undefined : statusFilter.value,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const roleText = (r: string) => ({ ROLE_SEEKER: '个人', ROLE_EMPLOYER: '企业', ROLE_ADMIN: '管理员' }[r] || r)
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const toggleStatus = async (row: any) => {
  const newStatus = row.status === 1 ? 0 : 1
  await ElMessageBox.confirm(`确认${newStatus === 1 ? '启用' : '禁用'}用户 ${row.username}?`, '提示', { type: 'warning' })
  await adminApi.updateUserStatus(row.id, newStatus)
  ElMessage.success('已更新')
  fetchList()
}

const toggleRole = async (row: any) => {
  const newRole = row.role === 'ROLE_SEEKER' ? 'ROLE_EMPLOYER' : 'ROLE_SEEKER'
  await ElMessageBox.confirm(`确认将 ${row.username} 角色切换为 ${newRole === 'ROLE_SEEKER' ? '个人用户' : '企业用户'}?`, '提示', { type: 'warning' })
  await adminApi.updateUserRole(row.id, newRole)
  ElMessage.success('角色已更新')
  fetchList()
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm(`确认删除用户 ${row.username}? 此操作不可恢复!`, '危险操作', { type: 'error' })
  await adminApi.deleteUser(row.id)
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
