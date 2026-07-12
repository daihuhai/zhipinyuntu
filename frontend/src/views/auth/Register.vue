<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { User, Lock, Phone, Message, OfficeBuilding } from '@element-plus/icons-vue'
import { authApi } from '@/api/auth'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  role: 'ROLE_SEEKER' as 'ROLE_SEEKER' | 'ROLE_EMPLOYER',
  username: '',
  phone: '',
  email: '',
  password: '',
  confirmPassword: '',
  agree: false,
  // 个人用户
  real_name: '',
  gender: '男',
  nickname: '',
  // 企业用户
  company_name: '',
  credit_code: '',
  contact_person: '',
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 64, message: '用户名长度 3-64 位', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, max: 64, message: '密码长度 8-64 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (!/[A-Za-z]/.test(value)) callback(new Error('密码必须包含至少一个字母'))
        else if (!/\d/.test(value)) callback(new Error('密码必须包含至少一个数字'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  confirmPassword: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
  company_name: [{ required: true, message: '请输入企业名称', trigger: 'blur' }],
  credit_code: [{ required: true, message: '请输入统一社会信用代码', trigger: 'blur' }],
}

// 密码强度计算 (0-4)
const passwordStrength = ref(0)
const calcStrength = (pwd: string) => {
  let score = 0
  if (pwd.length >= 8) score++
  if (pwd.length >= 12) score++
  if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score++
  if (/\d/.test(pwd) && /[^A-Za-z0-9]/.test(pwd)) score++
  return Math.min(score, 4)
}
const onPasswordInput = () => {
  passwordStrength.value = calcStrength(form.password)
}
const strengthLabels = ['弱', '弱', '中', '强', '极强']
const strengthColors = ['#ff4d4f', '#ff4d4f', '#faad14', '#52c41a', '#52c41a']

const handleRegister = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    if (!form.agree) {
      ElMessage.warning('请先同意用户协议')
      return
    }
    loading.value = true
    try {
      const payload: any = {
        username: form.username,
        password: form.password,
        role: form.role,
        phone: form.phone,
        email: form.email || undefined,
      }
      if (form.role === 'ROLE_SEEKER') {
        payload.real_name = form.real_name || undefined
        payload.nickname = form.nickname || form.real_name || undefined
        payload.gender = form.gender
      } else {
        payload.company_name = form.company_name
        payload.credit_code = form.credit_code
        payload.contact_person = form.contact_person || undefined
        payload.nickname = form.company_name
      }
      await authApi.register(payload)
      ElMessage.success('注册成功, 即将跳转登录')
      ;(document.activeElement as HTMLElement | null)?.blur()
      window.getSelection()?.removeAllRanges()
      setTimeout(() => router.push('/login'), 1200)
    } catch (e) {
      // 错误信息已由 axios 拦截器统一提示
    } finally {
      loading.value = false
    }
  })
}
</script>

