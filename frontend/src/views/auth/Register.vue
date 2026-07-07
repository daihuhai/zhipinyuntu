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
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度 6-20 位', trigger: 'blur' },
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
      // 清除当前焦点, 避免跳转后页面被光标整体选中
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
    <div class="brand-panel">
      <div class="brand-content">
        <h1 class="brand-title">加入智聘云图</h1>
        <p class="brand-slogan">开启智能招聘新体验</p>
        <div class="brand-features">
          <div class="feature-item"><span class="feature-check">✓</span><span>AI 智能解析 · 能力图谱可视化</span></div>
          <div class="feature-item"><span class="feature-check">✓</span><span>智能职位推荐 · 匹配度量化</span></div>
        </div>
      </div>
    </div>

    <div class="form-panel">
      <div class="form-wrapper">
        <h2>用户注册</h2>

        <!-- 角色选择 -->
        <div class="role-switch">
          <div
            class="role-card"
            :class="{ active: form.role === 'ROLE_SEEKER' }"
            @click="form.role = 'ROLE_SEEKER'"
          >
            <el-icon size="28"><User /></el-icon>
            <div class="role-label">个人用户</div>
            <div class="role-desc">求职找工作</div>
          </div>
          <div
            class="role-card"
            :class="{ active: form.role === 'ROLE_EMPLOYER' }"
            @click="form.role = 'ROLE_EMPLOYER'"
          >
            <el-icon size="28"><OfficeBuilding /></el-icon>
            <div class="role-label">企业用户</div>
            <div class="role-desc">招聘人才</div>
          </div>
        </div>

        <el-form ref="formRef" :model="form" :rules="rules" size="large" label-position="top">
          <el-form-item prop="username">
            <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
          </el-form-item>
          <el-form-item prop="phone">
            <el-input v-model="form.phone" placeholder="手机号" :prefix-icon="Phone" />
          </el-form-item>
          <el-form-item prop="email">
            <el-input v-model="form.email" placeholder="邮箱 (选填)" :prefix-icon="Message" />
          </el-form-item>
          <el-form-item prop="password">
            <el-input v-model="form.password" type="password" placeholder="密码 (6-20位)" :prefix-icon="Lock" show-password />
          </el-form-item>
          <el-form-item prop="confirmPassword">
            <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" :prefix-icon="Lock" show-password />
          </el-form-item>

          <!-- 个人用户额外字段 -->
          <template v-if="form.role === 'ROLE_SEEKER'">
            <el-form-item>
              <el-input v-model="form.real_name" placeholder="真实姓名 (选填)" />
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
              <el-input v-model="form.company_name" placeholder="企业名称" />
            </el-form-item>
            <el-form-item prop="credit_code">
              <el-input v-model="form.credit_code" placeholder="统一社会信用代码" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.contact_person" placeholder="联系人" />
            </el-form-item>
          </template>

          <el-form-item>
            <el-checkbox v-model="form.agree">
              我已阅读并同意 <el-link type="primary" :underline="false">《用户协议》</el-link>
            </el-checkbox>
          </el-form-item>

          <el-button type="primary" class="register-btn" :loading="loading" @click="handleRegister">
            注 册
          </el-button>
        </el-form>

        <div class="login-link">
          已有账号? <router-link to="/login">返回登录 ></router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.register-container { display: flex; height: 100vh; overflow: hidden; }
.brand-panel {
  flex: 0 0 40%;
  display: flex; align-items: center; justify-content: center;
  background: linear-gradient(135deg, #0958d9 0%, #1677ff 100%);
  color: #fff;
}
.brand-content { padding: 60px; max-width: 400px; }
.brand-title { font-size: 32px; font-weight: 700; margin-bottom: 12px; }
.brand-slogan { font-size: 16px; opacity: 0.9; margin-bottom: 40px; }
.brand-features { display: flex; flex-direction: column; gap: 14px; }
.feature-item { display: flex; align-items: center; gap: 10px; font-size: 14px; }
.feature-check {
  width: 22px; height: 22px; background: rgba(255,255,255,0.2);
  border-radius: 50%; display: inline-flex; align-items: center;
  justify-content: center; font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.form-panel { flex: 1; display: flex; align-items: center; justify-content: center; background: #fff; overflow-y: auto; }
.form-wrapper { width: 100%; max-width: 420px; padding: 40px; }
.form-wrapper h2 { font-size: 24px; margin-bottom: 24px; color: var(--text-primary); }
.role-switch { display: flex; gap: 12px; margin-bottom: 24px; }
.role-card {
  flex: 1; padding: 16px; border: 2px solid var(--border-color);
  border-radius: 8px; text-align: center; cursor: pointer;
  transition: all 0.2s; display: flex; flex-direction: column; align-items: center; gap: 4px;
}
.role-card.active { border-color: var(--primary); background: rgba(22, 119, 255, 0.05); }
.role-label { font-size: 14px; font-weight: 600; margin-top: 4px; }
.role-desc { font-size: 12px; color: var(--text-secondary); }
.register-btn { width: 100%; height: 44px; font-size: 16px; letter-spacing: 4px; }
.login-link { text-align: center; margin-top: 20px; color: var(--text-secondary); font-size: 14px; }
@media (max-width: 900px) { .brand-panel { display: none; } }
</style>
