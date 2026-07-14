<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)

const menuItems = [
  { index: '/admin/dashboard', icon: 'Odometer', title: '数据指挥中心' },
  { index: '/admin/users', icon: 'User', title: '用户管理' },
  { index: '/admin/resumes', icon: 'Document', title: '简历管理' },
  { index: '/admin/jobs', icon: 'Briefcase', title: '职位管理' },
  { index: '/admin/vip', icon: 'GoldMedal', title: 'VIP 管理' },
  { index: '/admin/revenue', icon: 'Money', title: '营收监控' },
  { index: '/admin/logs', icon: 'Tickets', title: '操作日志' },
  { index: '/admin/feedbacks', icon: 'ChatLineSquare', title: '反馈管理' },
]
const handleSelect = (index: string) => router.push(index)
const handleLogout = () => { userStore.logout(); router.push('/login') }
</script>

<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <img src="@/assets/logo.png" class="logo-img" alt="智聘云图" />
        <span v-if="!collapsed">管理后台</span>
      </div>
      <el-menu :default-active="$route.path" :collapse="collapsed" background-color="#001529" text-color="#ffffffb3" active-text-color="#fff" @select="handleSelect">
        <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed"><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
          <span class="page-title">{{ $route.meta.title }}</span>
        </div>
        <el-dropdown>
          <span class="user-info">
            <el-avatar :size="32">A</el-avatar>
            <span class="username">管理员</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown><el-dropdown-menu><el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item></el-dropdown-menu></template>
        </el-dropdown>
      </el-header>
      <el-main class="main"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout { height: 100vh; }
.sidebar { background: #001529; transition: width 0.2s; overflow: hidden; }
.logo { height: 60px; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 18px; font-weight: 700; gap: 8px; overflow: hidden; }
.logo-img { width: 40px; height: 40px; object-fit: contain; border-radius: 8px; flex-shrink: 0; }
.header { background: #fff; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid var(--border-color); padding: 0 20px; }
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { font-size: 20px; cursor: pointer; }
.page-title { font-size: 16px; font-weight: 600; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; }
.main { background: var(--bg-page); padding: 20px; overflow-y: auto; }
:deep(.el-menu-item) { caret-color: transparent; user-select: none; }

@media (max-width: 768px) {
  .sidebar { width: 0 !important; }
  .layout { flex-direction: column; }
  .header { padding: 0 10px; }
  .main { padding: 10px; }
  .page-title { font-size: 14px; }
  .username { display: none; }
}
</style>
