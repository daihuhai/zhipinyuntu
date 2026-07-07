<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()

const collapsed = ref(false)

const menuItems = [
  { index: '/seeker/dashboard', icon: 'Odometer', title: '仪表盘' },
  { index: '/seeker/resume/upload', icon: 'Upload', title: '上传简历' },
  { index: '/seeker/resume/list', icon: 'Document', title: '我的简历' },
  { index: '/seeker/jobs', icon: 'Briefcase', title: '职位广场' },
  { index: '/seeker/recommend', icon: 'Position', title: '结果推荐' },
  { index: '/seeker/graph', icon: 'Share', title: '能力图谱' },
  { index: '/seeker/applications', icon: 'Tickets', title: '投递记录' },
  { index: '/seeker/messages', icon: 'ChatDotRound', title: '消息' },
  { index: '/seeker/profile', icon: 'Setting', title: '个人设置' },
]

const handleSelect = (index: string) => router.push(index)
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}
</script>

<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <span v-if="!collapsed">智聘云图</span>
        <span v-else>智</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="collapsed"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#fff"
        @select="handleSelect"
      >
        <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>{{ item.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="collapsed = !collapsed">
            <Fold v-if="!collapsed" /><Expand v-else />
          </el-icon>
          <span class="page-title">{{ $route.meta.title }}</span>
        </div>
        <el-dropdown>
          <span class="user-info">
            <el-avatar :size="32">{{ userStore.userInfo?.nickname?.[0] || 'U' }}</el-avatar>
            <span class="username">{{ userStore.userInfo?.nickname }}</span>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.layout { height: 100vh; }
.sidebar { background: #001529; transition: width 0.2s; overflow: hidden; }
.logo {
  height: 60px; display: flex; align-items: center; justify-content: center;
  color: #fff; font-size: 20px; font-weight: 700; letter-spacing: 2px;
}
.header {
  background: #fff; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border-color); padding: 0 20px;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { font-size: 20px; cursor: pointer; }
.page-title { font-size: 16px; font-weight: 600; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; }
.main { background: var(--bg-page); padding: 20px; overflow-y: auto; }
</style>
