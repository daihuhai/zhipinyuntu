<!--
  个人设置 (求职者)
-->
<template>
  <div class="profile-page">
    <el-card shadow="never" class="profile-card">
      <template #header><div class="card-header">个人信息</div></template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="用户名">{{ userInfo?.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ userInfo?.nickname || '-' }}</el-descriptions-item>
        <el-descriptions-item label="角色">
          <el-tag>{{ roleText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="用户 ID">{{ userInfo?.user_id }}</el-descriptions-item>
      </el-descriptions>
      <div class="tips">
        <el-alert type="info" :closable="false" show-icon>
          个人信息维护功能将在后续版本开放。如需修改, 请联系管理员。
        </el-alert>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const userInfo = computed(() => userStore.userInfo)
const roleText = computed(() => ({
  ROLE_SEEKER: '个人用户',
  ROLE_EMPLOYER: '企业用户',
  ROLE_ADMIN: '管理员',
}[userInfo.value?.role || ''] || '未知'))
</script>

<style scoped>
.profile-page { max-width: 800px; margin: 0 auto; }
.profile-card { border-radius: 12px; }
.card-header { font-weight: 600; }
.tips { margin-top: 16px; }
</style>
