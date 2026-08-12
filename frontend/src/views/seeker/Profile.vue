<!--
  个人设置 (求职者) - 可编辑
-->
<template>
  <div class="profile-page">
    <el-card shadow="never" class="profile-card">
      <template #header><div class="card-header">个人信息</div></template>

      <div v-loading="loading">
        <!-- 只读信息 -->
        <el-descriptions :column="2" border class="readonly-section">
          <el-descriptions-item label="用户名">{{ form.username }}</el-descriptions-item>
          <el-descriptions-item label="角色">
            <el-tag>{{ roleText }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户 ID">{{ form.user_id }}</el-descriptions-item>
        </el-descriptions>

        <!-- 头像上传 -->
        <el-form-item label="头像">
          <div class="avatar-upload-wrap">
            <el-upload
              class="avatar-uploader"
              :show-file-list="false"
              :before-upload="beforeAvatarUpload"
              :http-request="handleAvatarUpload"
              accept="image/jpeg,image/png,image/gif,image/webp"
            >
              <div v-if="form.avatar_url" class="avatar-preview">
                <img :src="avatarFullUrl" class="avatar-img" />
                <div class="avatar-overlay">点击更换</div>
              </div>
              <div v-else class="avatar-placeholder">
                <el-icon :size="28"><Plus /></el-icon>
                <span>点击上传</span>
              </div>
              <div v-if="avatarUploading" class="avatar-loading">
                <el-icon class="is-loading" :size="24"><Loading /></el-icon>
              </div>
            </el-upload>
            <div class="avatar-tips">支持 JPG / PNG / GIF / WebP, 大小不超过 2MB</div>
          </div>
        </el-form-item>

        <!-- 可编辑表单 -->
        <el-form :model="form" label-width="100px" class="edit-form">
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="昵称">
                <el-input v-model="form.nickname" placeholder="请输入昵称" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="真实姓名">
                <el-input v-model="form.real_name" placeholder="请输入真实姓名" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="性别">
                <el-select v-model="form.gender" placeholder="请选择" style="width: 100%">
                  <el-option label="男" value="男" />
                  <el-option label="女" value="女" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="手机号">
                <el-input v-model="form.phone" placeholder="请输入手机号" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="邮箱">
                <el-input v-model="form.email" placeholder="请输入邮箱" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="身份证号">
                <el-input v-model="form.id_card" placeholder="请输入身份证号" maxlength="18" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="出生日期">
                <el-input :model-value="form.birth_date" disabled placeholder="由身份证号自动解析" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="16">
            <el-col :span="12">
              <el-form-item label="最高学历">
                <el-select v-model="form.education" placeholder="请选择" style="width: 100%" clearable>
                  <el-option label="高中及以下" value="高中及以下" />
                  <el-option label="大专" value="大专" />
                  <el-option label="本科" value="本科" />
                  <el-option label="硕士" value="硕士" />
                  <el-option label="博士" value="博士" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="工作年限">
                <el-input-number v-model="form.work_years" :min="0" :max="50" style="width: 100%" controls-position="right" />
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
        <el-button type="warning" @click="router.push('/seeker/vip')">
          {{ vipInfo.is_vip ? '续费 VIP' : '开通 VIP' }}
        </el-button>
      </div>
      <div v-else class="vip-info">
        <el-button type="warning" @click="router.push('/seeker/vip')">查看 VIP 会员</el-button>
      </div>
    </el-card>

    <!-- 修改密码弹窗 -->
    <ChangePasswordDialog ref="pwdDialogRef" @success="onPasswordChanged" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Loading } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'
import { vipApi } from '@/api/vip'
import ChangePasswordDialog from '@/components/ChangePasswordDialog.vue'

const router = useRouter()
const userStore = useUserStore()
const loading = ref(false)
const saving = ref(false)
const avatarUploading = ref(false)
const pwdDialogRef = ref<InstanceType<typeof ChangePasswordDialog>>()
const vipInfo = ref<any>(null)

const onPasswordChanged = () => {
  // 密码修改成功, 清除 token 跳转登录
  localStorage.removeItem('access_token')
  ElMessage.info('请使用新密码重新登录')
  setTimeout(() => window.location.href = '/login', 1500)
}

