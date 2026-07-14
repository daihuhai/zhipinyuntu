<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { authApi, healthApi } from '@/api/auth'
import ForgotPasswordDialog from '@/components/ForgotPasswordDialog.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const forgotDialogRef = ref<InstanceType<typeof ForgotPasswordDialog>>()
const healthStatus = ref<string>('')

// 注册后自动填充用户名
onMounted(() => {
  const uname = route.query.username as string
  if (uname) {
    form.account = uname
  }
})

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
    <!-- ============ 左侧品牌展示区 ============ -->
    <div class="brand-panel">
      <!-- 知识图谱节点动画层 (CSS 实现) -->
      <div class="graph-canvas">
        <!-- 连线 -->
        <div class="edge edge-1"></div>
        <div class="edge edge-2"></div>
        <div class="edge edge-3"></div>
        <div class="edge edge-4"></div>
        <div class="edge edge-5"></div>
        <div class="edge edge-6"></div>
        <div class="edge edge-7"></div>
        <div class="edge edge-8"></div>
        <!-- 节点 -->
        <span class="node node-1"></span>
        <span class="node node-2"></span>
        <span class="node node-3"></span>
        <span class="node node-4"></span>
        <span class="node node-5"></span>
        <span class="node node-6"></span>
        <span class="node node-7"></span>
        <span class="node node-8"></span>
        <span class="node node-9"></span>
        <span class="node node-10"></span>
        <!-- 漂浮的小光点 -->
        <span class="dust dust-1"></span>
        <span class="dust dust-2"></span>
        <span class="dust dust-3"></span>
        <span class="dust dust-4"></span>
        <span class="dust dust-5"></span>
      </div>
      <!-- 渐变光斑 -->
      <div class="brand-bg"></div>

      <div class="brand-content">
        <div class="logo">
          <div class="logo-icon">
            <img src="@/assets/logo.png" alt="智聘云图" class="brand-logo-img" />
          </div>
          <h1 class="brand-title">智聘云图</h1>
        </div>
        <p class="brand-slogan">灵犀驱动的智能招聘平台</p>
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

        <!-- 底部数据统计 -->
        <div class="brand-stats">
          <div class="stat-item">
            <div class="stat-num"><span class="num">10</span><span class="unit">万+</span></div>
            <div class="stat-label">在线简历</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-num"><span class="num">5000</span><span class="unit">+</span></div>
            <div class="stat-label">合作企业</div>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <div class="stat-num"><span class="num">98</span><span class="unit">%</span></div>
            <div class="stat-label">匹配准确率</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ============ 右侧登录表单区 ============ -->
    <div class="form-panel">
      <!-- 几何纹理背景 -->
      <div class="form-bg"></div>

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
            <el-link type="primary" :underline="false" @click="forgotDialogRef?.open()">忘记密码?</el-link>
          </div>
          <el-button
            type="primary"
            class="login-btn"
            :loading="loading"
            @click="handleLogin"
          >
            <span class="btn-text">登 录</span>
          </el-button>
        </el-form>

        <div class="register-link">
          还没有账号?
          <router-link to="/register">立即注册 &gt;</router-link>
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

    <!-- 忘记密码弹窗 -->
    <ForgotPasswordDialog ref="forgotDialogRef" />
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ============ 左侧品牌区 ============ */
.brand-panel {
  position: relative;
  flex: 0 0 44%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0958d9 0%, #1677ff 50%, #4096ff 100%);
  overflow: hidden;
}

/* 知识图谱节点画布 */
.graph-canvas {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

/* 节点样式 */
.node {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.6), 0 0 24px rgba(180, 220, 255, 0.4);
}
.node::after {
  content: '';
  position: absolute;
  inset: -8px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.25);
  animation: nodePulse 3s ease-in-out infinite;
}
.node-1  { width: 10px; height: 10px; top: 18%; left: 22%; animation: floatNode 7s ease-in-out infinite; }
.node-2  { width: 14px; height: 14px; top: 28%; left: 68%; animation: floatNode 9s ease-in-out infinite 0.5s; }
.node-3  { width: 8px;  height: 8px;  top: 45%; left: 12%; animation: floatNode 8s ease-in-out infinite 1s; }
.node-4  { width: 12px; height: 12px; top: 55%; left: 78%; animation: floatNode 10s ease-in-out infinite 1.5s; }
.node-5  { width: 10px; height: 10px; top: 72%; left: 28%; animation: floatNode 7.5s ease-in-out infinite 0.8s; }
.node-6  { width: 8px;  height: 8px;  top: 80%; left: 60%; animation: floatNode 9.5s ease-in-out infinite 2s; }
.node-7  { width: 6px;  height: 6px;  top: 12%; left: 48%; animation: floatNode 6.5s ease-in-out infinite 1.2s; }
.node-8  { width: 9px;  height: 9px;  top: 38%; left: 42%; animation: floatNode 8.5s ease-in-out infinite 0.3s; }
.node-9  { width: 7px;  height: 7px;  top: 62%; left: 50%; animation: floatNode 7.8s ease-in-out infinite 1.7s; }
.node-10 { width: 11px; height: 11px; top: 88%; left: 14%; animation: floatNode 9.2s ease-in-out infinite 0.6s; }

