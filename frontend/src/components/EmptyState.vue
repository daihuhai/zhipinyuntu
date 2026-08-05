<!--
  EmptyState - 统一空状态组件
  提供插画 + 标题 + 描述 + 引导 CTA 按钮, 替代简单的 el-empty
-->
<template>
  <div class="empty-state">
    <div class="empty-icon" :style="{ background: iconBg }">
      <el-icon :size="42"><component :is="icon" /></el-icon>
    </div>
    <div class="empty-title">{{ title }}</div>
    <div v-if="description" class="empty-desc">{{ description }}</div>
    <div v-if="actionText" class="empty-action">
      <el-button type="primary" :icon="actionIcon" @click="$emit('action')">
        {{ actionText }}
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Box, Briefcase, Upload, Tickets, ChatDotRound, Star, Document } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  title?: string
  description?: string
  actionText?: string
  actionIcon?: any
  icon?: string
}>(), {
  title: '暂无数据',
  description: '',
  actionText: '',
  actionIcon: undefined,
  icon: 'box',
})

defineEmits<{ (e: 'action'): void }>()

const iconMap: Record<string, any> = {
  box: Box,
  briefcase: Briefcase,
  upload: Upload,
  tickets: Tickets,
  chat: ChatDotRound,
  star: Star,
  document: Document,
}
const icon = computed(() => iconMap[props.icon] || Box)
const iconBg = computed(() => {
  const map: Record<string, string> = {
    box: 'linear-gradient(135deg,#e6f4ff,#1677ff)',
    briefcase: 'linear-gradient(135deg,#fff7e6,#faad14)',
    upload: 'linear-gradient(135deg,#f6ffed,#52c41a)',
    tickets: 'linear-gradient(135deg,#f9f0ff,#722ed1)',
    chat: 'linear-gradient(135deg,#e6fffb,#13c2c2)',
    star: 'linear-gradient(135deg,#fffbe6,#fadb14)',
    document: 'linear-gradient(135deg,#e6f4ff,#1677ff)',
  }
  return map[props.icon] || map.box
})
</script>

<style scoped>
.empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 48px 20px; text-align: center;
  grid-column: 1 / -1;
}
.empty-icon {
  width: 88px; height: 88px; border-radius: 24px;
  display: flex; align-items: center; justify-content: center;
  color: #fff; margin-bottom: 18px;
  box-shadow: 0 8px 20px rgba(22, 119, 255, 0.15);
}
.empty-title { font-size: 16px; font-weight: 600; color: var(--text-primary); margin-bottom: 8px; }
.empty-desc { font-size: 13px; color: var(--text-secondary); max-width: 360px; line-height: 1.6; margin-bottom: 18px; }
.empty-action { margin-top: 4px; }
</style>