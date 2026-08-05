<!--
  用户管理 (管理员)
-->
<template>
  <div class="users-page">
    <el-card shadow="never" class="filter-card">
      <el-input v-model="searchUsername" placeholder="用户名" clearable :prefix-icon="Search" style="width: 180px" @keyup.enter="fetchList" />
      <el-input v-model="searchPhone" placeholder="手机号" clearable :prefix-icon="Search" style="width: 180px" @keyup.enter="fetchList" />
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
      <el-button @click="handleReset">重置</el-button>
      <el-button :icon="Download" :loading="exporting" @click="handleExport">导出CSV</el-button>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div v-if="selectedRows.length" class="batch-bar">
        <span class="batch-info">已选 {{ selectedRows.length }} 项</span>
        <el-button type="success" @click="handleBatchStatus(1)">批量启用</el-button>
        <el-button type="warning" @click="handleBatchStatus(0)">批量禁用</el-button>
      </div>
      <el-table :data="list" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
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
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">查看详情</el-button>
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

    <!-- 用户详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="用户详情"
      direction="rtl"
      size="500px"
      :destroy-on-close="true"
    >
      <div v-loading="detailLoading">
        <template v-if="currentDetail">
          <!-- 基本信息 -->
          <div class="section-title">基本信息</div>
          <div class="info-grid">
            <div class="info-row"><span class="info-label">用户名</span><span class="info-value">{{ currentDetail.user.username }}</span></div>
            <div class="info-row"><span class="info-label">昵称</span><span class="info-value">{{ currentDetail.user.nickname || '-' }}</span></div>
            <div class="info-row"><span class="info-label">角色</span><span class="info-value">{{ roleText(currentDetail.user.role) }}</span></div>
            <div class="info-row"><span class="info-label">状态</span><span class="info-value">{{ currentDetail.user.status === 1 ? '启用' : '禁用' }}</span></div>
            <div class="info-row"><span class="info-label">手机号</span><span class="info-value">{{ currentDetail.user.phone || '-' }}</span></div>
            <div class="info-row"><span class="info-label">邮箱</span><span class="info-value">{{ currentDetail.user.email || '-' }}</span></div>
            <div v-if="currentDetail.user.company_name" class="info-row"><span class="info-label">企业名称</span><span class="info-value">{{ currentDetail.user.company_name }}</span></div>
            <div v-if="currentDetail.user.contact_person" class="info-row"><span class="info-label">联系人</span><span class="info-value">{{ currentDetail.user.contact_person }}</span></div>
            <div v-if="currentDetail.user.real_name" class="info-row"><span class="info-label">真实姓名</span><span class="info-value">{{ currentDetail.user.real_name }}</span></div>
            <div v-if="currentDetail.user.gender" class="info-row"><span class="info-label">性别</span><span class="info-value">{{ currentDetail.user.gender }}</span></div>
          </div>

          <!-- 关联统计 -->
          <div class="section-title" style="margin-top:20px">关联统计</div>
          <el-descriptions :column="2" border>
            <el-descriptions-item label="简历数">{{ currentDetail.stats?.resume_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="投递数">{{ currentDetail.stats?.application_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="职位数">{{ currentDetail.stats?.job_count ?? 0 }}</el-descriptions-item>
            <el-descriptions-item label="收到投递">{{ currentDetail.stats?.received_count ?? 0 }}</el-descriptions-item>
          </el-descriptions>

          <!-- 时间 -->
          <div class="section-title" style="margin-top:20px">时间信息</div>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="注册时间">{{ formatDate(currentDetail.user.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ formatDate(currentDetail.user.last_login_at) }}</el-descriptions-item>
          </el-descriptions>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Download } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'

const list = ref<any[]>([])
const loading = ref(false)
const exporting = ref(false)
const searchUsername = ref('')
const searchPhone = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null
watch(searchUsername, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchList()
  }, 300)
})
watch(searchPhone, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchList()
  }, 300)
})
const roleFilter = ref('')
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
    const res: any = await adminApi.users({
      page: page.value, size: size.value,
      username: searchUsername.value || undefined,
      phone: searchPhone.value || undefined,
      role: roleFilter.value || undefined,
      status: statusFilter.value === '' ? undefined : statusFilter.value,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  searchUsername.value = ''
  searchPhone.value = ''
  roleFilter.value = ''
  statusFilter.value = ''
  page.value = 1
  fetchList()
}

const showDetail = async (row: any) => {
  drawerVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  try {
    const res: any = await adminApi.userDetailStats(row.id)
    currentDetail.value = res.data || null
  } catch (e: any) {
    ElMessage.error(e?.message || '加载用户详情失败')
  } finally {
    detailLoading.value = false
  }
}

const roleText = (r: string) => ({ ROLE_SEEKER: '个人', ROLE_EMPLOYER: '企业', ROLE_ADMIN: '管理员' }[r] || r)
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const handleBatchStatus = async (status: number) => {
  const ids = selectedRows.value.map(r => r.id)
  const action = status === 1 ? '启用' : '禁用'
  try {
    await ElMessageBox.confirm(`确认批量${action}选中的 ${ids.length} 个用户?`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    const res: any = await adminApi.batchUpdateUserStatus(ids, status)
    ElMessage.success(`已${action} ${res.data?.updated ?? ids.length} 个`)
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

const toggleStatus = async (row: any) => {
  const newStatus = row.status === 1 ? 0 : 1
  try {
    await ElMessageBox.confirm(`确认${newStatus === 1 ? '启用' : '禁用'}用户 ${row.username}?`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await adminApi.updateUserStatus(row.id, newStatus)
    ElMessage.success('已更新')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

const toggleRole = async (row: any) => {
  const newRole = row.role === 'ROLE_SEEKER' ? 'ROLE_EMPLOYER' : 'ROLE_SEEKER'
  try {
    await ElMessageBox.confirm(`确认将 ${row.username} 角色切换为 ${newRole === 'ROLE_SEEKER' ? '个人用户' : '企业用户'}?`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await adminApi.updateUserRole(row.id, newRole)
    ElMessage.success('角色已更新')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '操作失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确认删除用户 ${row.username}? 此操作不可恢复!`, '危险操作', { type: 'error' })
  } catch {
    return
  }
  try {
    await adminApi.deleteUser(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

// 导出用户数据为 CSV
const handleExport = async () => {
  exporting.value = true
  try {
    const res: any = await adminApi.exportData('users')
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `users_${new Date().toISOString().slice(0, 10)}.csv`
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
</style>
