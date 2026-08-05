/**
 * 简历相关 API
 */
import request from './request'

export const resumeApi = {
  /** 上传简历 (multipart) */
  upload: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post('/resumes/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 600000,
    })
  },
  /** 我的简历列表 */
  list: () => request.get('/resumes'),
  /** 简历详情 (含工作经历 + 项目经历) */
  detail: (id: number) => request.get(`/resumes/${id}`),
  /** 在线编辑简历 */
  update: (id: number, data: Record<string, any>) => request.put(`/resumes/${id}`, data),
  /** 获取简历原文件 URL */
  getFile: (id: number) => request.get(`/resumes/${id}/file`),
  /** 删除简历 */
  remove: (id: number) => request.delete(`/resumes/${id}`),
  /** 灵犀分析简历缺失项 */
  gapAnalysis: (id: number) => request.post(`/resumes/${id}/gap-analysis`, {}, { timeout: 600000 }),
  /** 灵犀分析编辑中的简历(实时, 传当前表单数据) */
  analyzeForm: (id: number, formData: any) =>
    request.post(`/resumes/${id}/analyze-form`, { form_data: formData }, { timeout: 600000 }),
  /** 灵犀AI简历优化建议 */
  optimize: (id: number) => request.post(`/resumes/${id}/optimize`, {}, { timeout: 600000 }),
  /** 求职者竞争力分析 */
  competitiveness: (id: number) => request.get(`/resumes/${id}/competitiveness`),
}
