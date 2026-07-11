<template>
  <div class="dc-header">
    <div class="header-left">
      <img src="@/assets/logo.png" class="header-logo" alt="智聘云图" />
      <h1 class="header-title">智聘云图 · 数据指挥中心</h1>
    </div>
    <div class="header-center">
      <span class="clock">{{ clock }}</span>
    </div>
    <div class="header-right">
      <el-select v-model="range" size="small" class="range-select" @change="onRangeChange">
        <el-option label="今日" value="today" />
        <el-option label="近 7 日" value="7d" />
        <el-option label="近 30 日" value="30d" />
        <el-option label="全部" value="all" />
      </el-select>
      <el-button :icon="Refresh" circle size="small" @click="onRefresh" />
      <el-button :icon="FullScreen" circle size="small" @click="toggleFullscreen" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { Refresh, Expand, FullScreen } from '@element-plus/icons-vue'

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'range-change', v: string): void
}>()

const clock = ref('')
const range = ref('7d')
let timer: ReturnType<typeof setInterval> | null = null

const updateClock = () => {
  const d = new Date()
  const pad = (n: number) => String(n).padStart(2, '0')
  clock.value = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

const onRefresh = () => emit('refresh')
const onRangeChange = (v: string) => emit('range-change', v)

const toggleFullscreen = () => {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.()
  } else {
    document.exitFullscreen?.()
  }
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
})
onBeforeUnmount(() => { if (timer) clearInterval(timer) })
</script>

<style scoped>
.dc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
  padding: 0 24px;
  background: rgba(15, 12, 41, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.header-logo { width: 36px; height: 36px; border-radius: 8px; }
.header-title {
  font-size: 22px; font-weight: 700; letter-spacing: 2px;
  background: linear-gradient(90deg, #a78bfa, #60a5fa, #52c41a);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent;
}
.header-center { flex: 1; text-align: center; }
.clock {
  font-size: 18px; font-weight: 500; color: #e0e7ff;
  font-family: 'DIN Alternate', 'Helvetica Neue', monospace; letter-spacing: 2px;
}
.header-right { display: flex; align-items: center; gap: 10px; }
.range-select { width: 110px; }
:deep(.range-select .el-input__wrapper) {
  background: rgba(255,255,255,0.06);
  box-shadow: 0 0 0 1px rgba(167,139,250,0.3) inset;
}
:deep(.range-select .el-input__inner) { color: #c4b5fd; }
</style>
