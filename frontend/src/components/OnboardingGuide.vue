<!--
  新用户引导 (高亮定位式)
  - 首次登录按角色分步引导, 每步定位到具体界面元素并高亮
  - 步骤间自动跳转到对应页面
  - 记录 localStorage 避免重复弹出
-->
<template>
  <transition name="el-fade-in">
    <div v-if="visible" class="guide-root">
      <div class="guide-mask" @click.self="skip" />
      <div
        v-if="spotlight"
        class="spotlight"
        :style="spotlightStyle"
        @click.self="next"
      />
      <div
        v-if="spotlight"
        class="guide-tooltip"
        :style="tooltipStyle"
      >
        <div class="tooltip-head">
          <span class="tooltip-step">{{ step + 1 }} / {{ steps.length }}</span>
          <span class="tooltip-title">{{ current.title }}</span>
        </div>
        <div class="tooltip-desc">{{ current.desc }}</div>
        <div class="tooltip-footer">
          <el-button text size="small" @click="skip">跳过</el-button>
          <el-button v-if="step < steps.length - 1" type="primary" size="small" @click="next">
            下一步
          </el-button>
          <el-button v-else type="primary" size="small" @click="finish">开始使用</el-button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps<{ role: string }>()
const emit = defineEmits<{ skip: [] }>()

interface GuideStep {
  to: string
  selector: string
  title: string
  desc: string
}

const STEP_MAP: Record<string, GuideStep[]> = {
  ROLE_SEEKER: [
    { to: '/seeker/jobs', selector: '[data-guide="职位广场"]', title: '职位广场', desc: '浏览海量职位，支持城市、薪资、经验多维筛选与智能搜索' },
    { to: '/seeker/resume/list', selector: '[data-guide="我的简历"]', title: '我的简历', desc: '管理你的简历，上传后 AI 自动解析，并生成竞争力分析' },
    { to: '/seeker/applications', selector: '[data-guide="投递记录"]', title: '投递记录', desc: '追踪投递进度与面试状态，面试结束后还可评价企业' },
    { to: '/seeker/messages', selector: '[data-guide="消息"]', title: '消息中心', desc: '实时接收站内消息与投递通知，快速掌握最新进展' },
  ],
  ROLE_EMPLOYER: [
    { to: '/employer/job/create', selector: '[data-guide="发布职位"]', title: '发布职位', desc: '发布职位，支持 JD 解析或灵犀 AI 生成职位描述' },
    { to: '/employer/candidates', selector: '[data-guide="候选人推荐"]', title: '候选人推荐', desc: 'AI 匹配引擎根据简历与职位要求智能推荐候选人' },
    { to: '/employer/applications', selector: '[data-guide="投递管理"]', title: '投递管理', desc: '管理投递与面试流程，查看简历与匹配分析' },
    { to: '/employer/messages', selector: '[data-guide="消息"]', title: '消息中心', desc: '实时接收候选人消息与投递推送通知' },
  ],
}

const steps: GuideStep[] = STEP_MAP[props.role] || []

const router = useRouter()
const visible = ref(true)
const step = ref(0)
const spotlight = ref<{ top: number; left: number; width: number; height: number } | null>(null)
const tooltipPlacement = ref<'right' | 'left' | 'bottom'>('right')

const current = computed(() => steps[step.value] || steps[0])

/** 等待元素出现 (路由切换 + DOM 渲染) */
function waitForElement(selector: string, timeout = 4000): Promise<Element | null> {
  return new Promise((resolve) => {
    const start = Date.now()
    const poll = () => {
      const el = document.querySelector(selector)
      if (el) return resolve(el)
      if (Date.now() - start > timeout) return resolve(null)
      setTimeout(poll, 80)
    }
    poll()
  })
}

/** 计算目标元素位置并高亮 */
async function locate() {
  const c = current.value
  if (!c) return
  // 若不在目标路由, 先跳转
  if (router.currentRoute.value.path !== c.to) {
    await router.push(c.to)
    await nextTick()
  }
  const el = await waitForElement(c.selector)
  if (!el) return
  const rect = el.getBoundingClientRect()
  spotlight.value = {
    top: rect.top - 6,
    left: rect.left - 6,
    width: rect.width + 12,
    height: rect.height + 12,
  }
  // 菜单在左侧, 提示放右边; 若靠右侧则放左边
  tooltipPlacement.value = rect.left < window.innerWidth / 2 ? 'right' : 'left'
}

const spotlightStyle = computed(() => {
  if (!spotlight.value) return {}
  return {
    top: `${spotlight.value.top}px`,
    left: `${spotlight.value.left}px`,
    width: `${spotlight.value.width}px`,
    height: `${spotlight.value.height}px`,
  }
})

const tooltipStyle = computed(() => {
  if (!spotlight.value) return {}
  const s = spotlight.value
  if (tooltipPlacement.value === 'right') {
    return { top: `${s.top}px`, left: `${s.left + s.width + 16}px` }
  }
  return { top: `${s.top}px`, right: `${window.innerWidth - s.left + 16}px` }
})

function handleReposition() {
  if (visible.value) locate()
}

async function next() {
  if (step.value < steps.length - 1) {
    step.value += 1
    spotlight.value = null
    await nextTick()
    await locate()
  } else {
    finish()
  }
}

function skip() {
  visible.value = false
  // 后端持久化由 App.vue handleGuideSkip 统一处理, 此处仅通知
  emit('skip')
}

function finish() { skip() }

watch(() => props.role, () => { step.value = 0; nextTick(() => locate()) })

onMounted(() => {
  // 首次定位 (localStorage 已由 App.vue watch 提前写入, 此处无需重复)
  nextTick(() => locate())
  window.addEventListener('scroll', handleReposition, true)
  window.addEventListener('resize', handleReposition)
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', handleReposition, true)
  window.removeEventListener('resize', handleReposition)
})
</script>

<style scoped>
.guide-root { position: fixed; inset: 0; z-index: 4000; }
.guide-mask {
  position: fixed; inset: 0; z-index: 4000;
  background: rgba(0, 21, 41, 0.55);
}
.spotlight {
  position: fixed; z-index: 4001;
  border-radius: 10px;
  box-shadow: 0 0 0 9999px rgba(0, 21, 41, 0.55);
  border: 2px solid #1677ff;
  pointer-events: none;
  transition: all 0.25s ease;
}
.guide-tooltip {
  position: fixed; z-index: 4002;
  width: 280px; background: #fff; border-radius: 12px;
  padding: 16px 18px;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.28);
  animation: fadeIn 0.25s ease;
}
.tooltip-head { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.tooltip-step { font-size: 12px; color: #1677ff; font-weight: 600; }
.tooltip-title { font-size: 16px; font-weight: 700; color: #001529; }
.tooltip-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 12px; }
.tooltip-footer { display: flex; justify-content: space-between; align-items: center; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }
</style>