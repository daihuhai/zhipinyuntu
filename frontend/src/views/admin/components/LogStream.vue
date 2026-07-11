<template>
  <div class="dc-panel">
    <div class="log-header">
      <div class="dc-panel-title">实时操作日志</div>
      <div class="live-tag">
        <span class="live-dot"></span>
        <span>实时</span>
      </div>
    </div>
    <div class="log-list">
      <transition-group name="log-slide" tag="div">
        <div v-for="item in displayItems" :key="item.id" class="log-row">
          <span class="log-time">{{ formatTime(item.created_at) }}</span>
          <span
            class="log-action"
            :style="{ color: actionColor(item.action), borderColor: actionColor(item.action) }"
          >{{ item.action }}</span>
          <span class="log-detail" :title="item.detail">{{ item.detail }}</span>
          <span class="log-ip">{{ item.ip }}</span>
        </div>
      </transition-group>
      <div v-if="!displayItems.length" class="log-empty">暂无操作日志</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface LogItem {
  id: number | string
  admin_id: number | string
  action: string
  target_type: string
  target_id: number | string
  detail: string
  ip: string
  created_at: string
}

const props = defineProps<{ items: LogItem[] }>()

const displayItems = computed(() => (props.items || []).slice(0, 8))

const actionColor = (action: string) => {
  if (!action) return '#8c8c8c'
  if (action.startsWith('DELETE_')) return '#ff4d4f'
  if (action.startsWith('UPDATE_')) return '#3b82f6'
  if (action.startsWith('BATCH_')) return '#a78bfa'
  if (action.startsWith('CREATE_')) return '#52c41a'
  return '#8c8c8c'
}

const formatTime = (iso?: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  if (isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}
</script>

<style scoped>
.dc-panel {
  background: rgba(48, 43, 99, 0.25);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
  padding: 16px;
}
.dc-panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #a78bfa;
  margin-bottom: 12px;
  letter-spacing: 1px;
}
.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.live-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #52c41a;
  margin-bottom: 12px;
}
.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #52c41a;
  box-shadow: 0 0 6px #52c41a;
  animation: live-pulse 1.4s infinite;
}
@keyframes live-pulse {
  0% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.5); opacity: 0.4; }
  100% { transform: scale(1); opacity: 1; }
}
.log-list {
  height: 360px;
  overflow: hidden;
}
.log-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 4px;
  border-bottom: 1px solid rgba(167, 139, 250, 0.08);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
}
.log-time {
  color: #6b7280;
  font-size: 11px;
  flex-shrink: 0;
  width: 56px;
}
.log-action {
  padding: 1px 8px;
  border: 1px solid;
  border-radius: 4px;
  font-size: 11px;
  flex-shrink: 0;
  background: rgba(255, 255, 255, 0.03);
}
.log-detail {
  color: #e0e7ff;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}
.log-ip {
  color: #6b7280;
  font-size: 11px;
  flex-shrink: 0;
}
.log-empty {
  color: #6b7280;
  font-size: 13px;
  text-align: center;
  padding: 40px 0;
}
.log-slide-enter-active,
.log-slide-leave-active {
  transition: all 0.5s ease;
}
.log-slide-enter-from {
  opacity: 0;
  transform: translateY(-20px);
}
.log-slide-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
.log-slide-move {
  transition: transform 0.5s ease;
}
</style>
