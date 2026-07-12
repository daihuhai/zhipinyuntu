<!--
  修改密码弹窗 - 已登录用户使用
-->
<template>
  <el-dialog v-model="visible" title="修改密码" width="440px" :close-on-click-modal="false">
    <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="原密码" prop="old_password">
        <el-input v-model="form.old_password" type="password" show-password placeholder="请输入原密码" />
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
      <el-button type="primary" :loading="loading" @click="handleSubmit">确认修改</el-button>
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
  old_password: '',
  new_password: '',
  confirm_password: '',
})

const rules: FormRules = {
  old_password: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
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
  form.old_password = ''
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
      const res: any = await authApi.changePassword({
        old_password: form.old_password,
        new_password: form.new_password,
      })
      ElMessage.success(res.message || '密码修改成功')
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