<template>
  <div class="register-container">
    <!-- ============ 左侧品牌展示区 ============ -->
    <div class="brand-panel">
      <!-- 知识图谱节点动画层 (CSS 实现) -->
      <div class="graph-canvas">
        <div class="edge edge-1"></div>
        <div class="edge edge-2"></div>
        <div class="edge edge-3"></div>
        <div class="edge edge-4"></div>
        <div class="edge edge-5"></div>
        <div class="edge edge-6"></div>
        <div class="edge edge-7"></div>
        <div class="edge edge-8"></div>
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
        <span class="dust dust-1"></span>
        <span class="dust dust-2"></span>
        <span class="dust dust-3"></span>
        <span class="dust dust-4"></span>
        <span class="dust dust-5"></span>
      </div>
      <div class="brand-bg"></div>

      <div class="brand-content">
        <div class="logo">
          <div class="logo-icon">
            <img src="@/assets/logo.png" alt="智聘云图" class="brand-logo-img" />
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

    <!-- ============ 右侧注册表单区 ============ -->
    <div class="form-panel">
      <div class="form-bg"></div>

      <div class="form-wrapper">
        <div class="form-header">
          <h2>创建账号</h2>
          <p class="subtitle">智聘云图 · 人才智能匹配平台</p>
        </div>

        <!-- 角色选择 -->
        <div class="role-switch">
          <div
            class="role-card"
            :class="{ active: form.role === 'ROLE_SEEKER' }"
            @click="form.role = 'ROLE_SEEKER'"
          >
            <div class="role-icon">
              <el-icon size="20"><User /></el-icon>
            </div>
            <div class="role-text">
              <div class="role-label">个人用户</div>
              <div class="role-desc">求职找工作</div>
            </div>
          </div>
          <div
            class="role-card"
            :class="{ active: form.role === 'ROLE_EMPLOYER' }"
            @click="form.role = 'ROLE_EMPLOYER'"
          >
            <div class="role-icon">
              <el-icon size="20"><OfficeBuilding /></el-icon>
            </div>
            <div class="role-text">
              <div class="role-label">企业用户</div>
              <div class="role-desc">招聘人才</div>
            </div>
          </div>
        </div>

        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          size="large"
          label-position="top"
          @keyup.enter="handleRegister"
        >
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" clearable />
          </el-form-item>
          <el-form-item prop="phone">
            <el-input v-model="form.phone" placeholder="手机号" :prefix-icon="Phone" clearable />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱 (选填)" :prefix-icon="Message" clearable />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码 (至少8位, 含字母+数字)" :prefix-icon="Lock" show-password @input="onPasswordInput" />
          </el-form-item>

          <!-- 密码强度提示 -->
          <div class="pwd-strength" v-if="form.password">
            <div class="strength-bars">
              <span
                v-for="i in 4"
                :key="i"
                class="bar"
                :style="{ backgroundColor: passwordStrength >= i ? strengthColors[passwordStrength] : 'rgba(255,255,255,0.15)' }"
              ></span>
            </div>
            <span class="strength-label" :style="{ color: strengthColors[passwordStrength] }">
              {{ strengthLabels[passwordStrength] }}
            </span>
          </div>

          <el-form-item prop="confirmPassword" class="mt-2">
            <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password />
          </el-form-item>

          <!-- 个人用户额外字段 -->
          <template v-if="form.role === 'ROLE_SEEKER'">
            <el-form-item>
              <el-input v-model="form.real_name" placeholder="真实姓名 (选填)" clearable />
            </el-form-item>
            <el-form-item>
              <el-radio-group v-model="form.gender">
                <el-radio value="男">男</el-radio>
                <el-radio value="女">女</el-radio>
              </el-radio-group>
            </el-form-item>
          </template>

          <!-- 企业用户额外字段 -->
          <template v-if="form.role === 'ROLE_EMPLOYER'">
            <el-form-item prop="company_name">
              <el-input v-model="form.company_name" placeholder="企业名称" clearable />
            </el-form-item>
            <el-form-item prop="credit_code">
              <el-input v-model="form.credit_code" placeholder="统一社会信用代码" clearable />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.contact_person" placeholder="联系人" clearable />
            </el-form-item>
          </template>

          <el-form-item>
            <el-checkbox v-model="form.agree">
              我已阅读并同意 <el-link type="primary" :underline="false">《用户协议》</el-link>
            </el-checkbox>
          </el-form-item>

          <el-button type="primary" class="register-btn" :loading="loading" @click="handleRegister">
            <span class="btn-text">注 册</span>
          </el-button>
        </el-form>

        <div class="login-link">
          已有账号?
          <router-link to="/login">返回登录 &gt;</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* ============ 左侧品牌区 (与登录页完全一致) ============ */
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

@keyframes countUp {
  0%   { opacity: 0; transform: translateY(14px); letter-spacing: 4px; }
  100% { opacity: 1; transform: translateY(0); letter-spacing: 0; }
}

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
  max-width: 440px;
  padding: 32px 40px;
  max-height: 100vh;
  overflow-y: auto;
  animation: fadeInForm 0.7s ease-out both;
}

.form-wrapper::-webkit-scrollbar { width: 4px; }
.form-wrapper::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 2px; }

@keyframes fadeInForm {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}