@keyframes nodePulse {
  0%, 100% { transform: scale(1); opacity: 0.8; }
  50%      { transform: scale(1.6); opacity: 0; }
}
@keyframes floatNode {
  0%, 100% { transform: translate(0, 0); }
  25%      { transform: translate(8px, -10px); }
  50%      { transform: translate(-6px, 6px); }
  75%      { transform: translate(4px, 8px); }
}

/* 连线 */
.edge {
  position: absolute;
  height: 1px;
  background: linear-gradient(90deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.45), rgba(255, 255, 255, 0.05));
  transform-origin: 0 50%;
  animation: edgeFlow 4s ease-in-out infinite;
}
.edge-1 { top: 19%; left: 22%; width: 30%; transform: rotate(-12deg); animation-delay: 0s; }
.edge-2 { top: 29%; left: 68%; width: 22%; transform: rotate(155deg); animation-delay: 0.4s; }
.edge-3 { top: 46%; left: 12%; width: 32%; transform: rotate(-8deg); animation-delay: 0.8s; }
.edge-4 { top: 56%; left: 50%; width: 30%; transform: rotate(4deg); animation-delay: 1.2s; }
.edge-5 { top: 73%; left: 28%; width: 34%; transform: rotate(-6deg); animation-delay: 1.6s; }
.edge-6 { top: 39%; left: 42%; width: 28%; transform: rotate(28deg); animation-delay: 2s; }
.edge-7 { top: 63%; left: 50%; width: 22%; transform: rotate(78deg); animation-delay: 2.4s; }
.edge-8 { top: 88%; left: 14%; width: 26%; transform: rotate(-22deg); animation-delay: 2.8s; }

@keyframes edgeFlow {
  0%, 100% { opacity: 0.3; }
  50%      { opacity: 0.9; }
}

/* 漂浮光点 */
.dust {
  position: absolute;
  width: 4px; height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
}
.dust-1 { top: 25%; left: 35%; animation: dustFloat 12s linear infinite; }
.dust-2 { top: 60%; left: 65%; animation: dustFloat 14s linear infinite 2s; }
.dust-3 { top: 80%; left: 40%; animation: dustFloat 16s linear infinite 4s; }
.dust-4 { top: 35%; left: 85%; animation: dustFloat 13s linear infinite 6s; }
.dust-5 { top: 50%; left: 25%; animation: dustFloat 15s linear infinite 8s; }

@keyframes dustFloat {
  0%   { transform: translate(0, 0); opacity: 0; }
  20%  { opacity: 1; }
  80%  { opacity: 1; }
  100% { transform: translate(60px, -120px); opacity: 0; }
}

/* 品牌内容 */
.brand-content {
  position: relative;
  z-index: 2;
  color: #fff;
  padding: 60px;
  max-width: 480px;
  width: 100%;
}

.logo {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  animation: slideInLeft 0.8s ease-out both;
}

.logo-icon {
  display: flex;
  animation: float 3s ease-in-out infinite;
  filter: drop-shadow(0 6px 16px rgba(0, 0, 0, 0.25));
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50%      { transform: translateY(-8px); }
}

/* 品牌 Logo 图片 */
.brand-logo-img {
  width: 80px; height: 80px; object-fit: contain;
  border-radius: 16px;
  filter: drop-shadow(0 4px 12px rgba(255, 255, 255, 0.3));
}

@keyframes slideInLeft {
  from { opacity: 0; transform: translateX(-30px); }
  to   { opacity: 1; transform: translateX(0); }
}

.brand-title {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: 2px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.2);
}

.brand-slogan {
  font-size: 16px;
  opacity: 0.92;
  margin-bottom: 40px;
  animation: slideInLeft 0.8s ease-out 0.1s both;
}

.brand-features {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 56px;
  animation: slideInLeft 0.8s ease-out 0.2s both;
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
  backdrop-filter: blur(4px);
}

/* 数据统计 */
.brand-stats {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 24px 28px;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 14px;
  animation: slideInUp 0.9s ease-out 0.4s both;
}

@keyframes slideInUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}

.stat-item { flex: 1; text-align: center; }
.stat-num {
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 2px;
  line-height: 1;
}
.stat-num .num {
  font-size: 26px;
  font-weight: 700;
  color: #fff;
  font-family: 'DIN Alternate', 'Helvetica Neue', Arial, sans-serif;
  animation: countUp 1.4s cubic-bezier(0.2, 0.8, 0.2, 1) 0.6s both;
}
.stat-num .unit {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.85);
  margin-left: 2px;
}
.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  margin-top: 6px;
  letter-spacing: 0.5px;
}
.stat-divider {
  width: 1px;
  height: 32px;
  background: rgba(255, 255, 255, 0.2);
  flex-shrink: 0;
}

