<!--
  技能词云组件 (纯 Canvas 实现, 无第三方依赖)
  用法: <SkillWordCloud :skills="skills" />
  skills: [{ skill_name, skill_level }]
-->
<template>
  <div class="wordcloud-wrap">
    <canvas ref="canvasRef" class="wordcloud-canvas"></canvas>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, nextTick } from 'vue'

const props = defineProps<{ skills: any[] }>()

const canvasRef = ref<HTMLCanvasElement | null>(null)

// 技能等级 -> 权重
const LEVEL_WEIGHT: Record<string, number> = {
  '精通': 5, '熟练': 4, '掌握': 3, '熟悉': 2, '了解': 1,
}

// 主题配色
const COLORS = ['#1677ff', '#40a9ff', '#52c41a', '#faad14', '#f56c6c', '#722ed1', '#13c2c2', '#eb2f96']

interface Rect { x: number; y: number; w: number; h: number }

const overlap = (a: Rect, b: Rect) =>
  a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y

const draw = () => {
  const canvas = canvasRef.value
  if (!canvas || !props.skills?.length) return
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  // 画布尺寸跟随容器
  const rect = canvas.parentElement!.getBoundingClientRect()
  const W = Math.max(rect.width, 300)
  const H = 260
  const dpr = window.devicePixelRatio || 1
  canvas.width = W * dpr
  canvas.height = H * dpr
  canvas.style.width = W + 'px'
  canvas.style.height = H + 'px'
  ctx.scale(dpr, dpr)
  ctx.clearRect(0, 0, W, H)

  // 按权重降序
  const words = props.skills
    .map((s: any) => ({
      name: s.skill_name || s.name || '',
      weight: LEVEL_WEIGHT[s.skill_level] || 3,
    }))
    .filter((w: any) => w.name)
    .sort((a: any, b: any) => b.weight - a.weight)

  const placed: Rect[] = []

  words.forEach((word: any, idx: number) => {
    // 字号: 权重越大字越大 (14 ~ 34)
    const fontSize = 12 + word.weight * 4 + (idx < 3 ? 4 : 0)
    ctx.font = `bold ${fontSize}px "PingFang SC", "Microsoft YaHei", sans-serif`
    const tw = ctx.measureText(word.name).width
    const th = fontSize + 4
    const box: Rect = { x: 0, y: 0, w: tw, h: th }

    // 螺旋搜索空位
    let angle = Math.random() * Math.PI * 2
    let radius = 0
    let ok = false
    for (let i = 0; i < 800; i++) {
      const x = W / 2 + radius * Math.cos(angle) - tw / 2
      const y = H / 2 + radius * Math.sin(angle) * 0.75 - th / 2
      box.x = x; box.y = y
      if (x >= 2 && y >= 2 && x + tw <= W - 2 && y + th <= H - 2 &&
          !placed.some(r => overlap(r, box))) {
        ok = true
        break
      }
      angle += 0.4
      radius += 0.8
    }
    if (!ok) return // 放不下则跳过

    placed.push({ ...box })
    ctx.fillStyle = COLORS[idx % COLORS.length]
    ctx.textBaseline = 'top'
    ctx.fillText(word.name, box.x, box.y + 2)
  })
}

onMounted(() => nextTick(draw))
watch(() => props.skills, () => nextTick(draw), { deep: true })
</script>

<style scoped>
.wordcloud-wrap {
  width: 100%;
  background: linear-gradient(135deg, #f0f7ff 0%, #f8fbff 100%);
  border: 1px solid #e6f0fa;
  border-radius: 10px;
  padding: 8px;
  margin-top: 10px;
}
.wordcloud-canvas { display: block; width: 100%; }
</style>
