<template>
  <div class="dc-panel">
    <div class="dc-panel-title">院校 TOP10</div>
    <div class="rank-list">
      <div
        v-for="(school, i) in top10"
        :key="i"
        class="rank-row"
      >
        <span class="rank-badge" :style="badgeStyle(i + 1)">{{ i + 1 }}</span>
        <span class="rank-name" :title="school.name">{{ school.name }}</span>
        <div class="rank-bar-wrap">
          <div class="rank-bar" :style="{ width: barWidth(school.count) }"></div>
        </div>
        <span class="rank-count">{{ school.count }}</span>
      </div>
      <div v-if="!top10.length" class="rank-empty">暂无数据</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface School {
  name: string
  count: number
}

const props = defineProps<{ schools: School[] }>()

const top10 = computed(() => (props.schools || []).slice(0, 10))
const maxCount = computed(() => Math.max(...top10.value.map((s) => Number(s.count) || 0), 1))

const badgeStyle = (rank: number) => {
  let bg = '#a78bfa'
  if (rank === 1) bg = '#ffd700'
  else if (rank === 2) bg = '#c0c0c0'
  else if (rank === 3) bg = '#cd7f32'
  return { background: bg }
}

const barWidth = (count: number) => {
  const c = Number(count) || 0
  return ((c / maxCount.value) * 100).toFixed(1) + '%'
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
.rank-list {
  height: 300px;
  overflow-y: auto;
}
.rank-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 4px;
  height: 30px;
  box-sizing: border-box;
}
.rank-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
  color: #0f0c29;
  flex-shrink: 0;
}
.rank-name {
  color: #e0e7ff;
  font-size: 13px;
  width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}
.rank-bar-wrap {
  flex: 1;
  height: 6px;
  background: rgba(167, 139, 250, 0.12);
  border-radius: 3px;
  overflow: hidden;
}
.rank-bar {
  height: 100%;
  background: linear-gradient(90deg, #a78bfa, #60a5fa);
  border-radius: 3px;
  transition: width 0.5s ease;
}
.rank-count {
  color: #c4b5fd;
  font-size: 13px;
  font-weight: 600;
  width: 48px;
  text-align: right;
  flex-shrink: 0;
}
.rank-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #6b7280;
  font-size: 13px;
}
</style>
