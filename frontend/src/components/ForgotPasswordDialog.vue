<!--
  忘记密码弹窗 - 登录页使用, 通过用户名+手机号验证
-->
<template>
  <el-dialog v-model="visible" title="找回密码" width="440px" :close-on-click-modal="false">
    <el-alert type="info" :closable="false" style="margin-bottom: 16px">
      通过注册时的用户名和手机号验证身份后重置密码
    </el-alert>
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名" clearable />
      </el-form-item>
      <el-form-item label="手机号" prop="phone">
        <el-input v-model="form.phone" placeholder="注册时填写的手机号" clearable />
      </el-form-item>
      <el-form-item label="新密码" prop="new_password">
        <el-input v-model="form.new_password" type="password" show-password placeholder="至少8位, 含字母+数字" />
      </el-form-item>
      <el-form-item label="确认密码" prop="confirm_password">
        <el-input v-model="form.confirm_password" type="password" show-password placeholder="再次输入新密码" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">重置密码</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { authApi } from '@/api/auth'

const visible = ref(false)
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  phone: '',
  new_password: '',
  confirm_password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  phone: [
    { required: true, message: '请输入手机号', trigger: 'blur' },
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' },
  ],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
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
  confirm_password: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.new_password) callback(new Error('两次密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

const open = () => {
  form.username = ''
  form.phone = ''
  form.new_password = ''
  form.confirm_password = ''
  visible.value = true
}

const emit = defineEmits<{
  (e: 'success'): void
}>()

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    loading.value = true
    try {
      const res: any = await authApi.forgotPassword({
        username: form.username,
        phone: form.phone,
        new_password: form.new_password,
      })
      ElMessage.success(res.message || '密码重置成功')
      visible.value = false
      emit('success')
    } catch (e: any) {
      // 错误已由 request 拦截器处理
    } finally {
      loading.value = false
    }
  })
}

defineExpose({ open })
</script>
