<!--
  VIP 管理 (管理员)
  - 用户列表表格 (用户名/角色/VIP状态/到期时间/免费配额/付费配额)
  - 筛选: 全部用户 / 仅VIP用户
  - 操作: 开通VIP (弹窗选择时长) / 取消VIP
-->
<template>
  <div class="vip-manage-page">
    <!-- 筛选区 -->
    <el-card shadow="never" class="filter-card">
      <el-input
        v-model="keyword"
        placeholder="搜索用户名/昵称"
        clearable
        :prefix-icon="Search"
        style="width: 260px"
        @keyup.enter="fetchList"
        @clear="fetchList"
      />
      <el-radio-group v-model="vipOnly" @change="fetchList">
        <el-radio-button :value="0">全部用户</el-radio-button>
        <el-radio-button :value="1">仅 VIP 用户</el-radio-button>
      </el-radio-group>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
    </el-card>

    <!-- 用户列表 -->
    <el-card shadow="never" class="list-card">
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="username" label="用户名" min-width="120" />
        <el-table-column prop="nickname" label="昵称" min-width="120">
          <template #default="{ row }">{{ row.nickname || '-' }}</template>
        </el-table-column>
        <el-table-column label="角色" width="90">
          <template #default="{ row }">
            <el-tag size="small">{{ roleText(row.role) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="VIP 状态" width="110" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_vip" type="warning" size="small" effect="dark">
              <el-icon style="vertical-align: middle"><GoldMedal /></el-icon>
              VIP
            </el-tag>
            <el-tag v-else type="info" size="small">普通</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="会员类型" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.vip_plan_label" type="success" size="small" effect="plain">
              {{ row.vip_plan_label }}
            </el-tag>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="到期时间" min-width="160">
          <template #default="{ row }">
            <span v-if="row.vip_expire_at" :class="{ expired: isExpired(row.vip_expire_at) }">
              {{ formatDate(row.vip_expire_at) }}
            </span>
            <span v-else class="text-muted">-</span>
          </template>
        </el-table-column>
        <el-table-column label="免费配额" width="120" align="center">
          <template #default="{ row }">
            {{ row.free_used ?? 0 }} / {{ row.free_total ?? 0 }}
          </template>
        </el-table-column>
        <el-table-column label="付费配额" width="100" align="center">
          <template #default="{ row }">
            <span class="paid-num">{{ row.paid_remaining ?? 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_vip"
              link
              type="primary"
              :icon="GoldMedal"
              @click="openVipDialog(row)"
            >
              开通 VIP
            </el-button>
            <el-button
              v-else
              link
              type="warning"
              :icon="Clock"
              @click="openVipDialog(row)"
            >
              续费/延期
            </el-button>
            <el-button
              v-if="row.is_vip"
              link
              type="danger"
              :icon="Close"
              @click="handleCancelVip(row)"
            >
              取消 VIP
            </el-button>
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

    <!-- 开通/续费 VIP 对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="440px">
      <el-descriptions :column="1" border v-if="currentUser">
        <el-descriptions-item label="用户名">{{ currentUser.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ currentUser.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="当前状态">
          <el-tag v-if="currentUser.is_vip" type="warning" size="small">VIP 会员</el-tag>
          <el-tag v-else type="info" size="small">普通用户</el-tag>
        </el-descriptions-item>
        <el-descriptions-item v-if="currentUser.vip_expire_at" label="当前到期">
          {{ formatDate(currentUser.vip_expire_at) }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="duration-select">
        <div class="duration-label">选择开通时长</div>
        <div class="duration-list">
          <div
            v-for="opt in durationOptions"
            :key="opt.days"
            class="duration-card"
            :class="{ active: selectedDays === opt.days }"
            @click="selectedDays = opt.days"
          >
            <div class="duration-name">{{ opt.label }}</div>
            <div class="duration-days">{{ opt.days }} 天</div>
          </div>
        </div>
      </div>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleOpenVip">
          确认开通
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, GoldMedal, Clock, Close } from '@element-plus/icons-vue'
import { adminVipApi } from '@/api/vip'

const list = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
const vipOnly = ref(0)
const page = ref(1)
const size = ref(20)
const total = ref(0)

// 开通 VIP 对话框
const dialogVisible = ref(false)
const currentUser = ref<any>(null)
const selectedDays = ref(30)
const submitting = ref(false)

const durationOptions = [
  { days: 30, label: '月卡' },
  { days: 90, label: '季卡' },
  { days: 365, label: '年卡' },
]

const dialogTitle = computed(() => {
  if (!currentUser.value) return '开通 VIP'
  return currentUser.value.is_vip ? '续费 / 延期 VIP' : '开通 VIP'
})

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await adminVipApi.vipUsers({
      page: page.value,
      size: size.value,
      vip_only: vipOnly.value,
      keyword: keyword.value || undefined,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } catch {
    // 错误已由拦截器提示
  } finally {
    loading.value = false
  }
}

const openVipDialog = (row: any) => {
  currentUser.value = row
  selectedDays.value = 30
  dialogVisible.value = true
}

const handleOpenVip = async () => {
  if (!currentUser.value) return
  submitting.value = true
  try {
    await adminVipApi.setVip({
      user_id: currentUser.value.id,
      is_vip: true,
      duration_days: selectedDays.value,
    })
    ElMessage.success(`已开通 VIP ${selectedDays.value} 天`)
    dialogVisible.value = false
    fetchList()
  } catch {
    // 错误已由拦截器提示
  } finally {
    submitting.value = false
  }
}

const handleCancelVip = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确认取消用户 ${row.username} 的 VIP 身份? 此操作立即生效。`,
      '取消 VIP',
      { type: 'warning' }
    )
    await adminVipApi.setVip({ user_id: row.id, is_vip: false })
    ElMessage.success('已取消 VIP')
    fetchList()
  } catch {
    // 用户取消或请求失败
  }
}

const roleText = (r: string) => ({
  ROLE_SEEKER: '个人',
  ROLE_EMPLOYER: '企业',
  ROLE_ADMIN: '管理员',
}[r] || r)

const formatDate = (iso?: string) =>
  iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const isExpired = (iso: string) => new Date(iso).getTime() < Date.now()

onMounted(fetchList)
</script>

<style scoped>
.vip-manage-page { }
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; align-items: center; gap: 12px; padding: 16px; flex-wrap: wrap; }
.list-card { border-radius: 12px; }

.paid-num { font-weight: 600; color: #faad14; }
.text-muted { color: #bfbfbf; }
.expired { color: #ff4d4f; text-decoration: line-through; }

/* 开通时长选择 */
.duration-select { margin-top: 20px; }
.duration-label {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 12px;
}
.duration-list { display: flex; gap: 12px; }
.duration-card {
  flex: 1; padding: 16px 12px; border-radius: 10px;
  border: 2px solid #f0f0f0; background: #fff; cursor: pointer;
  text-align: center; transition: all 0.2s;
}
.duration-card:hover { border-color: #faad14; }
.duration-card.active {
  border-color: #faad14; background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  box-shadow: 0 4px 12px rgba(250, 173, 20, 0.2);
}
.duration-name { font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.duration-days { font-size: 12px; color: var(--text-secondary); }

@media (max-width: 768px) {
  .duration-list { flex-direction: column; }
}
</style>