.form-header {
  margin-bottom: 20px;
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

/* ============ 角色选择卡片 ============ */
.role-switch {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
}

.role-card {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #fafafa;
  border: 1.5px solid var(--border-color);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.role-card:hover {
  border-color: var(--primary-hover);
  background: #f0f5ff;
}

.role-card.active {
  background: linear-gradient(135deg, rgba(22, 119, 255, 0.06) 0%, rgba(64, 150, 255, 0.06) 100%);
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.12);
}

.role-icon {
  display: flex;
  width: 34px; height: 34px;
  align-items: center; justify-content: center;
  background: #fff;
  border-radius: 8px;
  color: var(--text-secondary);
  flex-shrink: 0;
  transition: all 0.25s;
  border: 1px solid var(--border-color);
}

.role-card.active .role-icon {
  background: linear-gradient(135deg, #1677ff 0%, #4096ff 100%);
  color: #fff;
  border-color: transparent;
}

.role-text { flex: 1; min-width: 0; }
.role-label { font-size: 13px; font-weight: 600; color: var(--text-primary); }
.role-desc { font-size: 11px; color: var(--text-secondary); margin-top: 1px; }

/* ============ 输入框样式 ============ */
.form-wrapper :deep(.el-form-item) { margin-bottom: 14px; }
.form-wrapper :deep(.el-form-item__label) {
  color: var(--text-primary) !important;
  font-size: 13px;
  font-weight: 500;
  padding-bottom: 4px;
}
.form-wrapper :deep(.el-form-item__error) {
  font-size: 12px;
  padding-top: 4px;
}
.mt-2 { margin-top: 4px; }

.form-wrapper :deep(.el-input__wrapper) {
  border-radius: 10px;
  height: 44px;
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
  height: 44px;
  line-height: 44px;
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

/* 单选框 */
.form-wrapper :deep(.el-radio__label) { color: var(--text-primary); font-size: 13px; }
.form-wrapper :deep(.el-radio__input.is-checked .el-radio__inner) {
  background: #1677ff;
  border-color: #1677ff;
}

/* 复选框 */
.form-wrapper :deep(.el-checkbox__label) { color: var(--text-secondary); font-size: 13px; }
.form-wrapper :deep(.el-checkbox__inner) {
  border-radius: 4px;
}
.form-wrapper :deep(.el-checkbox__input.is-checked .el-checkbox__inner) {
  background: #1677ff;
  border-color: #1677ff;
}

/* ============ 密码强度提示 ============ */
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: -6px 0 8px;
  padding: 0 2px;
}
.strength-bars {
  display: flex;
  gap: 4px;
  flex: 1;
}
.strength-bars .bar {
  flex: 1;
  height: 3px;
  background: #f0f0f0;
  border-radius: 2px;
  transition: background 0.3s ease;
}
.strength-bars .bar.weak { background: #f87171; }
.strength-bars .bar.medium { background: #fbbf24; }
.strength-bars .bar.strong { background: #34d399; }
.strength-label {
  font-size: 12px;
  font-weight: 500;
  min-width: 22px;
  text-align: right;
}
.strength-label.weak { color: #f87171; }
.strength-label.medium { color: #fbbf24; }
.strength-label.strong { color: #34d399; }

/* ============ 注册按钮 ============ */
.register-btn {
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
.register-btn:hover {
  background: linear-gradient(135deg, #4096ff 0%, #69b1ff 50%, #8b5cf6 100%) !important;
  box-shadow: 0 12px 28px rgba(22, 119, 255, 0.45), 0 4px 10px rgba(124, 58, 237, 0.3);
  transform: translateY(-2px);
}
.register-btn:active {
  transform: translateY(0);
  box-shadow: 0 4px 12px rgba(22, 119, 255, 0.3);
}
.register-btn::before {
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
.register-btn:hover::before { left: 130%; }
.btn-text { position: relative; z-index: 1; }

.login-link {
  text-align: center;
  margin-top: 20px;
  color: var(--text-secondary);
  font-size: 14px;
}
.login-link a {
  font-weight: 500;
  transition: color 0.2s;
}

/* ============ 响应式 ============ */
@media (max-width: 900px) {
  .brand-panel { display: none; }
  .form-panel { flex: 1; }
}
@media (max-width: 500px) {
  .form-wrapper { padding: 24px 18px; }
  .form-header h2 { font-size: 24px; }
  .role-desc { display: none; }
}
</style>
