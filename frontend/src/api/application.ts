/**
 * 投递记录 API
 */
import request from './request'

export const applicationApi = {
  /** 投递简历 */
  apply: (data: { resume_id: number; job_id: number; cover_letter?: string }) =>
    request.post('/applications', data),
  /** 我的投递记录 (求职者) */
  myList: (params: { page?: number; size?: number }) =>
    request.get('/applications', { params }),
  /** 求职者投递趋势 (近14天每日投递量 + 状态分布) */
  myTrend: () =>
    request.get('/applications/my/trend'),
  /** 某职位的投递记录 (企业) */
  jobList: (jobId: number) =>
    request.get(`/applications/job/${jobId}`),
  /** 企业全部投递记录 (可选按 job_id 筛选) */
  employerList: (jobId?: number) =>
    request.get('/applications/employer', { params: jobId ? { job_id: jobId } : {} }),
  /** 更新投递状态 (企业) */
  updateStatus: (id: number, status: number) =>
    request.post(`/applications/${id}/status`, { status }),
  /** 批量更新投递状态 (企业) */
  batchStatus: (ids: number[], status: number) =>
    request.post('/applications/batch/status', { ids, status }),
  /** 企业投递统计 (在招职位/收到简历/状态分布) */
  employerSummary: () =>
    request.get('/applications/employer/summary'),
  /** 企业投递趋势 (近14天每日投递量 + 职位分布 Top10) */
  employerTrend: () =>
    request.get('/applications/employer/trend'),
}
