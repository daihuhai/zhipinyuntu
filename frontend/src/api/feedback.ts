import request from './request'

export const feedbackApi = {
  /** 提交反馈 */
  create: (data: { type: string; title: string; content: string }) =>
    request.post('/api/v1/feedback', data),

  /** 我的反馈列表 */
  my: (params: { page: number; size: number }) =>
    request.get('/api/v1/feedback/my', { params }),

  /** 管理员-所有反馈列表 */
  adminList: (params: { page: number; size: number; status?: string }) =>
    request.get('/api/v1/admin/feedbacks', { params }),

  /** 管理员-回复反馈 */
  adminReply: (id: number, data: { status: string; reply?: string }) =>
    request.put(`/api/v1/admin/feedbacks/${id}`, data),
}