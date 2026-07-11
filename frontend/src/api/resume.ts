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
      timeout: 120000,
    })
  },
  /** 我的简历列表 */
  list: () => request.get('/resumes'),
  /** 简历详情 (含工作经历 + 项目经历) */
  detail: (id: number) => request.get(`/resumes/${id}`),
  /** 获取简历原文件 URL */
  getFile: (id: number) => request.get(`/resumes/${id}/file`),
  /** 删除简历 */
  remove: (id: number) => request.delete(`/resumes/${id}`),
}
