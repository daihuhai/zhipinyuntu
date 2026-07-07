<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi, healthApi } from '@/api/auth'

const router = useRouter()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const healthStatus = ref<string>('')

const form = reactive({
  account: '',
  password: '',
  remember: false,
})

const rules: FormRules = {
  account: [{ required: true, message: '请输入手机号/邮箱/用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
  ],
}

const handleLogin = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res: any = await authApi.login(form)
      const data = res.data
      userStore.setToken(data.access_token)
      userStore.setUserInfo({
        user_id: data.user_id,
        username: data.username,
        nickname: data.nickname,
        role: data.role,
        avatar_url: data.avatar_url,
      })
      ElMessage.success('登录成功')
      // 清除当前焦点, 避免跳转后页面被光标整体选中
      ;(document.activeElement as HTMLElement | null)?.blur()
      window.getSelection()?.removeAllRanges()
      // 按角色跳转
      const redirectMap: Record<string, string> = {
        ROLE_SEEKER: '/seeker/dashboard',
        ROLE_EMPLOYER: '/employer/dashboard',
        ROLE_ADMIN: '/admin/dashboard',
      }
      router.push(redirectMap[data.role] || '/seeker/dashboard')
    } catch (e) {
      // 错误信息已由 axios 拦截器统一提示
    } finally {
      loading.value = false
    }
  })
}

const checkHealth = async () => {
  try {
    const res: any = await healthApi.detail()
    healthStatus.value = res.status
    ElMessage.success(`后端状态: ${res.status} | ARK API: ${res.checks.ark_api}`)
  } catch (e) {
    ElMessage.error('后端服务不可达')
    healthStatus.value = 'offline'
  }
}
</script>

<template>
  <div class="login-container">
    <!-- 左侧品牌展示区 (精简, 让视线聚焦右侧表单) -->
    <div class="brand-panel">
      <div class="brand-content">
        <div class="logo">
          <div class="logo-icon">
            <svg viewBox="0 0 100 100" width="56" height="56">
              <circle cx="50" cy="50" r="20" fill="#fff" opacity="0.9" />
              <circle cx="20" cy="30" r="8" fill="#fff" opacity="0.7" />
              <circle cx="80" cy="30" r="8" fill="#fff" opacity="0.7" />
              <circle cx="20" cy="70" r="8" fill="#fff" opacity="0.7" />
              <circle cx="80" cy="70" r="8" fill="#fff" opacity="0.7" />
              <line x1="50" y1="50" x2="20" y2="30" stroke="#fff" stroke-width="2" opacity="0.5" />
              <line x1="50" y1="50" x2="80" y2="30" stroke="#fff" stroke-width="2" opacity="0.5" />
              <line x1="50" y1="50" x2="20" y2="70" stroke="#fff" stroke-width="2" opacity="0.5" />
              <line x1="50" y1="50" x2="80" y2="70" stroke="#fff" stroke-width="2" opacity="0.5" />
            </svg>
          </div>
          <h1 class="brand-title">智聘云图</h1>
        </div>
        <p class="brand-slogan">AI 驱动的智能招聘平台</p>
        <div class="brand-features">
          <div class="feature-item">
            <span class="feature-check">✓</span>
            <span>简历智能解析 · 能力图谱可视化</span>
          </div>
          <div class="feature-item">
            <span class="feature-check">✓</span>
            <span>双向精准匹配 · 契合度量化评分</span>
          </div>
        </div>
      </div>
      <div class="brand-bg"></div>
    </div>

    <!-- 右侧登录表单区 -->
    <div class="form-panel">
      <div class="form-wrapper">
        <div class="form-header">
          <h2>欢迎登录</h2>
          <p class="subtitle">智聘云图 · 人才智能匹配平台</p>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          label-position="top"
          @keyup.enter="handleLogin"
        >
          <el-form-item prop="account">
            <el-input
              v-model="form.account"
              placeholder="手机号 / 邮箱 / 用户名"
              :prefix-icon="User"
              clearable
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="form.password"
              type="password"
              placeholder="密码"
              :prefix-icon="Lock"
              show-password
            />
          </el-form-item>
          <div class="form-options">
            <el-checkbox v-model="form.remember">记住我</el-checkbox>
            <el-link type="primary" :underline="false">忘记密码?</el-link>
          </div>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            登 录
          </el-button>
        </el-form>

        <div class="register-link">
          还没有账号?
          <router-link to="/register">立即注册 ></router-link>
        </div>

        <!-- M1 健康检查 -->
        <div class="health-check">
          <el-button text size="small" @click="checkHealth">
            检查后端服务状态
          </el-button>
          <el-tag v-if="healthStatus" :type="healthStatus === 'ok' ? 'success' : 'danger'" size="small">
            后端: {{ healthStatus }}
          </el-tag>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ===== 左侧品牌区 (精简, 仅 logo + 标语 + 2 特性) ===== */
.brand-panel {
  position: relative;
  flex: 0 0 42%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0958d9 0%, #1677ff 50%, #4096ff 100%);
  overflow: hidden;
}

.brand-content {
  position: relative;
  z-index: 2;
  color: #fff;
  padding: 60px;
  max-width: 460px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.logo-icon {
  display: flex;
  animation: float 3s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.brand-title {
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 2px;
}

.brand-slogan {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 40px;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
  opacity: 0.95;
}

.feature-check {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
}

.brand-bg {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.1) 0%, transparent 40%),
                    radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.08) 0%, transparent 40%);
  z-index: 1;
}

/* ===== 右侧表单区 (视觉权重提升, 让视线聚焦) ===== */
.form-panel {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
}

.form-wrapper {
  width: 100%;
  max-width: 420px;
  padding: 40px;
}

.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 26px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.login-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  letter-spacing: 4px;
}

.register-link {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  font-size: 14px;
}

.health-check {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px dashed var(--border-color);
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
}

@media (max-width: 900px) {
  .brand-panel { display: none; }
  .form-panel { flex: 1; }
}
</style>
