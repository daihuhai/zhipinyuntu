<script setup lang="ts">
import { onMounted, onUnmounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { messageApi } from '@/api/message'
import { vipApi } from '@/api/vip'
import { useRealtime } from '@/composables/useRealtime'

const router = useRouter()
const userStore = useUserStore()

const avatarUrl = computed(() => {
  const url = userStore.userInfo?.avatar_url
  if (!url) return ''
  return url.startsWith('http') ? url : window.location.origin + url
})
const realtime = useRealtime()
const collapsed = ref(false)
const unreadCount = ref(0)
const isVip = ref(false)
let pollTimer: ReturnType<typeof setInterval> | null = null
let offMsg: (() => void) | null = null

const menuItems = [
  { index: '/seeker/dashboard', icon: 'Odometer', title: '仪表盘', guide: '仪表盘' },
  { index: '/seeker/resume/upload', icon: 'Upload', title: '上传简历', guide: '上传简历' },
  { index: '/seeker/resume/list', icon: 'Document', title: '我的简历', guide: '我的简历' },
  { index: '/seeker/jobs', icon: 'Briefcase', title: '职位广场', guide: '职位广场' },
  { index: '/seeker/recommend', icon: 'Position', title: '结果推荐', guide: '结果推荐' },
  { index: '/seeker/graph', icon: 'Share', title: '能力图谱', guide: '能力图谱' },
  { index: '/seeker/applications', icon: 'Tickets', title: '投递记录', guide: '投递记录' },
  { index: '/seeker/feedback', icon: 'ChatLineSquare', title: '意见反馈', guide: '意见反馈' },
  { index: '/seeker/messages', icon: 'ChatDotRound', title: '消息', badge: true, guide: '消息' },
  { index: '/seeker/profile', icon: 'Setting', title: '个人设置', guide: '个人设置' },
]

const fetchUnread = async () => {
  try {
    const res: any = await messageApi.unreadCount()
    unreadCount.value = res.data?.unread_count || 0
  } catch {}
}

const fetchVipStatus = async () => {
  try {
    const res: any = await vipApi.getQuota()
    isVip.value = !!res.data?.is_vip
  } catch {
    // 忽略
  }
}

const handleSelect = (index: string) => {
  if (index === '/seeker/messages') unreadCount.value = 0
  router.push(index)
}
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
}

onMounted(() => {
  fetchUnread()
  fetchVipStatus()
  // 建立 WebSocket 实时推送, 收到新消息即刷新未读角标
  if (userStore.token) realtime.connect(userStore.token)
  offMsg = realtime.onMessage(() => fetchUnread())
  // 保留轮询兜底 (WebSocket 断开时也能获取)
  pollTimer = setInterval(fetchUnread, 15000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (offMsg) offMsg()
})
</script>

<template>
  <el-container class="layout">
    <el-aside :width="collapsed ? '64px' : '220px'" class="sidebar">
      <div class="logo">
        <img src="@/assets/logo.png" class="logo-img" alt="智聘云图" loading="lazy" />
        <span v-if="!collapsed">智聘云图</span>
      </div>
      <el-menu
        :default-active="$route.path"
        :collapse="collapsed"
        background-color="#001529"
        text-color="#ffffffb3"
        active-text-color="#fff"
        @select="handleSelect"
      >
        <el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index" :data-guide="item.guide || null">
          <el-icon><component :is="item.icon" /></el-icon>
          <template #title>
            <el-badge v-if="item.badge" :value="unreadCount" :hidden="!unreadCount" :max="99" class="menu-badge">
              {{ item.title }}
            </el-badge>
            <span v-else>{{ item.title }}</span>
          </template>
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
        <div class="header-right">
          <span v-if="isVip" class="vip-tag" @click="router.push('/seeker/vip')">
            <el-icon><GoldMedal /></el-icon>
            <span>VIP</span>
          </span>
          <span v-else class="normal-tag" @click="router.push('/seeker/vip')">普通用户</span>
          <el-dropdown>
            <span class="user-info">
              <el-avatar :size="32" :src="avatarUrl || undefined">{{ userStore.userInfo?.nickname?.[0] || 'U' }}</el-avatar>
              <span class="username">{{ userStore.userInfo?.nickname }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
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
  gap: 8px; overflow: hidden;
}
.logo-img { width: 40px; height: 40px; object-fit: contain; border-radius: 8px; flex-shrink: 0; }
.header {
  background: #fff; display: flex; align-items: center; justify-content: space-between;
  border-bottom: 1px solid var(--border-color); padding: 0 20px;
}
.header-left { display: flex; align-items: center; gap: 16px; }
.collapse-btn { font-size: 20px; cursor: pointer; }
.page-title { font-size: 16px; font-weight: 600; }
.user-info { display: flex; align-items: center; gap: 8px; cursor: pointer; }
.username { font-size: 14px; }
.header-right { display: flex; align-items: center; gap: 14px; }
.vip-tag {
  display: flex; align-items: center; gap: 4px;
  padding: 3px 10px; border-radius: 12px; cursor: pointer;
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
  color: #fff; font-size: 12px; font-weight: 700;
  box-shadow: 0 2px 6px rgba(250, 173, 20, 0.4);
  transition: transform 0.2s;
}
.vip-tag:hover { transform: scale(1.05); }
.normal-tag {
  padding: 3px 10px; border-radius: 12px; cursor: pointer;
  background: #f0f0f0; color: #8c8c8c; font-size: 12px;
  transition: all 0.2s;
}
.normal-tag:hover { background: #e6f4ff; color: #1677ff; }
.main { background: var(--bg-page); padding: 20px; overflow-y: auto; }
.menu-badge :deep(.el-badge__content) {
  background-color: #f56c6c;
  border: none;
  font-size: 11px;
  height: 18px;
  line-height: 18px;
  position: absolute;
  top: 8px;
  right: 8px;
}
:deep(.el-menu-item) {
  position: relative;
  caret-color: transparent;
  user-select: none;
}

@media (max-width: 768px) {
  .sidebar { width: 0 !important; }
  .layout { flex-direction: column; }
  .header { padding: 0 10px; }
  .main { padding: 10px; }
  .page-title { font-size: 14px; }
  .username { display: none; }
}
</style>
