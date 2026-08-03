import request from './request'

export const feedbackApi = {
  /** 提交反馈 */
  create: (data: { type: string; title: string; content: string }) =>
    request.post('/feedback', data),

  /** 我的反馈列表 */
  my: (params: { page: number; size: number }) =>
    request.get('/feedback/my', { params }),

  /** 我的反馈统计 */
  myStats: () =>
    request.get('/feedback/my-stats'),

  /** 管理员-所有反馈列表 */
  adminList: (params: { page: number; size: number; status?: string; type?: string; keyword?: string }) =>
    request.get('/admin/feedbacks', { params }),

  /** 管理员-反馈统计 */
  adminStats: () =>
    request.get('/admin/feedbacks/stats'),

  /** 管理员-回复反馈 */
  adminReply: (id: number, data: { status: string; reply?: string; notify?: boolean }) =>
    request.put(`/admin/feedbacks/${id}`, data),
}
