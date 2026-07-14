/**
 * 职位相关 API
 */
import request from './request'

export interface JobCreateParams {
  title: string
  company?: string
  department?: string
  job_type?: string
  salary_min?: number
  salary_max?: number
  work_city?: string
  experience_required?: string
  education_required?: string
  headcount?: number
  description?: string
  parse_text?: string
}

export interface JobListParams {
  page?: number
  size?: number
  keyword?: string
  city?: string
  job_type?: string
  experience?: string
  education?: string
  salary_min?: number
  salary_max?: number
}

export const jobApi = {
  /** 上传 JD 文件 (PDF/DOC/DOCX) 并灵犀解析, 返回结构化字段供预填表单
   *  注意: doubao-seed 推理模型单次调用约 60-200s (视文本长度), 超时设为 300s 确保覆盖 */
  uploadJD: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post('/jobs/upload-jd', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 300000,
    })
  },
  /** 创建职位 (可带 parse_text 触发灵犀解析, 灵犀推理模型耗时较长单独设置 300s 超时) */
  create: (data: JobCreateParams) =>
    request.post('/jobs', data, { timeout: 300000 }),
  /** 解析 JD 纯文本, 返回结构化字段供预填表单 (doubao-seed 推理模型, 单独设置 300s 超时) */
  parseJDText: (text: string) =>
    request.post('/jobs/parse-jd-text', { text }, { timeout: 300000 }),
  /** 企业职位列表 (我的职位, 支持搜索) */
  myList: (keyword?: string) => request.get('/jobs', { params: keyword ? { keyword } : {} }),
  /** 职位广场 (公开, 分页, 多条件筛选) */
  list: (params: JobListParams) => request.get('/jobs/plaza', { params }),
  /** 职位详情 */
  detail: (id: number) => request.get(`/jobs/${id}`),
  /** 删除职位 */
  remove: (id: number) => request.delete(`/jobs/${id}`),
  /** 更新职位状态 (后端为 PATCH /jobs/{id}/status?status=N) */
  updateStatus: (id: number, status: number) =>
    request.patch(`/jobs/${id}/status`, null, { params: { status } }),
  /** 收藏职位 */
  addFavorite: (jobId: number) => request.post(`/jobs/${jobId}/favorite`),
  /** 取消收藏职位 */
  removeFavorite: (jobId: number) => request.delete(`/jobs/${jobId}/favorite`),
  /** 我的收藏列表 */
  listFavorites: () => request.get('/jobs/favorites'),
}
