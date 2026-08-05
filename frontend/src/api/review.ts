/**
 * 企业评价 API
 */
import request from './request'

export const reviewApi = {
  /** 提交企业评价 (面试结束后) */
  create: (data: {
    company_id: number
    application_id: number
    interview_score: number
    hr_score: number
    accuracy_score: number
    comment?: string
  }) => request.post('/reviews', data),

  /** 企业评价列表 + 综合评分 (公开) */
  companyList: (companyId: number, params: { page?: number; size?: number } = {}) =>
    request.get(`/reviews/company/${companyId}`, { params }),

  /** 我的评价状态 (是否已评价某职位) */
  my: (jobId: number) =>
    request.get('/reviews/my', { params: { job_id: jobId } }),
}