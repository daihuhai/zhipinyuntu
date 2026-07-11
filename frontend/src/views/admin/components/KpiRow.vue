<template>
  <div class="kpi-row">
    <div
      v-for="(kpi, i) in cards"
      :key="kpi.label"
      class="kpi-card"
      :style="{ animationDelay: `${i * 0.08}s`, '--accent': kpi.color }"
    >
      <div class="kpi-icon" :style="{ background: kpi.bg, color: kpi.color }">
        <el-icon :size="22"><component :is="kpi.icon" /></el-icon>
      </div>
      <div class="kpi-body">
        <div class="kpi-value">
          <span class="num">{{ displayValues[i] }}</span>
        </div>
        <div class="kpi-label">{{ kpi.label }}</div>
        <div class="kpi-delta" :class="kpi.delta >= 0 ? 'up' : 'down'" v-if="kpi.delta !== undefined">
          <span>{{ kpi.delta >= 0 ? '↑' : '↓' }} {{ Math.abs(kpi.delta) }}</span>
          <span class="delta-pct">{{ Math.abs(kpi.deltaPct).toFixed(1) }}%</span>
        </div>
      </div>
      <div class="kpi-bar"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { User, Document, Briefcase, Tickets, Connection, TrendCharts } from '@element-plus/icons-vue'

interface KpiData {
  users: { total: number; delta: number; delta_pct: number }
  resumes: { total: number; delta: number; delta_pct: number }
  jobs: { total: number; delta: number; delta_pct: number }
  applications: { total: number; delta: number; delta_pct: number }
  matches: { total: number; delta: number; delta_pct: number }
  avg_score: { total: number; delta: number; delta_pct: number }
}

const props = defineProps<{ data: KpiData | null }>()

const cards = ref<any[]>([])
const displayValues = ref<string[]>(['0', '0', '0', '0', '0', '0'])

const buildCards = (d: KpiData) => [
  { label: '用户总数', value: d.users.total, delta: d.users.delta, deltaPct: d.users.delta_pct, icon: User, color: '#1677ff', bg: 'rgba(22,119,255,0.15)' },
  { label: '简历总数', value: d.resumes.total, delta: d.resumes.delta, deltaPct: d.resumes.delta_pct, icon: Document, color: '#52c41a', bg: 'rgba(82,196,26,0.15)' },
  { label: '职位总数', value: d.jobs.total, delta: d.jobs.delta, deltaPct: d.jobs.delta_pct, icon: Briefcase, color: '#faad14', bg: 'rgba(250,173,20,0.15)' },
  { label: '投递总数', value: d.applications.total, delta: d.applications.delta, deltaPct: d.applications.delta_pct, icon: Tickets, color: '#ff6b35', bg: 'rgba(255,107,53,0.15)' },
  { label: '匹配记录', value: d.matches.total, delta: d.matches.delta, deltaPct: d.matches.delta_pct, icon: Connection, color: '#a78bfa', bg: 'rgba(167,139,250,0.15)' },
  { label: '平均匹配分', value: d.avg_score.total, delta: d.avg_score.delta, deltaPct: d.avg_score.delta_pct, icon: TrendCharts, color: '#36cfc9', bg: 'rgba(54,207,201,0.15)' },
]

const animateValue = (index: number, target: number, isFloat = false) => {
  const start = parseFloat(displayValues.value[index]) || 0
  const duration = 800
  const startTime = performance.now()
  const step = (now: number) => {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    const eased = 1 - Math.pow(1 - progress, 3)
    const current = start + (target - start) * eased
    displayValues.value[index] = isFloat ? current.toFixed(1) : Math.round(current).toLocaleString()
    if (progress < 1) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

watch(() => props.data, (d) => {
  if (!d) return
  cards.value = buildCards(d)
  const targets = [d.users.total, d.resumes.total, d.jobs.total, d.applications.total, d.matches.total, d.avg_score.total]
  targets.forEach((t, i) => animateValue(i, t, i === 5))
}, { immediate: true })
</script>

<style scoped>
.kpi-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 12px;
}
.kpi-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: rgba(48, 43, 99, 0.25);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
  overflow: hidden;
  animation: fadeInUp 0.6s ease-out both;
  transition: transform 0.3s, box-shadow 0.3s;
}
.kpi-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(167, 139, 250, 0.2);
}
.kpi-card::before {
  content: '';
  position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px; background: var(--accent);
  box-shadow: 0 0 12px var(--accent);
}
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
.kpi-icon {
  width: 44px; height: 44px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.kpi-body { flex: 1; min-width: 0; }
.kpi-value .num {
  font-size: 24px; font-weight: 700; color: #e0e7ff;
  font-family: 'DIN Alternate', 'Helvetica Neue', monospace;
  line-height: 1.2;
}
.kpi-label { font-size: 12px; color: #c4b5fd; margin-top: 2px; }
.kpi-delta {
  font-size: 11px; margin-top: 4px; display: flex; gap: 4px; align-items: center;
}
.kpi-delta.up { color: #52c41a; }
.kpi-delta.down { color: #ff4d4f; }
.delta-pct { opacity: 0.7; }
.kpi-bar {
  position: absolute; right: 0; bottom: 0; left: 0;
  height: 2px; background: var(--accent); opacity: 0.4;
}
</style>
