<!--
  企业设置 (企业) - 可编辑
-->
<template>
  <div class="profile-page">
    <el-card shadow="never" class="profile-card">
      <template #header><div class="card-header">企业信息</div></template>

      <div v-loading="loading">
        <!-- 只读信息 -->
        <el-descriptions :column="2" border class="readonly-section">
          <el-descriptions-item label="用户名">{{ form.username }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag>{{ roleText }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户 ID">{{ form.user_id }}</el-descriptions-item>
          <el-descriptions-item label="信用代码">{{ form.credit_code || '-' }}</el-descriptions-item>
        </el-descriptions>

        <!-- 可编辑表单 -->
        <el-form :model="form" label-width="100px" class="edit-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="企业昵称">
                <el-input v-model="form.nickname" placeholder="请输入企业昵称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="企业名称">
                <el-input v-model="form.company_name" placeholder="请输入企业全称" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="联系人 (HR姓名)">
                <el-input v-model="form.contact_person" placeholder="请输入联系人姓名" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="联系电话">
                <el-input v-model="form.phone" placeholder="请输入联系电话" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="邮箱">
                <el-input v-model="form.email" placeholder="请输入企业邮箱" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="头像/Logo">
                <el-input v-model="form.avatar_url" placeholder="企业 Logo 链接 (选填)" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <el-button type="primary" :loading="saving" @click="handleSave">保存修改</el-button>
            <el-button @click="handleReset">重置</el-button>
            <el-button type="warning" @click="pwdDialogRef?.open()">修改密码</el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- VIP 会员卡片 -->
    <el-card shadow="never" class="profile-card vip-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header" style="display: flex; align-items: center; gap: 8px;">
          <el-icon style="color: #faad14;"><GoldMedal /></el-icon>
          <span>VIP 会员</span>
        </div>
      </template>
      <div v-if="vipInfo" class="vip-info">
        <div class="vip-status">
          <el-tag v-if="vipInfo.is_vip" type="warning" effect="dark" size="large">
            <el-icon><GoldMedal /></el-icon> VIP 会员
          </el-tag>
          <el-tag v-else type="info" size="large">普通用户</el-tag>
          <span v-if="vipInfo.is_vip && vipInfo.vip_plan_type" class="vip-plan">
            {{ vipInfo.vip_plan_type }} · 剩余 {{ vipInfo.vip_remaining_days || 0 }} 天
          </span>
        </div>
        <div class="vip-quota">
          <span>免费额度: {{ vipInfo.free_quota_used || 0 }} / 2</span>
          <span v-if="vipInfo.paid_quota !== undefined">付费额度: {{ vipInfo.paid_quota }}</span>
        </div>
        <el-button type="warning" @click="router.push('/employer/vip')">
          {{ vipInfo.is_vip ? '续费 VIP' : '开通 VIP' }}
        </el-button>
      </div>
      <div v-else class="vip-info">
        <el-button type="warning" @click="router.push('/employer/vip')">查看 VIP 会员</el-button>
      </div>
    </el-card>

    <!-- 修改密码弹窗 -->
    <ChangePasswordDialog ref="pwdDialogRef" @success="onPasswordChanged" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const userStore = useUserStore()
const loading = ref(false)
const saving = ref(false)
const pwdDialogRef = ref<InstanceType<typeof ChangePasswordDialog>>()

const onPasswordChanged = () => {
  localStorage.removeItem('access_token')
  ElMessage.info('请使用新密码重新登录')
  setTimeout(() => window.location.href = '/login', 1500)
}

const form = reactive<any>({
  user_id: '',
  username: '',
  nickname: '',
  company_name: '',
  credit_code: '',
  contact_person: '',
  phone: '',
  email: '',
  avatar_url: '',
  role: '',
})

const roleText = computed(() => ({
  ROLE_SEEKER: '个人用户',
  ROLE_EMPLOYER: '企业用户',
  ROLE_ADMIN: '管理员',
}[form.role] || '未知'))

const fetchInfo = async () => {
  loading.value = true
  try {
    const res: any = await authApi.me()
    const d = res.data || {}
    Object.assign(form, {
      user_id: d.user_id,
      username: d.username,
      nickname: d.nickname || '',
      company_name: d.company_name || '',
      credit_code: d.credit_code || '',
      contact_person: d.contact_person || '',
      phone: d.phone || '',
      email: d.email || '',
      avatar_url: d.avatar_url || '',
      role: d.role,
    })
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  try {
    const res: any = await authApi.updateProfile({
      nickname: form.nickname,
      company_name: form.company_name,
      contact_person: form.contact_person,
      phone: form.phone,
      email: form.email,
      avatar_url: form.avatar_url,
    })
    ElMessage.success(res.message || '保存成功')
    if (userStore.userInfo) {
      userStore.setUserInfo({
        ...userStore.userInfo,
        nickname: form.nickname,
      })
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

const handleReset = () => {
  fetchInfo()
}

const fetchVipInfo = async () => {
  try {
    const res: any = await vipApi.getQuota()
    vipInfo.value = res.data || null
  } catch {}
}

onMounted(() => { fetchInfo(); fetchVipInfo() })
</script>

<style scoped>
.profile-page { max-width: 800px; margin: 0 auto; }
.profile-card { border-radius: 12px; }
.card-header { font-weight: 600; }
.readonly-section { margin-bottom: 24px; }
.edit-form { margin-top: 8px; }
.vip-card { border: 1px solid rgba(250, 173, 20, 0.3); }
.vip-info { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.vip-status { display: flex; align-items: center; gap: 10px; }
.vip-plan { font-size: 13px; color: var(--text-secondary); }
.vip-quota { font-size: 13px; color: var(--text-secondary); display: flex; gap: 16px; }
</style>
