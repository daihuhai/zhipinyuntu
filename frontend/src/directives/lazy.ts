/**
 * 图片懒加载自定义指令 v-lazy
 * 基于 Intersection Observer, 图片进入视口时才加载
 * 加载前显示灰色骨架占位, 加载完成后淡入显示
 *
 * 用法: <img v-lazy="imageUrl" />
 * 或:    <img v-lazy="imageUrl" :data-placeholder="'custom-placeholder-url'" />
 */
import type { Directive, DirectiveBinding } from 'vue'

// 占位灰色 1x1 SVG
const PLACEHOLDER =
  'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="1" height="1"%3E%3Crect width="1" height="1" fill="%23f0f0f0"/%3E%3C/svg%3E'

// 全局 IntersectionObserver 实例 (复用)
let observer: IntersectionObserver | null = null

// 待加载的元素队列
const pending = new Map<HTMLElement, () => void>()

function ensureObserver(): IntersectionObserver {
  if (observer) return observer
  observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          const el = entry.target as HTMLElement
          const callback = pending.get(el)
          if (callback) {
            callback()
            pending.delete(el)
          }
          observer!.unobserve(el)
        }
      }
    },
    { rootMargin: '50px', threshold: 0.01 },
  )
  return observer
}

const lazy: Directive = {
  mounted(el: HTMLElement, binding: DirectiveBinding) {
    const img = el as HTMLImageElement
    const src = binding.value as string

    if (!src) return

    // 设置占位图
    img.src = PLACEHOLDER
    img.style.opacity = '0'
    img.style.transition = 'opacity 0.3s ease-in-out'

    const obs = ensureObserver()
    pending.set(el, () => {
      // 加载真实图片
      const tempImg = new Image()
      tempImg.onload = () => {
        img.src = src
        img.style.opacity = '1'
      }
      tempImg.onerror = () => {
        // 加载失败也显示占位图, 但不淡入
        img.style.opacity = '1'
      }
      tempImg.src = src
    })
    obs.observe(el)
  },

  updated(el: HTMLElement, binding: DirectiveBinding) {
    // src 变化时重新加载
    if (binding.value !== binding.oldValue) {
      const img = el as HTMLImageElement
      const src = binding.value as string
      if (!src) return

      const tempImg = new Image()
      tempImg.onload = () => {
        img.src = src
        img.style.opacity = '1'
      }
      tempImg.src = src
    }
  },

  unmounted(el: HTMLElement) {
    pending.delete(el)
    if (observer) observer.unobserve(el)
  },
}

export default lazy
