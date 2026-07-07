/**
 * 格式化工具函数
 */

/**
 * 格式化薪资显示 (后端存储单位: K)
 * @param min 薪资下限 (K)
 * @param max 薪资上限 (K)
 * @returns "3K-5K" | "3K起" | "10K以下" | "面议"
 */
export function formatSalary(min?: number | null, max?: number | null): string {
  if (min == null && max == null) return '面议'
  if (min != null && max != null) return `${min}K-${max}K`
  if (min != null) return `${min}K起`
  return `${max}K以下`
}