const form = reactive<any>({
  user_id: '',
  username: '',
  nickname: '',
  real_name: '',
  gender: '',
  phone: '',
  email: '',
  avatar_url: '',
  role: '',
  id_card: '',
  birth_date: '',
  education: '',
  work_years: null as number | null,
})

const roleText = computed(() => ({
  ROLE_SEEKER: '个人用户',
  ROLE_EMPLOYER: '企业用户',
  ROLE_ADMIN: '管理员',
}[form.role] || '未知'))

const avatarFullUrl = computed(() => {
  if (!form.avatar_url) return ''
  return form.avatar_url.startsWith('http') ? form.avatar_url : window.location.origin + form.avatar_url
})

// 头像上传前校验
const beforeAvatarUpload = (file: File) => {
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error('仅支持 JPG / PNG / GIF / WebP 格式')
    return false
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 2MB')
    return false
  }
  return true
}

// 自定义上传
const handleAvatarUpload = async (options: any) => {
  const file = options.file as File
  avatarUploading.value = true
  try {
    const res: any = await authApi.uploadAvatar(file)
    const url = res.data?.avatar_url
    if (url) {
      form.avatar_url = url
      // 同步到 userStore, 其他页面立即生效
      if (userStore.userInfo) {
        userStore.setUserInfo({ ...userStore.userInfo, avatar_url: url })
      }
      ElMessage.success('头像上传成功')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '头像上传失败')
  } finally {
    avatarUploading.value = false
  }
}

const fetchInfo = async () => {
  loading.value = true
  try {
    const res: any = await authApi.me()
    const d = res.data || {}
    Object.assign(form, {
      user_id: d.user_id,
      username: d.username,
      nickname: d.nickname || '',
      real_name: d.real_name || '',
      gender: d.gender || '',
      phone: d.phone || '',
      email: d.email || '',
      avatar_url: d.avatar_url || '',
      role: d.role,
      id_card: d.id_card || '',
      birth_date: d.birth_date || '',
      education: d.education || '',
      work_years: d.work_years ?? null,
    })
  } finally {
    loading.value = false
  }
}

const handleSave = async () => {
  if (form.phone && !/^1[3-9]\d{9}$/.test(form.phone)) {
    ElMessage.warning('手机号格式不正确')
    return
  }
  if (form.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    ElMessage.warning('邮箱格式不正确')
    return
  }
  saving.value = true
  try {
    const res: any = await authApi.updateProfile({
      nickname: form.nickname,
      real_name: form.real_name,
      gender: form.gender,
      phone: form.phone,
      email: form.email,
      avatar_url: form.avatar_url,
      id_card: form.id_card,
      education: form.education,
      work_years: form.work_years,
    })
    ElMessage.success(res.message || '保存成功')
    // 同步更新 user store
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

.avatar-upload-wrap { display: flex; flex-direction: column; align-items: flex-start; gap: 6px; }
.avatar-uploader { width: 100px; height: 100px; }
.avatar-uploader :deep(.el-upload) {
  width: 100px; height: 100px; border-radius: 50%; border: 2px dashed #d9d9d9;
  overflow: hidden; cursor: pointer; transition: border-color 0.2s; position: relative;
  display: flex; align-items: center; justify-content: center;
}
.avatar-uploader :deep(.el-upload:hover) { border-color: #1677ff; }
.avatar-preview { width: 100%; height: 100%; position: relative; border-radius: 50%; overflow: hidden; }
.avatar-img { width: 100%; height: 100%; object-fit: cover; }
.avatar-overlay {
  position: absolute; bottom: 0; left: 0; right: 0; height: 24px;
  background: rgba(0,0,0,0.5); color: #fff; font-size: 11px;
  display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.2s;
}
.avatar-preview:hover .avatar-overlay { opacity: 1; }
.avatar-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 4px;
  color: #999; font-size: 12px;
}
.avatar-loading {
  position: absolute; inset: 0; background: rgba(255,255,255,0.8); border-radius: 50%;
  display: flex; align-items: center; justify-content: center; color: #1677ff;
}
.avatar-tips { font-size: 11px; color: #999; }
</style>
