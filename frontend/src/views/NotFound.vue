<!--
  404 页面 - 简洁科技风
-->
<template>
  <div class="not-found">
    <div class="content">
      <div class="code">404</div>
      <h2>页面走丢了</h2>
      <p>您访问的页面不存在,可能已被移除或地址输入有误。</p>
      <div class="actions">
        <el-button type="primary" :icon="HomeFilled" @click="goHome">返回首页</el-button>
        <el-button :icon="Back" plain @click="$router.back()">返回上一页</el-button>
      </div>
    </div>
    <div class="bg-pattern"></div>
  </div>
</template>

<script setup lang="ts">
import { HomeFilled, Back } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  const token = localStorage.getItem('access_token')
  router.push(token ? '/seeker/dashboard' : '/login')
}
</script>

<style scoped>
.not-found {
  position: relative;
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f0f5ff 0%, #e6f4ff 100%);
  overflow: hidden;
}
.content {
  text-align: center;
  z-index: 2;
  position: relative;
}
.code {
  font-size: 160px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, #1677ff 0%, #722ed1 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -4px;
  margin-bottom: 16px;
}
h2 {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 8px;
}
p {
  color: var(--text-secondary);
  margin-bottom: 24px;
}
.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
.bg-pattern {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(circle, #1677ff15 1.5px, transparent 1.5px);
  background-size: 32px 32px;
  z-index: 1;
}
</style>