/* 数字滚动入场动画 (透明度 + 位移) */
@keyframes countUp {
  0%   { opacity: 0; transform: translateY(14px); letter-spacing: 4px; }
  100% { opacity: 1; transform: translateY(0); letter-spacing: 0; }
}

/* 渐变光斑背景 */
.brand-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  background-image:
    radial-gradient(circle at 20% 30%, rgba(255, 255, 255, 0.12) 0%, transparent 40%),
    radial-gradient(circle at 80% 70%, rgba(255, 255, 255, 0.08) 0%, transparent 40%),
    radial-gradient(circle at 50% 50%, rgba(186, 230, 253, 0.1) 0%, transparent 50%);
}

/* ============ 右侧表单区 ============ */
.form-panel {
  position: relative;
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff;
  overflow: hidden;
}

/* 几何纹理背景 (极淡) */
.form-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(22, 119, 255, 0.04) 0%, transparent 35%),
    radial-gradient(circle at 80% 80%, rgba(124, 58, 237, 0.04) 0%, transparent 35%),
    linear-gradient(45deg, transparent 48%, rgba(22, 119, 255, 0.025) 49%, rgba(22, 119, 255, 0.025) 51%, transparent 52%),
    linear-gradient(-45deg, transparent 48%, rgba(124, 58, 237, 0.025) 49%, rgba(124, 58, 237, 0.025) 51%, transparent 52%);
  background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
}

.form-wrapper {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 420px;
  padding: 40px;
  animation: fadeInForm 0.7s ease-out both;
}

@keyframes fadeInForm {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.form-header {
  margin-bottom: 32px;
}

.form-header h2 {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
}

/* ============ 输入框聚焦动画 ============ */
.form-wrapper :deep(.el-input__wrapper) {
  border-radius: 10px;
  height: 48px;
  padding: 0 14px;
  background: #fff;
  border: 1.5px solid var(--border-color);
  box-shadow: none !important;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.form-wrapper :deep(.el-input__wrapper:hover) {
  border-color: var(--primary-hover);
}
.form-wrapper :deep(.el-input__wrapper.is-focus),
.form-wrapper :deep(.el-input__wrapper:focus-within) {
  border-color: var(--primary) !important;
  box-shadow: 0 0 0 4px rgba(22, 119, 255, 0.12), 0 4px 12px rgba(22, 119, 255, 0.08) !important;
  transform: translateY(-1px);
}
.form-wrapper :deep(.el-input__inner) {
  height: 48px;
  line-height: 48px;
  font-size: 14px;
}
.form-wrapper :deep(.el-input__prefix-inner) {
  color: var(--text-secondary);
  margin-right: 8px;
  transition: color 0.3s ease, transform 0.3s ease;
}
.form-wrapper :deep(.el-input__wrapper.is-focus .el-input__prefix-inner),
.form-wrapper :deep(.el-input__wrapper:focus-within .el-input__prefix-inner) {
  color: var(--primary);
  transform: scale(1.1);
}
.form-wrapper :deep(.el-input__suffix-inner) {
  color: var(--text-secondary);
  transition: color 0.3s ease;
}
.form-wrapper :deep(.el-input__wrapper.is-focus .el-input__suffix-inner) {
  color: var(--primary);
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

/* ============ 登录按钮 (渐变 + 悬停光效) ============ */
.login-btn {
  width: 100%;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 6px;
  border: none !important;
  border-radius: 10px;
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 50%, #7c3aed 100%) !important;
  color: #fff !important;
  box-shadow: 0 8px 20px rgba(22, 119, 255, 0.32), 0 2px 6px rgba(124, 58, 237, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}
.login-btn:hover {
  background: linear-gradient(135deg, #4096ff 0%, #69b1ff 50%, #8b5cf6 100%) !important;
  box-shadow: 0 12px 28px rgba(22, 119, 255, 0.45), 0 4px 10px rgba(124, 58, 237, 0.3);
  transform: translateY(-2px);
}
.login-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
}
/* 按钮光泽划过 */
.login-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 50%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transition: left 0.7s ease;
  pointer-events: none;
}
.login-btn:hover::before { left: 130%; }
.btn-text { position: relative; z-index: 1; }

.register-link {
  text-align: center;
  margin-top: 24px;
  color: var(--text-secondary);
  font-size: 14px;
}
.register-link a {
  font-weight: 500;
  transition: color 0.2s;
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

/* ============ 响应式 ============ */
@media (max-width: 900px) {
  .brand-panel { display: none; }
  .form-panel { flex: 1; }
}
</style>
