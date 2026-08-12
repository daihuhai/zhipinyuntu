<!--
  消息中心 - 求职者与企业共用
  左侧会话列表 + 右侧聊天窗口
-->
<template>
  <div class="message-page">
    <!-- 左侧会话列表 -->
    <div class="conv-panel">
      <div class="conv-header">
        <span>消息</span>
        <el-badge :value="unreadTotal" :hidden="!unreadTotal" :max="99">
          <el-icon :size="18"><ChatDotRound /></el-icon>
        </el-badge>
      </div>
      <div class="conv-list" v-loading="convLoading">
        <div
          v-for="conv in conversations"
          :key="conv.user_id"
          class="conv-item"
          :class="{ active: activeUserId === conv.user_id }"
          @click="selectConv(conv.user_id)"
        >
          <el-avatar :size="40" :src="resolveAvatar(conv.user_avatar_url)" class="conv-avatar">
            {{ (conv.user_name || '?')[0] }}
          </el-avatar>
          <div class="conv-body">
            <div class="conv-top">
              <span class="conv-name">{{ conv.user_name }}</span>
              <span class="conv-time">{{ formatTime(conv.last_time) }}</span>
            </div>
            <div class="conv-bottom">
              <span class="conv-last">{{ conv.last_message }}</span>
              <el-badge v-if="conv.unread_count" :value="conv.unread_count" :max="99" class="conv-badge" />
            </div>
          </div>
        </div>
        <el-empty v-if="!convLoading && !conversations.length" description="暂无消息" :image-size="60" />
      </div>
    </div>

    <!-- 右侧聊天窗口 -->
    <div class="chat-panel">
      <template v-if="activeUserId">
        <div class="chat-header">
          <span class="chat-title">{{ otherInfo?.user_name || '聊天' }}</span>
          <el-tag v-if="otherInfo?.user_role" size="small" type="info">
            {{ roleText(otherInfo.user_role) }}
          </el-tag>
        </div>
        <div ref="chatBodyRef" class="chat-body" v-loading="msgLoading">
          <template v-for="(msg, idx) in messages" :key="msg.id">
            <!-- 时间分隔线 (微信风格: 相邻消息间隔>3分钟时显示居中时间) -->
            <div v-if="showTimeDivider(idx)" class="time-divider">
              <span>{{ formatTime(msg.created_at) }}</span>
            </div>
            <div
              class="msg-row"
              :class="{ mine: msg.sender_id === currentUserId }"
            >
              <el-avatar :size="32" :src="resolveMsgAvatar(msg)" class="msg-avatar">
                {{ (msg.sender_name || '?')[0] }}
              </el-avatar>
              <div class="msg-content">
                <div class="msg-bubble">{{ msg.content }}</div>
              </div>
            </div>
          </template>
          <el-empty v-if="!msgLoading && !messages.length" description="开始对话吧" :image-size="60" />
        </div>
        <div class="chat-input">
          <el-input
            v-model="inputText"
            type="textarea"
            :rows="2"
            placeholder="输入消息, Enter 发送, Shift+Enter 换行"
            resize="none"
            @keydown.enter.exact.prevent="send"
          />
          <el-button type="primary" :icon="Promotion" :loading="sending" @click="send">发送</el-button>
        </div>
      </template>
      <el-empty v-else description="选择一个会话开始聊天" class="chat-empty" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Promotion } from '@element-plus/icons-vue'
import { messageApi } from '@/api/message'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const userStore = useUserStore()
const currentUserId = userStore.userInfo?.user_id || 0

const conversations = ref<any[]>([])
const convLoading = ref(false)
const activeUserId = ref<number | null>(null)
const messages = ref<any[]>([])
const msgLoading = ref(false)
const inputText = ref('')
const sending = ref(false)
const otherInfo = ref<any>(null)
const unreadTotal = ref(0)
const chatBodyRef = ref<HTMLElement>()

// 当前用户头像 URL (从全局状态获取, 修改头像后会自动同步)
const myAvatarUrl = computed(() => userStore.userInfo?.avatar_url || '')

// 将后端返回的相对路径头像 URL 转为可访问的绝对路径
const resolveAvatar = (url?: string | null): string => {
  if (!url) return ''
  if (url.startsWith('http')) return url
  return window.location.origin + url
}

// 根据消息发送者解析头像: 自己的消息用全局状态中的头像, 对方的消息用 otherInfo 中的头像
const resolveMsgAvatar = (msg: any): string => {
  if (msg.sender_id === currentUserId) {
    return resolveAvatar(myAvatarUrl.value)
  }
  return resolveAvatar(otherInfo.value?.user_avatar_url)
}

const roleText = (role: string) =>
  ({ ROLE_SEEKER: '求职者', ROLE_EMPLOYER: '企业', ROLE_ADMIN: '管理员' }[role] || role)

const formatTime = (iso?: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) {
    return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
  }
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

