/**
 * useDraft - 表单草稿自动保存
 * - 输入变化时自动保存草稿到 localStorage (防抖 500ms)
 * - 页面重新进入时提示恢复未提交内容
 * - 提交成功后清除草稿
 */
import { onBeforeUnmount, ref, watch } from 'vue'

export function useDraft(key: string, formData: () => Record<string, any>, options?: { saveOnUnmount?: boolean; shouldSave?: () => boolean }) {
  const { saveOnUnmount = true, shouldSave } = options || {}
  const checked = ref(false)
  const draftKey = `draft:${key}`
  let timer: ReturnType<typeof setTimeout> | null = null

  /** 读取草稿 (若存在则返回, 供页面提示恢复) */
  function loadDraft(): Record<string, any> | null {
    try {
      const raw = localStorage.getItem(draftKey)
      if (!raw) return null
      const parsed = JSON.parse(raw)
      checked.value = true
      return parsed
    } catch {
      return null
    }
  }

  /** 开始自动保存 (监听表单变化, 防抖写入) */
  function startAutoSave() {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      try {
        if (shouldSave && !shouldSave()) return
        localStorage.setItem(draftKey, JSON.stringify(formData()))
      } catch { /* 存储满或禁用时静默忽略 */ }
    }, 500)
  }

  /** 清除草稿 (提交成功后调用) */
  function clearDraft() {
    if (timer) { clearTimeout(timer); timer = null }
    try { localStorage.removeItem(draftKey) } catch { /* noop */ }
  }

  onBeforeUnmount(() => {
    // 离开页面时立即保存一次最终状态 (是否保存由 shouldSave 决定)
    if (saveOnUnmount) {
      try {
        if (shouldSave && !shouldSave()) return
        localStorage.setItem(draftKey, JSON.stringify(formData()))
      } catch { /* noop */ }
    }
    if (timer) { clearTimeout(timer); timer = null }
  })

  return { draftKey, checked, loadDraft, startAutoSave, clearDraft }
}