// 微信风格: 首条消息显示时间, 或与上一条间隔>3分钟时显示居中时间分隔线
const showTimeDivider = (idx: number) => {
  if (idx === 0) return true
  const cur = new Date(messages.value[idx].created_at).getTime()
  const prev = new Date(messages.value[idx - 1].created_at).getTime()
  return cur - prev > 3 * 60 * 1000
}

const fetchConversations = async () => {
  convLoading.value = true
  try {
    const res: any = await messageApi.conversations()
    conversations.value = res.data?.items || []
    unreadTotal.value = conversations.value.reduce((s, c) => s + (c.unread_count || 0), 0)
  } finally {
    convLoading.value = false
  }
}

const selectConv = async (userId: number) => {
  activeUserId.value = userId
  msgLoading.value = true
  try {
    const res: any = await messageApi.messagesWith(userId)
    messages.value = res.data?.items || []
    otherInfo.value = res.data?.other
    await nextTick()
    scrollToBottom()
    fetchConversations() // 刷新未读数
  } finally {
    msgLoading.value = false
  }
}

const send = async () => {
  if (!inputText.value.trim() || !activeUserId.value) return
  sending.value = true
  try {
    await messageApi.send(activeUserId.value, inputText.value.trim())
    inputText.value = ''
    await selectConv(activeUserId.value)
  } catch (e: any) {
    ElMessage.error(e?.message || '发送失败')
  } finally {
    sending.value = false
  }
}

const scrollToBottom = () => {
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }
}

// ===== 新消息轮询: 停留在会话时定时静默拉取, 对方新消息自动呈现 =====
const POLL_INTERVAL = 10000
let pollTimer: ReturnType<typeof setInterval> | null = null

const pollLatest = async () => {
  if (!activeUserId.value) return
  try {
    const res: any = await messageApi.messagesWith(activeUserId.value)
    const items = res.data?.items || []
    // 用最后一条消息 id 判断是否有新消息 (比 length 更稳健)
    const lastId = messages.value[messages.value.length - 1]?.id
    const newLastId = items[items.length - 1]?.id
    if (items.length && newLastId !== lastId) {
      messages.value = items
      otherInfo.value = res.data?.other
      await nextTick()
      scrollToBottom()
    }
    // 同步刷新会话列表未读数
    fetchConversations()
  } catch {
    // 轮询失败静默处理, 不打扰用户
  }
}

const startPolling = () => {
  if (pollTimer) return
  pollTimer = setInterval(pollLatest, POLL_INTERVAL)
}
const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

onMounted(async () => {
  await fetchConversations()
  if (route.query.user_id) {
    selectConv(Number(route.query.user_id))
  }
  startPolling()
})
onUnmounted(stopPolling)
</script>

<style scoped>
.message-page {
  display: flex;
  gap: 1px;
  height: calc(100vh - 120px);
  background: #e8e8e8;
  border-radius: 12px;
  overflow: hidden;
}

/* 左侧会话列表 */
.conv-panel {
  width: 280px;
  background: #fff;
  display: flex;
  flex-direction: column;
}
.conv-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
  font-size: 15px;
}
.conv-list { flex: 1; overflow-y: auto; }
.conv-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background 0.2s;
}
.conv-item:hover { background: #f5f5f5; }
.conv-item.active { background: #e6f4ff; }
.conv-avatar { background: #1677ff; color: #fff; flex-shrink: 0; }
.conv-body { flex: 1; min-width: 0; }
.conv-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}
.conv-name { font-weight: 500; font-size: 14px; }
.conv-time { font-size: 11px; color: #999; }
.conv-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.conv-last {
  font-size: 12px;
  color: #999;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 140px;
}

/* 右侧聊天 */
.chat-panel {
  flex: 1;
  background: #fff;
  display: flex;
  flex-direction: column;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
}
.chat-title { font-size: 15px; }
.chat-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: #f5f5f5;
}
.msg-row {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
}
.msg-row.mine { flex-direction: row-reverse; }
.msg-avatar { flex-shrink: 0; background: #52c41a; color: #fff; }
.msg-row.mine .msg-avatar { background: #1677ff; }
.msg-content { max-width: 70%; }
.msg-row.mine .msg-content { text-align: right; }
.msg-bubble {
  display: inline-block;
  padding: 10px 14px;
  background: #fff;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.5;
  text-align: left;
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}
.msg-row.mine .msg-bubble { background: #1677ff; color: #fff; }

/* 时间分隔线 (微信风格居中) */
.time-divider {
  display: flex; align-items: center; justify-content: center;
  margin: 16px 0 12px;
}
.time-divider span {
  font-size: 11px; color: #999; background: rgba(0,0,0,0.06);
  padding: 2px 10px; border-radius: 4px;
}

.chat-input {
  display: flex;
  gap: 8px;
  padding: 12px;
  border-top: 1px solid #f0f0f0;
}
.chat-input .el-button { align-self: flex-end; }
.chat-empty { flex: 1; display: flex; align-items: center; justify-content: center; }
</style>
